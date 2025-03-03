import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import os
from urllib.parse import urlparse
import pymongo
import logging
from datetime import datetime

# Configure logging to only show errors
logging.getLogger('scrapy').setLevel(logging.INFO)
logging.getLogger('pymongo').setLevel(logging.ERROR)


class ToscrapeSpider(CrawlSpider):
    name = "toscrape"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://example.invalid"]

    rules = (
        Rule(LinkExtractor(allow_domains=allowed_domains), callback='parse_item', follow=True),
    )
    
    # Configure Spider logging and crawl behavior
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'CLOSESPIDER_PAGECOUNT': 100,  # Limit to 100 pages
        'ROBOTSTXT_OBEY': True,
    }
    

    

    # Modified parse_item method
    def parse_item(self, response):
        from src.items import WebpageItem  # Import your item class
        
        # only accept text/html
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type:
            return

        # Extract metadata from head section
        title = response.css('title::text').get() or ''
        meta_description = response.css('meta[name="description"]::attr(content)').get() or ''
        meta_keywords = response.css('meta[name="keywords"]::attr(content)').get() or ''
        meta_author = response.css('meta[name="author"]::attr(content)').get() or ''
        
        # Extract OpenGraph metadata
        og_title = response.css('meta[property="og:title"]::attr(content)').get() or ''
        og_description = response.css('meta[property="og:description"]::attr(content)').get() or ''
        og_image = response.css('meta[property="og:image"]::attr(content)').get() or ''
        og_type = response.css('meta[property="og:type"]::attr(content)').get() or ''
        
        # Extract canonical URL if available
        canonical_url = response.css('link[rel="canonical"]::attr(href)').get() or ''
        
        # Extract HTTP header information
        last_modified = response.headers.get('Last-Modified', b'').decode('utf-8', errors='ignore') or None
        etag = response.headers.get('ETag', b'').decode('utf-8', errors='ignore') or None
        
        # Create a Scrapy Item
        item = WebpageItem(
            url=response.url,
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            meta_author=meta_author,
            og_title=og_title,
            og_description=og_description, 
            og_image=og_image,
            og_type=og_type,
            canonical_url=canonical_url,
            last_modified=last_modified,
            etag=etag,
            content_type=content_type,
            raw_html=response.text,  # Store the complete HTML
            content_length=len(response.body),
            response_headers=str(response.headers),
            status_code=response.status,
            crawled_at=datetime.now(),
            depth=response.meta.get('depth', 0)
        )
        
        # Yield the item to be processed by the pipeline
        yield item

