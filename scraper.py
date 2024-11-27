from bs4 import BeautifulSoup
import requests
import time
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_url(url):
    # Remove all whitespace, newlines, and control characters
    url = ''.join(char for char in url if not char.isspace())
    
    # Ensure proper URL format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Parse and rebuild URL to ensure proper format
    try:
        parsed = urlparse(url)
        # Rebuild URL with only necessary components
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    except Exception as e:
        raise ValueError(f"Invalid URL format: {str(e)}")

class RateLimiter:
    def __init__(self, requests_per_second=0.5):  # Changed to 1 request per 2 seconds
        self.last_request = 0
        self.min_interval = 1.0 / requests_per_second

    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

rate_limiter = RateLimiter()

def parse_sitemap(url):
    try:
        url = clean_url(url)
        if not url.endswith('sitemap.xml'):
            parsed = urlparse(url)
            url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
        logger.info(f"Attempting to parse sitemap: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        logger.info(f"Successfully parsed sitemap, found {len(urls)} URLs")
        return urls
    except Exception as e:
        logger.error(f"Error parsing sitemap: {str(e)}")
        raise Exception(f"Error parsing sitemap: {str(e)}")

def scrape_website(url):
    try:
        url = clean_url(url)
        if not url:
            raise ValueError("Invalid URL provided")
        rate_limiter.wait()
        logger.info(f"Scraping URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else url
        
        # Get main content (adjust selectors based on target website)
        content = ''
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            # Remove script and style elements
            for element in main_content(['script', 'style']):
                element.decompose()
            content = main_content.get_text(separator=' ', strip=True)
        
        logger.info(f"Successfully scraped URL: {url}")
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        return {
            'title': title,
            'content': content[:10000],  # Limit content length
            'status': 'success',
            'domain': domain
        }
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {str(e)}")
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        return {
            'title': url,
            'content': f'Error: {str(e)}',
            'status': 'error',
            'domain': domain
        }

def scrape_multiple_pages(urls):
    results = []
    total_urls = len(urls)
    
    for index, url in enumerate(urls, 1):
        try:
            logger.info(f"Processing URL {index}/{total_urls}: {url}")
            result = scrape_website(url)
            result['url'] = url
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            results.append({
                'url': url,
                'title': url,
                'content': f'Error: {str(e)}',
                'status': 'error'
            })
    
    return results
