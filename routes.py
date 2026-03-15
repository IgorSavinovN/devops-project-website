from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta

def init_routes(app, db, Project, Visit, Setting):

    @app.route('/')
    def home():
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