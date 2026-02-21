import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Подключение к базе данных"""
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/myapp'),
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    """Создание таблиц, если их нет"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Создаем таблицу для сообщений
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized!")

def save_message(name, email, message):
    """Сохранить сообщение в БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s) RETURNING id",
        (name, email, message)
    )
    message_id = cur.fetchone()['id']
    
    conn.commit()
    cur.close()
    conn.close()
    
    return message_id

def get_all_messages():
    """Получить все сообщения"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM messages ORDER BY created_at DESC")
    messages = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return messages
