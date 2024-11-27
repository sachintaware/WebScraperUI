from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db, login_manager
from models import User, ScrapedData
from scraper import scrape_website
from urllib.parse import urlparse

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/data')
@login_required
def data():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = ScrapedData.query
    if search:
        query = query.filter(
            (ScrapedData.title.ilike(f'%{search}%')) |
            (ScrapedData.content.ilike(f'%{search}%'))
        )
    
    pagination = query.order_by(ScrapedData.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('data.html', pagination=pagination, search=search)

@app.route('/scrape', methods=['POST'])
@login_required
def scrape():
    url = request.form.get('url')
    if not url:
        flash('URL is required')
        return redirect(url_for('dashboard'))
    
    try:
        result = scrape_website(url)
        data = ScrapedData(
            url=url,
            title=result['title'],
            content=result['content']
        )
        db.session.add(data)
        db.session.commit()
        flash('Website scraped successfully')
    except Exception as e:
        flash(f'Error scraping website: {str(e)}')
    
    return redirect(url_for('dashboard'))
