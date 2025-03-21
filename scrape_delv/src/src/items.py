# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# src/items.py
import scrapy

class WebpageItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    meta_description = scrapy.Field()
    meta_language = scrapy.Field()
    og_title = scrapy.Field()
    og_description = scrapy.Field()
    canonical_url = scrapy.Field()
    last_modified = scrapy.Field()
    etag = scrapy.Field()
    content_type = scrapy.Field()
    raw_html = scrapy.Field()
    content_length = scrapy.Field()
    response_headers = scrapy.Field()
    status_code = scrapy.Field()
    crawled_at = scrapy.Field()
    depth = scrapy.Field()
