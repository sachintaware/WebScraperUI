from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db, login_manager
from models import User, ScrapedData
from scraper import parse_sitemap, scrape_website, scrape_multiple_pages
from analyzer import ContentAnalyzer
from flask import jsonify
from models import User, ScrapedData, ContentAnalysis
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db


@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    try:
        # Only delete ScrapedData, preserve User data
        db.session.query(ScrapedData).delete()
        db.session.commit()
        flash('Successfully cleared all scraped data')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing data: {str(e)}')
    return redirect(url_for('data'))


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
        db.func.count(ScrapedData.id).label('page_count')).group_by(
            ScrapedData.domain).all()

    # Get pages for selected domain
    selected_domain = request.args.get('domain')
    query = ScrapedData.query

    if selected_domain:
        query = query.filter_by(domain=selected_domain)
    if search:
        query = query.filter((ScrapedData.title.ilike(f'%{search}%'))
                             | (ScrapedData.content.ilike(f'%{search}%')))

    pagination = query.order_by(ScrapedData.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    return render_template('data.html',
                           pagination=pagination,
                           search=search,
                           domains=domains,
                           selected_domain=selected_domain)


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
            logger.info(
                f"No sitemap found or error parsing sitemap: {sitemap_error}")
            # If sitemap parsing fails, treat as single URL
            results = [scrape_website(url)]
            results[0]['url'] = url

        # Save all results
        success_count = 0
        error_count = 0

        for result in results:
            data = ScrapedData(url=result['url'],
                               title=result['title'],
                               content=result['content'],
                               status=result.get('status', 'success'),
                               domain=result.get('domain', ''))
            db.session.add(data)
            if result.get('status') == 'success':
                success_count += 1
            else:
                error_count += 1

        db.session.commit()

        if len(results) > 1:
            flash(
                f'Scraping completed: {success_count} successful, {error_count} failed'
            )
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
    try:
        app.logger.info(f"Fetching website details for domain: {domain}")
        query = ScrapedData.query.filter_by(domain=domain)
        pagination = query.order_by(ScrapedData.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False)
        if pagination.total == 0:
            app.logger.warning(f"No pages found for domain: {domain}")
            flash('No pages found for this domain')
            return redirect(url_for('data'))
        app.logger.info(f"Found {pagination.total} pages for domain: {domain}")
        return render_template('website_details.html',
                               domain=domain,
                               pagination=pagination)
    except Exception as e:
        app.logger.error(
            f"Error loading website details for domain {domain}: {str(e)}")


@app.route('/analyze/<int:content_id>', methods=['POST'])
@login_required
def analyze_content(content_id):
    try:
        content = ScrapedData.query.get_or_404(content_id)
        analyzer = ContentAnalyzer()
        analysis_result = analyzer.analyze_content(content.content,
                                                   content.url)
        # Restructure the analysis result to match the expected format
        analysis = {
            'style_tone':
            analysis_result.get('website_style', {}).get('tone', '') +
            '\nTheme: ' +
            analysis_result.get('website_style', {}).get('theme', ''),
            'products_services':
            '\n'.join([
                f"• {product['name']}: " + '\n  USPs: ' +
                '\n  - '.join(product['usps'])
                for product in analysis_result.get('products_services', [])
            ]),
            'icp':
            (f"Description: {analysis_result.get('ideal_customer_profile', {}).get('description', '')}\n\n"
             + f"Key Attributes:\n- " + '\n- '.join(
                 analysis_result.get('ideal_customer_profile', {}).get(
                     'key_attributes', [])))
        }
        # Save analysis results
        new_analysis = ContentAnalysis(
            scraped_data_id=content_id,
            style_tone=analysis['style_tone'],
            products_services=analysis['products_services'],
            icp=analysis['icp'])
        db.session.add(new_analysis)
        db.session.commit()
        return jsonify(analysis)
    except Exception as e:
        app.logger.error(f"Analysis error for content {content_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
