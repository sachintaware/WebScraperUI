from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

class ScrapedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')
    domain = db.Column(db.String(200))

class ContentAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scraped_data_id = db.Column(db.Integer, db.ForeignKey('scraped_data.id'))
    style_tone = db.Column(db.Text)
    products_services = db.Column(db.Text)
    icp = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DomainSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(200), unique=True, nullable=False)
    style_tone = db.Column(db.Text)
    products_services = db.Column(db.Text)
    icp = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
