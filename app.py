from flask import Flask, render_template, request
import datetime
import os
import calendar
from models import init_db, save_message, get_all_messages, get_messages_count
init_db()
app = Flask(__name__)

# Домашняя страница
@app.route('/')
def home():
    return render_template('index.html', 
                          message="Привет, DevOps-инженер!",
                          time=datetime.datetime.now())

# Страница "О нас"
@app.route('/about')
def about():
    return render_template('about.html')

# Страница с информацией о сервере
@app.route('/system')
def system_info():
    info = {
        'hostname': os.uname().nodename,
        'os': os.uname().sysname,
        'python_version': os.sys.version,
        'current_dir': os.getcwd(),
        'user': os.environ.get('USER', 'unknown')
    }
    return render_template('system.html', info=info)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        
        # Сохраняем в базу данных
        from models import save_message
        message_id = save_message(name, email, message)
        
        return f"Спасибо, {name}! Мы получили ваше сообщение (ID: {message_id})"
    return render_template('contact.html')       



# Календарь
@app.route('/calendar.html')
def calendar_page():
    # Получаем текущий год и месяц
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    # Генерируем календарь месяца в виде HTML
    cal = calendar.HTMLCalendar(firstweekday=0)  # Понедельник первый день
    month_calendar = cal.formatmonth(year, month)

    return render_template('calendar.html', month_calendar=month_calendar, year=year, month=month)



# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
