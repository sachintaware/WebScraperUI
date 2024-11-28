import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add user loader
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    import models
    db.create_all()

    # Create initial agents if they don't exist
    from models import User, Agent
    
    analyzer = Agent.query.filter_by(name='Content Analyzer').first()
    if not analyzer:
        analyzer = Agent(
            name='Content Analyzer',
            role='Analyzer',
            goal='Go through the scraped content and identify websites style, tone of language, theme and vibe. Identify products/services provided by the website/client with USP\'s. Identify ICP(ideal customer profile) for the website.',
            backstory='You are a web Content analyst who can build product and customer profiles based on website data, blogs and articles available on the website. You can Identify products/services provided by the website/client with USP\'s and also Identify ICP(ideal customer profile) for the website.'
        )
        db.session.add(analyzer)

    generator = Agent.query.filter_by(name='Content Generator').first()
    if not generator:
        generator = Agent(
            name='Content Generator',
            role='Content Generator',
            goal='Generate highly engaging and platform-optimized content based on website analysis',
            backstory='You are an expert content writer with deep expertise in creating content for multiple platforms. You understand the nuances of different content types and how to optimize for each platform while maintaining brand voice and messaging.'
        )
        db.session.add(generator)
    
    db.session.commit()

    # Create default admin user if not exists
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()

from auth import *
