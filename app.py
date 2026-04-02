from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import db, Project, Visit, Setting
from routes import init_routes
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://igor:password@localhost/devopsdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

admin = Admin(app, name='DevOps Admin')
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Visit, db.session))
admin.add_view(ModelView(Setting, db.session))
init_routes(app, db, Project, Visit, Setting)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)