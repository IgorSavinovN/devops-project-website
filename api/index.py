import sys
import os

# Добавляем корневую папку в путь, чтобы найти app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel ищет переменную с именем 'app'
handler = app
