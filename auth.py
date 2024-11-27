from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db, login_manager
from models import User, ScrapedData
from scraper import parse_sitemap, scrape_website, scrape_multiple_pages
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

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
    
    # Get unique domains with page counts
    domains = db.session.query(
        ScrapedData.domain,
        db.func.count(ScrapedData.id).label('page_count')
    ).group_by(ScrapedData.domain).all()
    
    # Get pages for selected domain
    selected_domain = request.args.get('domain')
    query = ScrapedData.query
    
    if selected_domain:
        query = query.filter_by(domain=selected_domain)
    if search:
        query = query.filter(
            (ScrapedData.title.ilike(f'%{search}%')) |
            (ScrapedData.content.ilike(f'%{search}%'))
        )
    
    pagination = query.order_by(ScrapedData.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template(
        'data.html',
        pagination=pagination,
        search=search,
        domains=domains,
        selected_domain=selected_domain
    )

@app.route('/scrape', methods=['POST'])
@login_required
def scrape():
    url = request.form.get('url')
    if not url:
        flash('URL is required')
        return redirect(url_for('dashboard'))
    
    try:
        # Try to parse sitemap first
        logger.info(f"Attempting to scrape URL: {url}")
        try:
            urls = parse_sitemap(url)
            logger.info(f"Successfully parsed sitemap, found {len(urls)} URLs")
            flash(f'Found {len(urls)} URLs in sitemap, starting scraping...')
            results = scrape_multiple_pages(urls)
        except Exception as sitemap_error:
            logger.info(f"No sitemap found or error parsing sitemap: {sitemap_error}")
            # If sitemap parsing fails, treat as single URL
            results = [scrape_website(url)]
            results[0]['url'] = url
        
        # Save all results
        success_count = 0
        error_count = 0
        
        for result in results:
            data = ScrapedData(
                url=result['url'],
                title=result['title'],
                content=result['content'],
                status=result.get('status', 'success'),
                domain=result.get('domain', '')
            )
            db.session.add(data)
            if result.get('status') == 'success':
                success_count += 1
            else:
                error_count += 1
        
        db.session.commit()
        
        if len(results) > 1:
            flash(f'Scraping completed: {success_count} successful, {error_count} failed')
        else:
            flash('Website scraped successfully')
            
    except Exception as e:
        logger.error(f"Error in scrape route: {str(e)}")
        flash(f'Error scraping website: {str(e)}')
    
    return redirect(url_for('dashboard'))


@app.route('/website/<domain>')
@login_required
def website_details(domain):
    page = request.args.get('page', 1, type=int)
    query = ScrapedData.query.filter_by(domain=domain)
    pagination = query.order_by(ScrapedData.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('website_details.html', domain=domain, pagination=pagination)