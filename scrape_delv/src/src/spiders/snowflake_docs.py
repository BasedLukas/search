from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import IgnoreRequest, CloseSpider
import logging
from datetime import datetime
import signal
import time
from urllib.parse import urlparse
import re

class ToscrapeSpider(CrawlSpider):
    name = "snowflake_docs"
    allowed_domains = ["docs.snowflake.com"]
    start_urls = [
        "https://docs.snowflake.com/en/developer",
        "https://docs.snowflake.com/en/reference",
        "https://docs.snowflake.com/en/guides",
        "https://docs.snowflake.com/en/user-guide-getting-started",
        "https://docs.snowflake.com/en/tutorials",
        "https://docs.snowflake.com/en/"
    ]
    
    # Use stricter LinkExtractor to avoid unnecessary pages
    rules = (
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                deny=r'.*\.(css|js|jpg|jpeg|png|gif|pdf|zip|ico|svg)$'
            ), 
            callback='parse_item', 
            follow=True,
            process_links='filter_links'
        ),
    )
    
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'LOG_FILE': 'snowflake.log',
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
        'ITEM_PIPELINES': {
            'src.pipelines.MongoDBPipeline': 300,
        },
        'SPIDER_MIDDLEWARES': {
            'src.middlewares.LanguageMiddleware': 543,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
        },
        'STATS_DUMP': True,
    }
    
    def __init__(self, *args, **kwargs):
        super(ToscrapeSpider, self).__init__(*args, **kwargs)
        self.visited_urls = set()
        self.items_processed = 0
        self.batch_size = 1000
        self.start_time = time.time()
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Set up graceful shutdown on signals"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Received shutdown signal. Closing spider gracefully...")
        stats = self.crawler.stats.get_stats()
        elapsed = time.time() - self.start_time
        self.logger.info(f"Spider ran for {elapsed:.2f} seconds")
        self.logger.info(f"Processed {self.items_processed} items")
        self.logger.info(f"Average processing rate: {self.items_processed / elapsed:.2f} items/sec")
        raise CloseSpider("Shutdown signal received")
        
    def filter_links(self, links):
        """Filter links to avoid processing duplicates and non-relevant pages"""
        filtered_links = []
        for link in links:
            # Skip if we've already seen this URL
            if link.url in self.visited_urls:
                continue
                
            # Skip URLs that match patterns we want to avoid
            if self._should_skip_url(link.url):
                continue
                
            # Add to filtered links and mark as visited
            filtered_links.append(link)
            self.visited_urls.add(link.url)
            
        return filtered_links
        
    def _should_skip_url(self, url):
        """Check if URL should be skipped based on patterns"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Skip common file types and paths that won't contain useful content
        skip_patterns = [
            r'/(search|login|logout|register|signup|signin|404|500)/?$',
            r'.*\.(css|js|jpg|jpeg|png|gif|pdf|zip|ico|svg)$',
            r'/assets/',
            r'/static/',
            r'/comments/',
            r'/tag/',
            r'/category/',
            r'/author/',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, path):
                return True
                
        return False
        
    def parse_item(self, response):
        """Parse HTML response and extract document metadata, optimized for performance"""
        from src.items import WebpageItem

        # Skip non-HTML content
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type:
            return None

        # Check language - use the optimized version
        lang = self._extract_language_fast(response)
        
        # If not English, skip
        if lang not in ['en', '']:
            response.meta['dont_follow'] = True
            return None
            
        # Update processed items count and log progress
        self.items_processed += 1
        if self.items_processed % self.batch_size == 0:
            elapsed = time.time() - self.start_time
            self.logger.info(f"Processed {self.items_processed} items ({self.items_processed / elapsed:.2f} items/sec)")
            
        # Create a lightweight item - only store what's necessary
        item = WebpageItem(
            url=response.url,
            title=self._extract_title(response),
            description=self._extract_description(response),
            lang=lang,
            etag=response.headers.get('ETag', ''),
            last_modified=response.headers.get('Last-Modified', ''),
            headers=str(response.headers),
            raw_html=response.text, 
            status_code=response.status,
            crawled_at=datetime.now(),
        )
        return item

    def _extract_title(self, response):
        """Extract title with efficient CSS selector"""
        return response.css('title::text').get() or ''
        
    def _extract_description(self, response):
        """Extract description with efficient CSS selector"""
        return response.css('meta[name="description"]::attr(content)').get() or \
               response.css('meta[property="og:description"]::attr(content)').get() or ''

    def _extract_language_fast(self, response):
        """
        Optimized language extraction focusing only on most common method
        """
        # Method 1: Check html lang attribute (most common and fastest)
        lang = response.css('html::attr(lang)').get()
        if lang:
            return lang.strip().lower()[:2]  # Just get the 2-letter code
            
        # Method 2: Try to extract from URL structure if it follows a pattern like /en/
        path = urlparse(response.url).path
        match = re.search(r'/([a-z]{2})/', path)
        if match:
            return match.group(1)
                
        # Default to empty string if no language detected
        return ''