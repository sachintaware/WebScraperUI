from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, ScrapedData, ContentAnalysis, DomainSummary, Agent
from scraper import scrape_website, scrape_multiple_pages, parse_sitemap
from analyzer import ContentAnalyzer
from werkzeug.security import check_password_hash
import json

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    try:
        result = scrape_website(url)
        
        # Save to database
        scraped_data = ScrapedData(
            url=url,
            title=result['title'],
            content=result['content'],
            status=result['status'],
            domain=result['domain']
        )
        db.session.add(scraped_data)
        db.session.commit()
        
        flash('Website scraped successfully!')
    except Exception as e:
        flash(f'Error scraping website: {str(e)}')
    
    return redirect(url_for('dashboard'))

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

@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    try:
        ScrapedData.query.delete()
        db.session.commit()
        flash('All scraped data cleared successfully!')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}')
    
    return redirect(url_for('data'))

@app.route('/analyze/<int:content_id>', methods=['POST'])
@login_required
def analyze_content(content_id):
    try:
        scraped_data = ScrapedData.query.get_or_404(content_id)
        
        # Initialize analyzer
        analyzer = ContentAnalyzer()
        
        # Analyze content
        analysis_result = analyzer.analyze_content(scraped_data.content, scraped_data.url)
        
        # Save analysis to database
        analysis = ContentAnalysis(
            scraped_data_id=content_id,
            style_tone=json.dumps(analysis_result),
            products_services=json.dumps(analysis_result.get('website_analysis', {}).get('products_services', [])),
            icp=json.dumps(analysis_result.get('website_analysis', {}).get('ideal_customer_profile', {}))
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify(analysis_result)
        
    except Exception as e:
        app.logger.error(f"Error analyzing content {content_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/website/<domain>')
@login_required
def website_details(domain):
    # Get all scraped data for the domain
    scraped_data = ScrapedData.query.filter_by(domain=domain).all()
    if not scraped_data:
        flash('No data found for this domain')
        return redirect(url_for('data'))
    
    # Get domain summary if it exists
    domain_summary = DomainSummary.query.filter_by(domain=domain).first()
    
    return render_template('website_details.html', 
                         domain=domain,
                         scraped_data=scraped_data,
                         domain_summary=domain_summary)

@app.route('/domain_summary/<domain>')
@login_required
def domain_summary(domain):
    try:
        # Get all scraped data for the domain
        scraped_data = ScrapedData.query.filter_by(domain=domain).all()
        if not scraped_data:
            return jsonify({'error': 'No data found for this domain'}), 404
        
        # Combine all content for analysis
        combined_content = "\n".join(data.content for data in scraped_data)
        
        # Initialize analyzer
        analyzer = ContentAnalyzer()
        
        # Analyze combined content
        analysis_result = analyzer.analyze_content(combined_content, domain)
        
        # Extract components from analysis
        website_analysis = analysis_result.get('website_analysis', {})
        
        style_tone = [
            f"Style: {website_analysis.get('style', 'Not available')}",
            f"Tone: {website_analysis.get('tone', 'Not available')}",
            f"Theme: {website_analysis.get('theme', 'Not available')}"
        ]
        
        products_services = []
        for product in website_analysis.get('products_services', []):
            product_info = []
            if product.get('name'):
                product_info.append(f"Product/Service: {product['name']}")
            if product.get('description'):
                product_info.append(f"Description: {product['description']}")
            if product.get('USPs'):
                product_info.append("USPs:\n- " + "\n- ".join(product['USPs']))
            products_services.append("\n".join(product_info))
        
        icp = []
        icp_data = website_analysis.get('ideal_customer_profile', {})
        if icp_data:
            if icp_data.get('business_types'):
                icp.append("Business Types:\n- " + "\n- ".join(icp_data['business_types']))
            if icp_data.get('size'):
                icp.append(f"Size: {icp_data['size']}")
            if icp_data.get('goals'):
                icp.append("Goals:\n- " + "\n- ".join(icp_data['goals']))
            if icp_data.get('pain_points'):
                icp.append("Pain Points:\n- " + "\n- ".join(icp_data['pain_points']))
        
        # Save or update domain summary
        domain_summary = DomainSummary.query.filter_by(domain=domain).first()
        if domain_summary:
            domain_summary.style_tone = json.dumps(style_tone)
            domain_summary.products_services = json.dumps(products_services)
            domain_summary.icp = json.dumps(icp)
        else:
            domain_summary = DomainSummary(
                domain=domain,
                style_tone=json.dumps(style_tone),
                products_services=json.dumps(products_services),
                icp=json.dumps(icp)
            )
            db.session.add(domain_summary)
        
        db.session.commit()
        
        return jsonify({
            'style_tone': style_tone,
            'products_services': products_services,
            'icp': icp
        })
        
    except Exception as e:
        app.logger.error(f"Error generating domain summary for {domain}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/agents')
@login_required
def agents():
    agents = Agent.query.all()
    return render_template('agents.html', agents=agents)

@app.route('/content_generation')
@login_required
def content_generation():
    # Get unique domains from scraped data
    domains = db.session.query(ScrapedData.domain).distinct().all()
    domains = [domain[0] for domain in domains if domain[0]]  # Extract domain names and filter None
    return render_template('content_generation.html', domains=domains)

@app.route('/update_agent/<int:agent_id>', methods=['POST'])
@login_required
def update_agent(agent_id):
    try:
        agent = Agent.query.get_or_404(agent_id)
        agent.role = request.form.get('role')
        agent.goal = request.form.get('goal')
        agent.backstory = request.form.get('backstory')
        db.session.commit()
        flash('Agent updated successfully')
        return redirect(url_for('agents'))
    except Exception as e:
        flash(f'Error updating agent: {str(e)}')
        return redirect(url_for('agents'))

@app.route('/generate_content/<domain>', methods=['POST'])
@login_required
def generate_content(domain):
    try:
        content_type = request.json.get('content_type')
        title = request.json.get('title')
        
        if not content_type or not title:
            return jsonify({'error': 'Content type and title are required'}), 400
            
        # Get domain summary
        domain_summary = DomainSummary.query.filter_by(domain=domain).first()
        if not domain_summary:
            return jsonify({'error': 'Domain summary not found'}), 404

        # Initialize analyzer
        analyzer = ContentAnalyzer()
        
        # Prepare context for content generation
        context = {
            'style_tone': domain_summary.style_tone,
            'products_services': domain_summary.products_services,
            'icp': domain_summary.icp,
            'content_type': content_type,
            'title': title
        }

        # Generate content based on domain summary and content type
        generated_content = analyzer.generate_content(context)
        
        return jsonify({
            'content': generated_content
        })
        
    except Exception as e:
        app.logger.error(f"Error generating content for {domain}: {str(e)}")
        return jsonify({'error': str(e)}), 500
