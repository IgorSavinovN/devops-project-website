from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import os
import logging

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://igor:password@localhost/devopsdb')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

        return render_template('status.html',
                               pg_status=pg_status)

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

    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "env": os.getenv("ENV", "production")})

    # --- Управление проектами (CRUD) ---
    @app.route('/projects/manage')
    def manage_projects():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('manage_projects.html', projects=projects)

    @app.route('/projects/add', methods=['GET', 'POST'])
    def add_project_form():
        if request.method == 'POST':
            project = Project(
                title=request.form['title'],
                description=request.form.get('description', ''),
                status=request.form.get('status', 'pending'),
                priority=request.form.get('priority', 'medium')
            )
            db.session.add(project)
            db.session.commit()
            flash('Проект добавлен', 'success')
            return redirect(url_for('manage_projects'))
        return render_template('project_form.html', title='Добавить проект')

    @app.route('/projects/edit/<int:id>', methods=['GET', 'POST'])
    def edit_project_form(id):
        project = Project.query.get_or_404(id)
        if request.method == 'POST':
            project.title = request.form['title']
            project.description = request.form.get('description', '')
            project.status = request.form.get('status', 'pending')
            project.priority = request.form.get('priority', 'medium')
            db.session.commit()
            flash('Проект обновлён', 'success')
            return redirect(url_for('manage_projects'))
        return render_template('project_form.html', title='Редактировать проект', project=project)

    @app.route('/projects/delete/<int:id>')
    def delete_project_form(id):
        project = Project.query.get_or_404(id)
        db.session.delete(project)
        db.session.commit()
        flash('Проект удалён', 'success')
        return redirect(url_for('manage_projects'))

    # --- Просмотр посещений ---
    @app.route('/visits.html')
    def list_visits():
        page = request.args.get('page', 1, type=int)
        visits = Visit.query.order_by(Visit.timestamp.desc()).paginate(page=page, per_page=20)
        return render_template('visits.html.html', visits=visits)

    # --- Статус БД (техническая страница) ---
    @app.route('/db-status')
    def db_status():
        try:
            db.session.execute('SELECT 1')
            db_status = '✅ PostgreSQL работает'
            tables = db.engine.table_names()
        except Exception as e:
            db_status = f'❌ Ошибка: {e}'
            tables = []
        return render_template('db_status.html', db_status=db_status, tables=tables)

