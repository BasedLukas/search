# src/pipelines.py
import pymongo
from pymongo import MongoClient
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

MONGODB_DATABASE = 'snowflake'
MONGODB_COLLECTION_DOCS = 'docs'
MONGODB_COLLECTION_GITHUB = 'github'

class MongoDBPipeline:
    """
    Pipeline for storing scraped items in MongoDB.
    Creates a unique index on URL to prevent duplicates.
    """
    collection_name = MONGODB_COLLECTION_DOCS

    def __init__(self, mongo_uri, mongo_db):
        """
        Initialize pipeline with MongoDB connection parameters.
        
        Args:
            mongo_uri: MongoDB connection string
            mongo_db: Database name
        """
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create pipeline from crawler settings.
        
        Args:
            crawler: Scrapy crawler
            
        Returns:
            MongoDBPipeline: Pipeline instance
        """
        return cls(
            mongo_uri='mongodb://localhost:27017/',
            mongo_db=MONGODB_DATABASE
        )

    def open_spider(self, spider):
        """
        Connect to MongoDB when spider starts.
        Create unique index on URL field.
        
        Args:
            spider: Running spider
        """
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # Create a unique index on url to prevent duplicates
        self.db[self.collection_name].create_index("url", unique=True)
        spider.logger.info(f"Connected to MongoDB: {self.mongo_uri}")

    def close_spider(self, spider):
        """
        Close MongoDB connection when spider finishes.
        
        Args:
            spider: Running spider
        """
        self.client.close()
        spider.logger.info("Closed MongoDB connection")

    def process_item(self, item, spider):
        """
        Store or update item in MongoDB.
        
        Args:
            item: Scraped item
            spider: Running spider
            
        Returns:
            item: Processed item
        """
        try:
            self.db[self.collection_name].update_one(
                {"url": item["url"]},
                {"$set": ItemAdapter(item).asdict()},
                upsert=True
            )
            spider.logger.debug(f"Saved page to MongoDB: {item['url']}")
        except pymongo.errors.DuplicateKeyError as e:
            spider.logger.debug(f"Duplicate URL rejected: {item['url']}, details: {str(e)}")
            # print the name and id of the existing document
            existing_doc = self.db[self.collection_name].find_one({"url": item["url"]})
            spider.logger.debug(f"Existing document: {existing_doc}")
        except Exception as e:
            spider.logger.error(f"Error saving to MongoDB: {e}")
        
        return item


class MongoDBRepoFilePipeline:
    collection_name = MONGODB_COLLECTION_GITHUB

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