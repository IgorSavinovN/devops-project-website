from kafka import KafkaProducer
import json
import logging
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
from models import db, Project, Visit, Setting, KafkaTopicStat
from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Единый адрес Kafka (localhost внутри сервера)
KAFKA_BROKER = '127.0.0.1:9092'

# Глобальный продюсер
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    logger.info("✅ Kafka producer connected")
except Exception as e:
    logger.error(f"❌ Kafka producer failed: {e}")
    producer = None


def init_routes(app, db, Project, Visit, Setting):

    @app.route('/')
    def home():
        visit = Visit(
            ip=request.remote_addr,
            page=request.path,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(visit)
        db.session.commit()

        projects = Project.query.order_by(Project.created_at.desc()).all()
        total_projects = Project.query.count()
        done_projects = Project.query.filter_by(status='done').count()
        pending_projects = Project.query.filter_by(status='pending').count()
        in_progress_projects = Project.query.filter_by(status='in_progress').count()

        high_priority = Project.query.filter_by(priority='high').count()
        medium_priority = Project.query.filter_by(priority='medium').count()
        low_priority = Project.query.filter_by(priority='low').count()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_visits = Visit.query.filter(Visit.timestamp >= today).count()
        week_visits = Visit.query.filter(Visit.timestamp >= today - timedelta(days=7)).count()
        total_visits = Visit.query.count()
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        active_visitors = Visit.query.filter(Visit.timestamp >= five_min_ago).count()
        new_projects = Project.query.filter(Project.created_at >= today - timedelta(days=7)).count()

        return render_template('index.html')

    @app.route('/projects')
    def projects():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/stats')
    def stats():
        total_projects = Project.query.count()
        done_projects = Project.query.filter_by(status='done').count()
        pending = Project.query.filter_by(status='pending').count()
        in_progress = Project.query.filter_by(status='in_progress').count()
        today = datetime.utcnow().replace(hour=0, minute=0, second=0)
        today_visits = Visit.query.filter(Visit.timestamp >= today).count()
        return render_template('stats.html',
                               total=total_projects,
                               done=done_projects,
                               pending=pending,
                               in_progress=in_progress,
                               today_visits=today_visits)

    @app.route('/status')
    def status():
        # Проверка PostgreSQL
        try:
            db.session.execute('SELECT 1')
            pg_status = True
        except:
            pg_status = False

        # Проверка Kafka
        try:
            test_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
            test_producer.close()
            kafka_status = True
        except:
            kafka_status = False

        # Статистика Kafka из БД
        kafka_stat = KafkaTopicStat.query.first()

        return render_template('status.html',
                               pg_status=pg_status,
                               kafka_status=kafka_status,
                               kafka_stat=kafka_stat)

    @app.route('/add', methods=['POST'])
    def add_project():
        project = Project(
            title=request.form['title'],
            description=request.form.get('description', ''),
            priority=request.form.get('priority', 'medium'),
            status=request.form.get('status', 'pending')
        )
        db.session.add(project)
        db.session.commit()
        flash('Проект добавлен', 'success')
        return redirect(url_for('projects'))

    @app.route('/delete/<int:id>')
    def delete_project(id):
        project = Project.query.get_or_404(id)
        db.session.delete(project)
        db.session.commit()
        flash('Проект удалён', 'success')
        return redirect(url_for('projects'))

    @app.route('/send-event')
    def send_event():
        global producer
        if not producer:
            return "Kafka producer not available", 500

        event = {
            'event_type': 'page_view',
            'page': request.referrer or 'direct',
            'user_ip': request.remote_addr,
            'timestamp': str(datetime.utcnow())
        }

        try:
            future = producer.send('devops-events', value=event)
            result = future.get(timeout=10)
            logger.info(f"✅ Event sent: {event}")
            return f"Event sent: {event}"
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            return f"Error: {e}", 500

    @app.route('/kafka')
    def kafka_dashboard():
        """Главная страница управления Kafka"""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BROKER,
                client_id='devops-admin'
            )
            topics = admin_client.list_topics()
            admin_client.close()

            # Получаем статистику из БД
            topic_stats = {stat.topic_name: stat for stat in KafkaTopicStat.query.all()}

            # Получаем детальную информацию о каждом топике
            topics_detail = []
            from kafka import KafkaConsumer
            for topic in sorted(topics):
                if topic.startswith('_'):  # пропускаем внутренние топики
                    continue
                try:
                    consumer = KafkaConsumer(
                        topic,
                        bootstrap_servers=KAFKA_BROKER,
                        consumer_timeout_ms=1000
                    )
                    partitions = consumer.partitions_for_topic(topic)
                    # Получаем последние сообщения
                    consumer.seek_to_end()
                    end_offsets = consumer.end_offsets(partitions) if partitions else {}
                    total_messages = sum(end_offsets.values()) if end_offsets else 0
                    consumer.close()

                    topics_detail.append({
                        'name': topic,
                        'partitions': len(partitions) if partitions else 0,
                        'messages': total_messages,
                        'stat': topic_stats.get(topic)
                    })
                except Exception as e:
                    topics_detail.append({
                        'name': topic,
                        'partitions': 0,
                        'messages': 0,
                        'error': str(e)
                    })

            return render_template('kafka_dashboard.html',
                                   topics=topics_detail,
                                   kafka_status=bool(producer))
        except NoBrokersAvailable:
            return render_template('kafka_dashboard.html',
                                   error="Kafka broker not available",
                                   kafka_status=False)
        except Exception as e:
            return render_template('kafka_dashboard.html',
                                   error=str(e),
                                   kafka_status=False)

    @app.route('/kafka/create-topic', methods=['POST'])
    def create_topic():
        """Создание нового топика"""
        topic_name = request.form.get('topic_name')
        partitions = int(request.form.get('partitions', 1))
        replication = int(request.form.get('replication', 1))

        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BROKER,
                client_id='devops-admin'
            )

            topic_list = [NewTopic(
                name=topic_name,
                num_partitions=partitions,
                replication_factor=replication
            )]

            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            admin_client.close()

            flash(f"✅ Топик '{topic_name}' успешно создан", 'success')
        except TopicAlreadyExistsError:
            flash(f"❌ Топик '{topic_name}' уже существует", 'error')
        except Exception as e:
            flash(f"❌ Ошибка: {str(e)}", 'error')

        return redirect(url_for('kafka_dashboard'))

    @app.route('/kafka/send-message', methods=['POST'])
    def send_kafka_message():
        """Отправка кастомного сообщения в топик"""
        topic = request.form.get('topic')
        key = request.form.get('key', '')
        message = request.form.get('message')

        if not message:
            flash("❌ Сообщение не может быть пустым", 'error')
            return redirect(url_for('kafka_dashboard'))

        try:
            msg_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: v.encode('utf-8') if v else None
            )

            # Пытаемся распарсить JSON или отправляем как строку
            try:
                msg_value = json.loads(message)
            except:
                msg_value = message

            future = msg_producer.send(
                topic,
                value=msg_value,
                key=key.encode('utf-8') if key else None
            )
            result = future.get(timeout=10)

            # Обновляем статистику в БД
            stat = KafkaTopicStat.query.filter_by(topic_name=topic).first()
            if stat:
                stat.message_count += 1
            else:
                stat = KafkaTopicStat(
                    topic_name=topic,
                    message_count=1,
                    partition_count=result.partition + 1
                )
                db.session.add(stat)
            db.session.commit()

            msg_producer.close()
            flash(f"✅ Сообщение отправлено в топик '{topic}' (партиция {result.partition})", 'success')
        except Exception as e:
            flash(f"❌ Ошибка: {str(e)}", 'error')

        return redirect(url_for('kafka_dashboard'))

    @app.route('/kafka/view-topic/<topic_name>')
    def view_topic(topic_name):
        """Просмотр сообщений из топика"""
        limit = int(request.args.get('limit', 20))
        messages = []

        try:
            consumer = KafkaConsumer(
                topic_name,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=3000
            )

            # Получаем информацию о партициях
            partitions = consumer.partitions_for_topic(topic_name)

            # Читаем сообщения
            for msg in consumer:
                try:
                    value = json.loads(msg.value.decode('utf-8')) if msg.value else None
                except:
                    value = msg.value.decode('utf-8') if msg.value else None

                messages.append({
                    'partition': msg.partition,
                    'offset': msg.offset,
                    'key': msg.key.decode('utf-8') if msg.key else None,
                    'value': value,
                    'timestamp': msg.timestamp
                })

                if len(messages) >= limit:
                    break

            consumer.close()

            return render_template('kafka_topic_view.html',
                                   topic=topic_name,
                                   messages=messages,
                                   partitions=partitions,
                                   limit=limit)
        except Exception as e:
            flash(f"❌ Ошибка при чтении топика: {str(e)}", 'error')
            return redirect(url_for('kafka_dashboard'))

    @app.route('/kafka/delete-topic/<topic_name>')
    def delete_topic(topic_name):
        """Удаление топика"""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BROKER,
                client_id='devops-admin'
            )
            admin_client.delete_topics([topic_name])
            admin_client.close()

            # Удаляем статистику из БД
            KafkaTopicStat.query.filter_by(topic_name=topic_name).delete()
            db.session.commit()

            flash(f"✅ Топик '{topic_name}' удалён", 'success')
        except Exception as e:
            flash(f"❌ Ошибка: {str(e)}", 'error')

        return redirect(url_for('kafka_dashboard'))