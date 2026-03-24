from models import db, Project, Visit, Setting, KafkaTopicStat
from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import os
import logging

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://igor:password@localhost/devopsdb')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
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
        try:
            db.session.execute('SELECT 1')
            pg_status = True
        except:
            pg_status = False

        try:
            test_producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            test_producer.close()
            kafka_status = True
        except:
            kafka_status = False

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