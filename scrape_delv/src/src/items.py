# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# src/items.py
import scrapy

class WebpageItem(scrapy.Item):

    def __repr__(self):
        """Control how the item is represented in debug output"""
        # Create a copy of the item
        data = dict(self)
        # Replace raw_html with a placeholder
        if 'raw_html' in data:
            data['raw_html'] = '[HTML content hidden]'
        # Replace long headers with placeholder too if needed
        if 'headers' in data and len(str(data['headers'])) > 100:
            data['headers'] = '[Headers content hidden]'
        return f"{self.__class__.__name__}({data})"


    url = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()  
    lang = scrapy.Field()         
    last_modified = scrapy.Field()
    etag = scrapy.Field()
    raw_html = scrapy.Field()
    headers = scrapy.Field()      
    status_code = scrapy.Field()
    crawled_at = scrapy.Field()

class RepoFileItem(scrapy.Item):
    file_content = scrapy.Field()
    file_url = scrapy.Field()
    repo_name = scrapy.Field()
    file_extension = scrapy.Field()
    file_path = scrapy.Field()
    url = scrapy.Field()  