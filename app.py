from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_mail import Mail
from models import db, Project, Visit, Setting, ContactMessage
from routes import init_routes
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://igor:password@localhost/devopsdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка почты
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

db.init_app(app)

admin = Admin(app, name='DevOps Admin')
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Visit, db.session))
admin.add_view(ModelView(Setting, db.session))
init_routes(app, db, Project, Visit, Setting)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)