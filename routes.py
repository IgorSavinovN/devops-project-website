@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/status')
def status():
    # Проверка PostgreSQL
    try:
        from models import db
        db.session.execute('SELECT 1')
        pg_status = True
    except:
        pg_status = False

    # Проверка Kafka (заглушка, пока не подключена)
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(bootstrap_servers='localhost:9092')
        producer.close()
        kafka_status = True
    except:
        kafka_status = False

    return render_template('status.html', pg_status=pg_status, kafka_status=kafka_status)