from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db
from models import User, ScrapedData
from scraper import scrape_website, scrape_multiple_pages, parse_sitemap
from analyzer import ContentAnalyzer
import logging

app.logger.setLevel(logging.INFO)

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

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/scrape', methods=['POST'])
@login_required
def scrape():
    url = request.form.get('url')
    if not url:
        flash('Please provide a URL')
        return redirect(url_for('dashboard'))
    
    try:
        # Try to get URLs from sitemap first
        try:
            urls = parse_sitemap(url)
            results = scrape_multiple_pages(urls)
        except Exception as e:
            app.logger.info(f"Sitemap parsing failed, falling back to single page: {str(e)}")
            results = [scrape_website(url)]
        
        for result in results:
            data = ScrapedData(
                url=result['url'],
                title=result['title'],
                content=result['content'],
                status=result['status'],
                domain=result['domain']
            )
            db.session.add(data)
        
        db.session.commit()
        flash('Website(s) scraped successfully')
        
    except Exception as e:
        flash(f'Error scraping website: {str(e)}')
        app.logger.error(f"Scraping error: {str(e)}")
    
    return redirect(url_for('data'))

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
    
    # Get unique domains with page counts
    domains = db.session.query(
        ScrapedData.domain,
        db.func.count(ScrapedData.id).label('page_count')).group_by(
            ScrapedData.domain).all()

    # Get pages for selected domain
    selected_domain = request.args.get('domain')

    return render_template('data.html', pagination=pagination, search=search, domains=domains, selected_domain=selected_domain)

@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    try:
        ScrapedData.query.delete()
        db.session.commit()
        flash('All scraped data cleared successfully')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}')
    return redirect(url_for('data'))

@app.route('/analyze/<int:content_id>', methods=['POST'])
@login_required
def analyze_content(content_id):
    try:
        content = ScrapedData.query.get_or_404(content_id)
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze_content(content.content, content.url)
        return jsonify(analysis)
    except Exception as e:
        app.logger.error(f"Analysis error for content {content_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/website/<domain>')
@login_required
def website_details(domain):
    # Get all scraped data for this domain
    items = ScrapedData.query.filter_by(domain=domain).all()
    if not items:
        flash('No data found for this domain')
        return redirect(url_for('data'))
    
    return render_template('website_details.html', domain=domain, items=items)

@app.route('/domain_summary/<domain>')
@login_required
def domain_summary(domain):
    try:
        # Get all content for this domain
        items = ScrapedData.query.filter_by(domain=domain).all()
        if not items:
            return jsonify({'error': 'No data found for this domain'})

        # Combine all content with proper separation
        combined_content = "\n\n=== Page Break ===\n\n".join(
            [f"Page: {item.url}\n\n{item.content}" for item in items if item.content]
        )
        
        # Initialize analyzer with combined content
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze_content(combined_content, domain)
        
        # Format response for frontend
        style_tone = []
        wa = analysis.get('website_analysis', {})
        if wa.get('style'): style_tone.append(f"Style: {wa['style']}")
        if wa.get('tone'): style_tone.append(f"Tone: {wa['tone']}")
        if wa.get('theme'): style_tone.append(f"Theme: {wa['theme']}")

        products_services = []
        for product in wa.get('products_services', []):
            product_info = []
            if product.get('name'): product_info.append(f"Product/Service: {product['name']}")
            if product.get('description'): product_info.append(f"Description: {product['description']}")
            if product.get('USPs'): product_info.append("USPs:\n- " + "\n- ".join(product['USPs']))
            if product_info: products_services.append("\n".join(product_info))

        icp_data = wa.get('ideal_customer_profile', {})
        icp = []
        if icp_data.get('business_types'): 
            icp.append("Business Types:\n- " + "\n- ".join(icp_data['business_types']))
        if icp_data.get('size'): 
            icp.append(f"Size: {icp_data['size']}")
        if icp_data.get('goals'): 
            icp.append("Goals:\n- " + "\n- ".join(icp_data['goals']))
        if icp_data.get('pain_points'): 
            icp.append("Pain Points:\n- " + "\n- ".join(icp_data['pain_points']))

        return jsonify({
            'style_tone': style_tone,
            'products_services': products_services,
            'icp': icp
        })
        
    except Exception as e:
        app.logger.error(f"Error generating domain summary for {domain}: {str(e)}")
        return jsonify({'error': str(e)}), 500