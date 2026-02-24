from flask import Flask, render_template, request
import datetime
import os
from models import init_db, save_message, get_all_messages, get_messages_count

app = Flask(__name__)

# Инициализируем БД при запуске
init_db()

@app.route('/')
def home():
    messages_count = get_messages_count()
    return render_template('index.html', 
                          message="Привет, DevOps-инженер!",
                          time=datetime.datetime.now(),
                          messages_count=messages_count)

@app.route('/about')
def about():
    return render_template('about.html')

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
        
        message_id = save_message(name, email, message)
        
        return f"Спасибо, {name}! Мы получили ваше сообщение (ID: {message_id})"
    return render_template('contact.html')

@app.route('/calendar')
@app.route('/calendar.html')
def calendar():
    return render_template('calendar.html')


@app.route('/admin/messages')
def admin_messages():
    messages = get_all_messages()
    return render_template('messages.html', messages=messages)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
