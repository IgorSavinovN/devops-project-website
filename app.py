from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://igor:password@localhost/devopsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели данных
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, done
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45))
    page = db.Column(db.String(100))
    user_agent = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.String(200))

# Админка
admin = Admin(app, name='DevOps Admin')
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Visit, db.session))
admin.add_view(ModelView(Setting, db.session))

# HTML шаблон
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevOps Project Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --card-bg: rgba(255, 255, 255, 0.95);
            --text-color: #333;
            --text-secondary: #666;
            --border-color: #e0e0e0;
            --input-bg: white;
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        [data-theme="dark"] {
            --bg-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            --card-bg: rgba(30, 30, 46, 0.95);
            --text-color: #f0f0f0;
            --text-secondary: #b0b0b0;
            --border-color: #2a2a3a;
            --input-bg: #2a2a3a;
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-gradient);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-color);
            transition: background 0.3s, color 0.3s;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 20px;
        }

        .title {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #e0e0ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        .theme-switch {
            background: var(--card-bg);
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            color: var(--text-color);
            box-shadow: var(--shadow);
            transition: transform 0.2s;
        }

        .theme-switch:hover {
            transform: scale(1.05);
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 15px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
            transition: transform 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-title {
            font-size: 1.1em;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .stat-trend {
            font-size: 0.9em;
            color: #4CAF50;
        }

        /* Form */
        .project-form {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 15px;
            box-shadow: var(--shadow);
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .project-form input,
        .project-form select,
        .project-form textarea {
            padding: 12px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            background: var(--input-bg);
            color: var(--text-color);
            font-size: 1em;
            transition: border-color 0.3s;
        }

        .project-form input:focus,
        .project-form select:focus,
        .project-form textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        .project-form button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .project-form button:hover {
            transform: scale(1.02);
        }

        /* Projects Grid */
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .project-card {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: var(--shadow);
            transition: all 0.3s;
            border: 1px solid var(--border-color);
        }

        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }

        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }

        .project-title {
            font-size: 1.3em;
            font-weight: 600;
            color: var(--text-color);
        }

        .project-priority {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }

        .priority-high { background: #ff4757; color: white; }
        .priority-medium { background: #ffa502; color: white; }
        .priority-low { background: #26de81; color: white; }

        .project-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            margin-bottom: 15px;
        }

        .status-done { background: #26de81; color: white; }
        .status-in_progress { background: #ffa502; color: white; }
        .status-pending { background: #ff4757; color: white; }

        .project-description {
            color: var(--text-secondary);
            margin-bottom: 15px;
            line-height: 1.5;
        }

        .project-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }

        .project-date {
            font-size: 0.85em;
            color: var(--text-secondary);
        }

        .project-actions a {
            color: var(--text-color);
            text-decoration: none;
            margin-left: 10px;
            opacity: 0.7;
            transition: opacity 0.2s;
        }

        .project-actions a:hover {
            opacity: 1;
        }

        /* Charts */
        .charts-container {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 15px;
            box-shadow: var(--shadow);
            margin-bottom: 30px;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .chart {
            height: 200px;
            position: relative;
        }

        .bar-chart {
            display: flex;
            align-items: flex-end;
            gap: 10px;
            height: 150px;
            margin-top: 20px;
        }

        .bar {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px 5px 0 0;
            min-width: 30px;
            transition: height 0.3s;
            position: relative;
        }

        .bar-label {
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            color: var(--text-secondary);
            white-space: nowrap;
        }

        .bar-value {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9em;
            font-weight: 600;
        }

        /* Flash messages */
        .flash-messages {
            margin-bottom: 20px;
        }

        .flash {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .flash.success { background: #26de81; color: white; }
        .flash.error { background: #ff4757; color: white; }
        .flash.info { background: #667eea; color: white; }

        /* Footer */
        .footer {
            text-align: center;
            margin-top: 50px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        .footer a {
            color: var(--text-color);
            text-decoration: none;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .title { font-size: 2em; }
            .stats-grid { grid-template-columns: 1fr; }
            .projects-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🚀 DevOps Project Dashboard</h1>
            <button class="theme-switch" onclick="toggleTheme()">🌓 Сменить тему</button>
        </div>

        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Всего проектов</div>
                <div class="stat-value">{{ total_projects }}</div>
                <div class="stat-trend">+{{ new_projects }} за неделю</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Выполнено</div>
                <div class="stat-value">{{ done_projects }}</div>
                <div class="stat-trend">{{ (done_projects/total_projects*100)|round|int if total_projects > 0 else 0 }}% успеха</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Посещений сегодня</div>
                <div class="stat-value">{{ today_visits }}</div>
                <div class="stat-trend">+{{ week_visits }} за неделю</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Активных проектов</div>
                <div class="stat-value">{{ active_projects }}</div>
                <div class="stat-trend">⚡ В работе</div>
            </div>
        </div>

        <form class="project-form" method="POST" action="/add">
            <input type="text" name="title" placeholder="Название проекта" required>
            <textarea name="description" placeholder="Описание" rows="1"></textarea>
            <select name="priority">
                <option value="low">🟢 Низкий приоритет</option>
                <option value="medium" selected>🟡 Средний приоритет</option>
                <option value="high">🔴 Высокий приоритет</option>
            </select>
            <select name="status">
                <option value="pending">⏳ В ожидании</option>
                <option value="in_progress">⚡ В работе</option>
                <option value="done">✅ Готово</option>
            </select>
            <button type="submit">➕ Добавить проект</button>
        </form>

        <div class="charts-container">
            <h2>📊 Статистика проектов</h2>
            <div class="charts-grid">
                <div class="chart">
                    <h3>По статусам</h3>
                    <div class="bar-chart">
                        <div class="bar" style="height: {{ (pending_projects/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ pending_projects }}</span>
                            <span class="bar-label">В ожидании</span>
                        </div>
                        <div class="bar" style="height: {{ (in_progress_projects/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ in_progress_projects }}</span>
                            <span class="bar-label">В работе</span>
                        </div>
                        <div class="bar" style="height: {{ (done_projects/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ done_projects }}</span>
                            <span class="bar-label">Готово</span>
                        </div>
                    </div>
                </div>
                <div class="chart">
                    <h3>По приоритетам</h3>
                    <div class="bar-chart">
                        <div class="bar" style="height: {{ (high_priority/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ high_priority }}</span>
                            <span class="bar-label">Высокий</span>
                        </div>
                        <div class="bar" style="height: {{ (medium_priority/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ medium_priority }}</span>
                            <span class="bar-label">Средний</span>
                        </div>
                        <div class="bar" style="height: {{ (low_priority/total_projects*150)|round if total_projects > 0 else 0 }}px">
                            <span class="bar-value">{{ low_priority }}</span>
                            <span class="bar-label">Низкий</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <h2>📋 Проекты</h2>
        <div class="projects-grid">
            {% for project in projects %}
            <div class="project-card">
                <div class="project-header">
                    <span class="project-title">{{ project.title }}</span>
                    <span class="project-priority priority-{{ project.priority }}">
                        {{ {'low': '🟢', 'medium': '🟡', 'high': '🔴'}[project.priority] }}
                    </span>
                </div>
                <div class="project-status status-{{ project.status }}">
                    {{ {'pending': '⏳ В ожидании', 'in_progress': '⚡ В работе', 'done': '✅ Готово'}[project.status] }}
                </div>
                <div class="project-description">{{ project.description or 'Нет описания' }}</div>
                <div class="project-footer">
                    <span class="project-date">{{ project.created_at.strftime('%Y-%m-%d') }}</span>
                    <div class="project-actions">
                        <a href="/edit/{{ project.id }}" title="Редактировать">✏️</a>
                        <a href="/delete/{{ project.id }}" title="Удалить" onclick="return confirm('Удалить проект?')">🗑️</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            <p>🕐 Время на сервере: {{ current_time }}</p>
            <p>👥 Онлайн: {{ active_visitors }} | 👁️ Всего посещений: {{ total_visits }}</p>
            <p><a href="/admin">🔐 Админка</a> | <a href="/api/stats">📡 API статистики</a> | <a href="/health">💚 Health check</a></p>
        </div>
    </div>

    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }

        // Загружаем сохранённую тему
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);

        // Анимация для flash сообщений
        setTimeout(() => {
            document.querySelectorAll('.flash').forEach(flash => {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 300);
            });
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Сохраняем посещение
    visit = Visit(
        ip=request.remote_addr,
        page=request.path,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(visit)
    db.session.commit()

    # Статистика проектов
    projects = Project.query.order_by(Project.created_at.desc()).all()
    total_projects = Project.query.count()
    done_projects = Project.query.filter_by(status='done').count()
    pending_projects = Project.query.filter_by(status='pending').count()
    in_progress_projects = Project.query.filter_by(status='in_progress').count()

    # По приоритетам
    high_priority = Project.query.filter_by(priority='high').count()
    medium_priority = Project.query.filter_by(priority='medium').count()
    low_priority = Project.query.filter_by(priority='low').count()

    # Посещения
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_visits = Visit.query.filter(Visit.timestamp >= today).count()
    week_visits = Visit.query.filter(Visit.timestamp >= today - timedelta(days=7)).count()
    total_visits = Visit.query.count()

    # Активные посетители (за последние 5 минут)
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    active_visitors = Visit.query.filter(Visit.timestamp >= five_min_ago).count()

    # Новые проекты за неделю
    new_projects = Project.query.filter(Project.created_at >= today - timedelta(days=7)).count()

    return render_template_string(
        HTML_TEMPLATE,
        projects=projects,
        total_projects=total_projects,
        done_projects=done_projects,
        pending_projects=pending_projects,
        in_progress_projects=in_progress_projects,
        active_projects=in_progress_projects,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority,
        today_visits=today_visits,
        week_visits=week_visits,
        total_visits=total_visits,
        active_visitors=active_visitors,
        new_projects=new_projects,
        current_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/add', methods=['POST'])
def add_project():
    try:
        project = Project(
            title=request.form['title'],
            description=request.form.get('description', ''),
            priority=request.form.get('priority', 'medium'),
            status=request.form.get('status', 'pending')
        )
        db.session.add(project)
        db.session.commit()
        flash('Проект успешно добавлен!', 'success')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('Проект удалён', 'success')
    return redirect(url_for('home'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form.get('description', '')
        project.priority = request.form.get('priority', 'medium')
        project.status = request.form.get('status', 'pending')
        db.session.commit()
        flash('Проект обновлён!', 'success')
        return redirect(url_for('home'))

    # GET запрос — показываем форму редактирования
    return f"""
    <form method="POST">
        <input name="title" value="{project.title}">
        <textarea name="description">{project.description}</textarea>
        <select name="priority">
            <option value="low" {"selected" if project.priority=="low" else ""}>Низкий</option>
            <option value="medium" {"selected" if project.priority=="medium" else ""}>Средний</option>
            <option value="high" {"selected" if project.priority=="high" else ""}>Высокий</option>
        </select>
        <select name="status">
            <option value="pending" {"selected" if project.status=="pending" else ""}>В ожидании</option>
            <option value="in_progress" {"selected" if project.status=="in_progress" else ""}>В работе</option>
            <option value="done" {"selected" if project.status=="done" else ""}>Готово</option>
        </select>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/">Назад</a>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    return jsonify({
        "projects": {
            "total": Project.query.count(),
            "done": Project.query.filter_by(status='done').count(),
            "in_progress": Project.query.filter_by(status='in_progress').count(),
            "pending": Project.query.filter_by(status='pending').count()
        },
        "visits": {
            "total": Visit.query.count(),
            "today": Visit.query.filter(Visit.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)).count()
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/projects')
def api_projects():
    projects = Project.query.all()
    return jsonify([{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "status": p.status,
        "priority": p.priority,
        "created_at": p.created_at.isoformat()
    } for p in projects])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Добавим тестовые данные если их нет
        if Project.query.count() == 0:
            test_projects = [
                Project(title="Настроить CI/CD", description="GitHub Actions автоматизация", priority="high", status="in_progress"),
                Project(title="Установить Grafana", description="Мониторинг сервера", priority="medium", status="done"),
                Project(title="Написать документацию", description="README и wiki", priority="low", status="pending"),
            ]
            db.session.add_all(test_projects)
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)