import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.db')

def get_db():
    """Подключение к SQLite"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Создание таблицы"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    db.close()
    print("Database initialized!")

def save_message(name, email, message):
    """Сохранить сообщение"""
    db = get_db()
    cur = db.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    db.commit()
    message_id = cur.lastrowid
    db.close()
    return message_id

def get_all_messages():
    """Получить все сообщения"""
    db = get_db()
    cur = db.execute("SELECT * FROM messages ORDER BY created_at DESC")
    messages = cur.fetchall()
    db.close()
    return [dict(msg) for msg in messages]

def get_messages_count():
    """Количество сообщений"""
    db = get_db()
    cur = db.execute("SELECT COUNT(*) as count FROM messages")
    result = cur.fetchone()
    db.close()
    return result['count'] if result else 0
