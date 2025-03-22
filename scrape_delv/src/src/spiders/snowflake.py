from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import logging
from datetime import datetime

# Configure logging to only show errors
# logging.getLogger('scrapy').setLevel(logging.INFO)
# logging.getLogger('pymongo').setLevel(logging.ERROR)


class ToscrapeSpider(CrawlSpider):
    name = "snowflake"
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
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'LOG_FILE': 'snowflake.log',
        'CLOSESPIDER_PAGECOUNT': 10,  # Limit page numbers
        'ROBOTSTXT_OBEY': True,
    }
    

    def parse_item(self, response):
        from src.items import WebpageItem  # Import your item class

        # Only accept text/html
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type:
            return

        # Extract metadata from head section
        title = response.css('title::text').get() or ''
        meta_description = response.css('meta[name="description"]::attr(content), meta[property="og:description"]::attr(content)').get() or ''
        
        # Extract language from either <meta> or <html lang="...">
        meta_language = response.css('meta[http-equiv="Content-Language"]::attr(content)').get() or ''
        if not meta_language:
            meta_language = response.css('html::attr(lang)').get() or ''  # Extract from <html lang="">

        # Extract OpenGraph metadata
        og_title = response.css('meta[property="og:title"]::attr(content), meta[name="og:title"]::attr(content)').get() or ''
        og_description = response.css('meta[property="og:description"]::attr(content), meta[name="og:description"]::attr(content)').get() or ''
        # Extract canonical URL
        canonical_url = response.css('link[rel="canonical"]::attr(href)').get() or ''

        # Extract HTTP headers
        last_modified = response.headers.get('Last-Modified', b'').decode('utf-8', errors='ignore') or None
        etag = response.headers.get('ETag', b'').decode('utf-8', errors='ignore') or None

        # Create a Scrapy Item
        item = WebpageItem(
            url=response.url,
            title=title,
            meta_description=meta_description,
            meta_language=meta_language,
            og_title=og_title,
            og_description=og_description,
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

