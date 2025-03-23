# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# src/pipelines.py
import pymongo
from pymongo import MongoClient
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

MONGODB_DATABASE = 'test_db'
# MONGODB_COLLECTION = 'github'
MONGODB_COLLECTION = 'docs'

class MongoDBPipeline:
    collection_name = MONGODB_COLLECTION

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri='mongodb://localhost:27017/',
            mongo_db=MONGODB_DATABASE
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


class MongoDBRepoFilePipeline:
    collection_name = MONGODB_COLLECTION

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri='mongodb://localhost:27017/',
            mongo_db=MONGODB_DATABASE
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # Create a compound unique index on repo_name and file_path
        self.db[self.collection_name].create_index(
            [("repo_name", pymongo.ASCENDING), ("file_path", pymongo.ASCENDING)],
            unique=True
        )

    def close_spider(self, spider):
        self.client.close()

    def should_process_file(self, file_path, file_extension):
        # Skip common directories and files that should be excluded
        excluded_dirs = ['.git', '__pycache__', 'node_modules', '.venv', '.idea', '.vscode']
        excluded_extensions = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.obj', '.o']
        
        # Check if file is in an excluded directory
        for excluded_dir in excluded_dirs:
            if f'/{excluded_dir}/' in file_path or file_path.startswith(f'{excluded_dir}/'):
                return False
                
        # Check if file has an excluded extension
        if file_extension.lower() in excluded_extensions:
            return False
            
        return True

    def process_item(self, item, spider):
        # Only process RepoFileItem objects
        if 'file_path' not in item or 'repo_name' not in item:
            return item
            
        # Skip files that should be excluded
        if not self.should_process_file(item['file_path'], item.get('file_extension', '')):
            raise DropItem(f"Excluded file: {item['file_path']}")
            
        try:
            self.db[self.collection_name].update_one(
                {
                    "repo_name": item["repo_name"],
                    "file_path": item["file_path"]
                },
                {"$set": ItemAdapter(item).asdict()},
                upsert=True
            )
            spider.logger.info(f"Saved file to MongoDB: {item['repo_name']}/{item['file_path']}")
        except pymongo.errors.DuplicateKeyError:
            spider.logger.debug(f"Duplicate file: {item['repo_name']}/{item['file_path']}")
        except Exception as e:
            spider.logger.error(f"Error saving file to MongoDB: {e}")
            
        return item