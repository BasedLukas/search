from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
import signal
import time
from urllib.parse import urlparse, urljoin
import os
from bs4 import BeautifulSoup
import requests
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
JINA_API_KEY = os.getenv("JINA_API_KEY")

def get_url(
    url: str,
    target_selector: str = None,
    wait_for_selector: str = None,
    header: dict = None,
    cookies: dict = None,
    proxy: str = None,
    headless: bool = True,
    output: str = 'markdown'
) -> str:
    """
    Fetch the content of a URL using the Jina Reader API.

    This function sends a GET request to the Jina Reader API endpoint to retrieve the content
    of a specified URL, with optional parameters to customize the request.

    :param url: The target URL to fetch content from (without the base API URL, e.g., 'https://example.com')
    :type url: str
    :param target_selector: A CSS selector to extract specific elements from the page (e.g., 'h1', '.content')
    :type target_selector: str, optional
    :param wait_for_selector: A CSS selector to wait for before fetching content (e.g., '#main')
    :type wait_for_selector: str, optional
    :param header: Custom HTTP headers to send with the request to the target URL (e.g., {'User-Agent': 'CustomAgent'})
    :type header: dict, optional
    :param cookies: Cookies to send with the request to the target URL (e.g., {'session_id': 'abc123'})
    :type cookies: dict, optional
    :param proxy: Proxy server URL to route the request through (e.g., 'http://proxy.example.com:8080')
    :type proxy: str, optional
    :param headless: Whether to run the browser in headless mode (True for no UI, False to disable headless)
    :type headless: bool, default True
    :param output: The desired output format of the response, specified via the 'X-Respond-With' header
                  (options: 'markdown', 'text', 'html', 'screenshot')
    :type output: str, default 'markdown'
    :return: The content of the URL as a string, in the specified output format
    :rtype: str
    """
    base = 'https://r.jina.ai/'
    full_url = base + url
    query_params = {}

    # Add optional query parameters if provided
    if target_selector:
        query_params['target_selector'] = target_selector
    if wait_for_selector:
        query_params['wait_for_selector'] = wait_for_selector
    if header:
        # Serialize headers into a comma-separated string
        header_str = ', '.join([f"{k}: {v}" for k, v in header.items()])
        query_params['header'] = header_str
    if cookies:
        # Serialize cookies into a semicolon-separated string
        cookies_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        query_params['cookies'] = cookies_str
    if proxy:
        query_params['proxy'] = proxy
    if not headless:
        # Only include headless parameter if False, assuming True is default
        query_params['headless'] = 'false'

    # Append query parameters to the URL if any exist
    if query_params:
        full_url += '?' + urllib.parse.urlencode(query_params)

    # Set up request headers
    headers = {
        'Authorization': f'Bearer {JINA_API_KEY}',
        'X-Respond-With': output
    }

    # Make the API request
    response = requests.get(full_url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

class AgentSpider(CrawlSpider):
    name = "simple_crawler"
    allowed_domains = ["openai.github.io"]
    start_urls = [
        "https://openai.github.io/openai-agents-python/"
    ]
    
    # Disable the automatic rule processing
    rules = ()
    
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'LOG_FILE': 'crawler.log',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOAD_DELAY': 0.25,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1.0,
        'AUTOTHROTTLE_MAX_DELAY': 10.0,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 86400,
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_IGNORE_HTTP_CODES': [401, 403, 404, 500, 501, 502, 503],
        'STATS_DUMP': True,
    }
    
    def __init__(self, *args, **kwargs):
        super(AgentSpider, self).__init__(*args, **kwargs)
        self.visited_urls = set()
        self.visited_fragments = set()
        self.items_processed = 0
        self.batch_size = 1000
        self.start_time = time.time()
        self.setup_signal_handlers()
        
        # Verify if Jina API key is available
        if not JINA_API_KEY:
            self.logger.error("JINA_API_KEY not found in environment variables. Please set it in your .env file.")
        else:
            self.logger.info("JINA_API_KEY found in environment variables.")
        
        # Create output directory if it doesn't exist
        self.output_dir = 'crawled_pages'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Print log location
        print(f"Logs will be written to: crawler.log")
        
    def setup_signal_handlers(self):
        """Set up graceful shutdown on signals"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Received shutdown signal. Closing spider gracefully...")
        elapsed = time.time() - self.start_time
        self.logger.info(f"Spider ran for {elapsed:.2f} seconds")
        self.logger.info(f"Processed {self.items_processed} items")
        self.logger.info(f"Average processing rate: {self.items_processed / elapsed:.2f} items/sec")
        raise CloseSpider("Shutdown signal received")
        
    def parse_start_url(self, response):
        """Override to ensure we process the start URL"""
        self.logger.info(f"Processing start URL: {response.url}")
        return self.parse(response)
        
    def parse(self, response):
        """Parse the page, find all links including fragment identifiers"""
        # Process the current page
        for item in self.process_page(response):
            yield item
        
        # Extract all links from the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links in the navigation menu
        links = []
        
        # Find all standard links (both regular and ones in navigation)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Skip external links and javascript
            if href.startswith('javascript:') or href.startswith('tel:') or href.startswith('mailto:'):
                continue
                
            # Get absolute URL
            absolute_url = urljoin(response.url, href)
            
            # Make sure it's within our allowed domain
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc and parsed_url.netloc not in self.allowed_domains:
                continue
                
            # Get link text for navigation purposes
            link_text = a_tag.get_text().strip()
            
            links.append((absolute_url, link_text))
        
        # Additionally, find all navigation elements (which may be nested)
        nav_elements = soup.find_all('nav', class_='md-nav')
        for nav in nav_elements:
            for a_tag in nav.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('javascript:') or href.startswith('tel:') or href.startswith('mailto:'):
                    continue
                    
                # Get absolute URL
                absolute_url = urljoin(response.url, href)
                
                # Make sure it's within our allowed domain
                parsed_url = urlparse(absolute_url)
                if parsed_url.netloc and parsed_url.netloc not in self.allowed_domains:
                    continue
                    
                # Get link text for navigation purposes
                link_text = a_tag.get_text().strip()
                
                links.append((absolute_url, link_text))
            
        # Follow links
        for url, link_text in links:
            # Check if we've already visited this URL (without fragment)
            parsed_url = urlparse(url)
            base_url = parsed_url._replace(fragment='').geturl()
            fragment = parsed_url.fragment
            
            # Track URL+fragment combination
            url_fragment_key = f"{base_url}#{fragment}" if fragment else base_url
            
            if url_fragment_key in self.visited_fragments:
                continue
                
            self.visited_fragments.add(url_fragment_key)
            self.logger.info(f"Following link: {url} ({link_text})")
            
            # Use meta to pass section information
            yield response.follow(
                url, 
                callback=self.parse,
                meta={
                    'section_title': link_text,
                    'parent_url': response.url
                }
            )
            
    def process_page(self, response):
        """Process a page and save its content using Jina API"""
        # Skip if not HTML
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type:
            return []  # Return empty list instead of None
            
        # Get URL for filename
        url = response.url
        parsed_url = urlparse(url)
        base_url = parsed_url._replace(fragment='').geturl()
        fragment = parsed_url.fragment
        
        # Create a unique key for this URL+fragment combination
        url_fragment_key = f"{base_url}#{fragment}" if fragment else base_url
        
        if url_fragment_key in self.visited_urls:
            return []  # Return empty list instead of None
            
        self.visited_urls.add(url_fragment_key)
        self.items_processed += 1
        
        # Log progress periodically
        if self.items_processed % self.batch_size == 0:
            elapsed = time.time() - self.start_time
            self.logger.info(f"Processed {self.items_processed} items ({self.items_processed / elapsed:.2f} items/sec)")
        
        # Get section title from meta if available
        section_title = response.meta.get('section_title', None)
        
        # Prepare target selector if fragment is present
        target_selector = None
        if fragment:
            target_selector = f"#{fragment}"
            
        # Use Jina API to get clean content
        try:
            # Strip the http:// or https:// prefix for the Jina API
            api_url = url.split('://', 1)[1] if '://' in url else url
            
            self.logger.info(f"Fetching clean content for {url} using Jina API")
            
            # Get clean content using Jina API
            clean_content = get_url(
                url=api_url,
                target_selector=target_selector,
                output='markdown'  # Get content in markdown format
            )
            
            # Add the title at the top if we have one and it's not already there
            if section_title and not clean_content.startswith(f"# {section_title}"):
                clean_content = f"# {section_title}\n\n{clean_content}"
            
            # Create a filename from the URL
            filename = self._url_to_filename(url)
            filepath = os.path.join(self.output_dir, filename)
            
            # Save clean content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_content)
                
            self.logger.info(f"Saved clean content from {url} to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error using Jina API for {url}: {str(e)}")
            # Fallback to original processing method if Jina API fails
            self.logger.info(f"Falling back to BeautifulSoup for {url}")
            
            # Extract content using BeautifulSoup (original method)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # If we have a fragment, try to extract just that section
            section_content = None
            
            if fragment:
                # Try to find the element with that ID
                section_element = soup.find(id=fragment)
                if section_element:
                    # Get content of this section
                    section_content = section_element
                    if not section_title:
                        # Try to extract a title
                        header = section_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if header:
                            section_title = header.get_text().strip()
            
            # If we couldn't extract a specific section or there's no fragment, use the whole page
            if not section_content:
                # For main page content, try to find the main content area
                main_content = soup.find('main') or soup.find(class_='md-content')
                section_content = main_content if main_content else soup
                
                # Try to get the page title if we don't have a section title
                if not section_title:
                    title_element = soup.find('title')
                    if title_element:
                        section_title = title_element.get_text().strip()
            
            # Remove script and style elements from the section
            for script in section_content.find_all(['script', 'style']):
                script.extract()
                
            # Get text
            text = section_content.get_text(separator='\n')
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Add the title at the top if we have one
            if section_title:
                text = f"# {section_title}\n\n{text}"
            
            # Create a filename from the URL
            filename = self._url_to_filename(url)
            filepath = os.path.join(self.output_dir, filename)
            
            # Save text to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
                
            self.logger.info(f"Saved content from {url} to {filepath} (fallback method)")
        
        # Always return an empty list to make the method iterable
        return []
        
    def _url_to_filename(self, url):
        """Convert URL to a valid filename"""
        # Remove protocol and domain
        parsed = urlparse(url)
        path = parsed.path
        fragment = parsed.fragment
        
        # Handle empty path or just '/'
        if not path or path == '/':
            base_filename = 'index'
        else:
            # Replace slashes and remove leading slash
            base_filename = path.replace('/', '_').lstrip('_')
        
        # Add fragment to filename if present
        if fragment:
            base_filename = f"{base_filename}_{fragment}"
            
        # Add .txt extension if not present
        if not base_filename.endswith('.txt'):
            base_filename += '.txt'
            
        # Handle very long filenames
        if len(base_filename) > 255:
            base_filename = base_filename[:250] + '.txt'
            
        return base_filename
