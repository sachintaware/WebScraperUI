from bs4 import BeautifulSoup
import requests
import time
from urllib.parse import urlparse

class RateLimiter:
    def __init__(self, requests_per_second=1):
        self.last_request = 0
        self.min_interval = 1.0 / requests_per_second

    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

rate_limiter = RateLimiter()

def scrape_website(url):
    rate_limiter.wait()
    
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
    
    return {
        'title': title,
        'content': content[:10000]  # Limit content length
    }
