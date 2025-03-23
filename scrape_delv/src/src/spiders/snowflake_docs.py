from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import logging
from datetime import datetime

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

    rules = (
        Rule(LinkExtractor(allow_domains=allowed_domains), callback='parse_item', follow=True),
    )
    
    # Configure Spider logging and crawl behavior
    custom_settings = {
        'LOG_LEVEL': 'DEBUG',
        'LOG_ENABLED': True,
        'LOG_FILE': 'snowflake.log',
        'CLOSESPIDER_PAGECOUNT': 100,  # Limit page numbers
        'ROBOTSTXT_OBEY': True,
    'ITEM_PIPELINES': {
        'src.pipelines.MongoDBPipeline': 300,
    }
    }
    
    def parse_item(self, response):
        """
        Parse HTML response and extract document metadata.
        
        Args:
            response: Scrapy response object
            
        Returns:
            WebpageItem: Item containing extracted metadata
        """
        from src.items import WebpageItem

        # Skip non-HTML content
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type:
            return

        # Extract language carefully from various potential sources
        lang = self._extract_language(response)
        
        # Create the item with all required fields
        item = WebpageItem(
            url=response.url,
            title=response.css('title::text').get() or '',
            description=response.css('meta[name="description"]::attr(content), meta[property="og:description"]::attr(content)').get() or '',
            lang=lang,
            last_modified=response.headers.get('Last-Modified', b'').decode('utf-8', errors='ignore') or None,
            etag=response.headers.get('ETag', b'').decode('utf-8', errors='ignore') or None,
            raw_html=response.text,
            headers=str(response.headers),
            status_code=response.status,
            crawled_at=datetime.now(),
        )
        
        return item
    
    def _extract_language(self, response):
        """
        Extract language from HTML using multiple methods in order of reliability.
        
        Args:
            response: Scrapy response object
            
        Returns:
            str: Detected language code or empty string if not found
        """
        # Method 1: Check html lang attribute (most common)
        lang = response.css('html::attr(lang)').get()
        if lang:
            return lang.strip()
            
        # Method 2: Check Content-Language meta tag
        lang = response.css('meta[http-equiv="Content-Language"]::attr(content)').get()
        if lang:
            return lang.strip()
            
        # Method 3: Check hreflang link elements
        # Often the default language will have x-default or no locale
        lang = response.css('link[rel="alternate"][hreflang="x-default"]::attr(hreflang)').get()
        if lang:
            return lang.strip()
            
        # Method 4: Try to extract from URL structure if it follows a pattern like /en/
        url_parts = response.url.split('/')
        for part in url_parts:
            if len(part) == 2:  # Most language codes are 2 characters
                return part
                

        # Default to empty string if no language detected
        return ''