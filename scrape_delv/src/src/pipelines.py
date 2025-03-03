# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# src/pipelines.py
import pymongo
from pymongo import MongoClient
from itemadapter import ItemAdapter

class MongoDBPipeline:
    collection_name = 'pages'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri='mongodb://localhost:27017/',
            mongo_db='toscrape_db'
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # Create a unique index on url to prevent duplicates
        self.db[self.collection_name].create_index("url", unique=True)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            self.db[self.collection_name].update_one(
                {"url": item["url"]},
                {"$set": ItemAdapter(item).asdict()},
                upsert=True
            )
        except pymongo.errors.DuplicateKeyError:
            spider.logger.debug(f"Duplicate URL: {item['url']}")
        except Exception as e:
            spider.logger.error(f"Error saving to MongoDB: {e}")
        return item