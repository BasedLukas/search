# src/pipelines.py
import pymongo
from pymongo import MongoClient
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import logging
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
import time
import atexit

MONGODB_DATABASE = 'snowflake'
# MONGODB_DATABASE = 'test'
MONGODB_COLLECTION_DOCS = 'docs'
MONGODB_COLLECTION_GITHUB = 'github'

# Create a singleton client to be shared across pipelines
class MongoDBSingleton:
    _instance = None
    _client = None
    
    @classmethod
    def get_client(cls, mongo_uri, mongo_options=None):
        if cls._client is None:
            options = mongo_options or {}
            cls._client = MongoClient(mongo_uri, **options)
            # Register shutdown function
            atexit.register(cls.close_client)
            logging.info(f"Created MongoDB client with options: {options}")
        return cls._client
    
    @classmethod
    def close_client(cls):
        if cls._client is not None:
            logging.info("Closing MongoDB connection on shutdown")
            cls._client.close()
            cls._client = None


class MongoDBPipeline:
    """
    Pipeline for storing scraped items in MongoDB.
    Uses connection pooling and robust error handling.
    """
    collection_name = MONGODB_COLLECTION_DOCS

    def __init__(self, mongo_uri, mongo_db, mongo_options=None):
        """
        Initialize pipeline with MongoDB connection parameters.
        
        Args:
            mongo_uri: MongoDB connection string
            mongo_db: Database name
            mongo_options: Connection pool and timeout settings
        """
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_options = mongo_options or {}
        self.items_processed = 0
        self.retry_delay = 1
        self.max_retries = 3
        self.batch_size = 100
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create pipeline from crawler settings.
        
        Args:
            crawler: Scrapy crawler
            
        Returns:
            MongoDBPipeline: Pipeline instance
        """
        # Connection pool settings optimized for high throughput
        mongo_options = {
            'maxPoolSize': 50,           # Allow up to 50 connections in the pool
            'minPoolSize': 10,           # Keep at least 10 connections open
            'maxIdleTimeMS': 30000,      # Close connections after 30 seconds of inactivity
            'socketTimeoutMS': 10000,    # Socket operation timeout
            'connectTimeoutMS': 5000,    # Initial connection timeout
            'serverSelectionTimeoutMS': 10000,  # Server selection timeout
            'waitQueueTimeoutMS': 10000, # How long to wait in queue for a connection
            'retryWrites': True,         # Retry write operations
            'w': 1,                      # Write acknowledgment level
            'journal': False,            # Don't wait for journal commit (faster)
        }
        
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_URI', 'mongodb://127.0.0.1:27017'),
            mongo_db=crawler.settings.get('MONGODB_DATABASE', MONGODB_DATABASE),
            mongo_options=mongo_options
        )

    def open_spider(self, spider):
        """
        Get MongoDB client from singleton when spider starts.
        Create unique index on URL field.
        
        Args:
            spider: Running spider
        """
        # Use the singleton client
        self.client = MongoDBSingleton.get_client(self.mongo_uri, self.mongo_options)
        self.db = self.client[self.mongo_db]
        
        # Create indexes if they don't exist
        try:
            self.db[self.collection_name].create_index("url", unique=True)
            spider.logger.info("Connected to the configured MongoDB collection")
        except Exception as e:
            spider.logger.error(f"Error creating MongoDB index: {e}")

    def close_spider(self, spider):
        """
        Log statistics when spider finishes.
        Client is closed by the singleton.
        
        Args:
            spider: Running spider
        """
        spider.logger.info(f"Processed {self.items_processed} items in MongoDB")

    def process_item(self, item, spider):
        """
        Store or update item in MongoDB with retry logic.
        
        Args:
            item: Scraped item
            spider: Running spider
            
        Returns:
            item: Processed item
        """
        for attempt in range(self.max_retries):
            try:
                # Do a lightweight update - only store fields we need
                document = ItemAdapter(item).asdict()
                
                # Don't store raw HTML if it's too large
                if 'raw_html' in document and len(document.get('raw_html', '')) > 1_000_000:
                    document['raw_html'] = document['raw_html'][:100000] + '... [truncated]'
                
                self.db[self.collection_name].update_one(
                    {"url": item["url"]},
                    {"$set": document},
                    upsert=True
                )
                
                # Increment counter and log progress periodically
                self.items_processed += 1
                if self.items_processed % self.batch_size == 0:
                    spider.logger.info(f"Saved {self.items_processed} documents to MongoDB")
                    
                return item
                
            except DuplicateKeyError:
                # This is normal, just log at debug level and return item
                if spider.settings.getbool('LOG_DUPLICATES', False):
                    spider.logger.debug(f"Duplicate URL skipped: {item['url']}")
                return item
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    spider.logger.warning(f"MongoDB connection error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    spider.logger.error(f"Failed to connect to MongoDB after {self.max_retries} attempts")
                    # Don't raise so the spider can continue - we'll try again with next item
                    return item
                    
            except Exception as e:
                spider.logger.error(f"Error saving to MongoDB: {e}")
                # Return item anyway so the spider can continue
                return item
        
        return item


class MongoDBRepoFilePipeline:
    """
    Pipeline for storing GitHub repository files in MongoDB.
    Uses connection pooling and robust error handling.
    """
    collection_name = MONGODB_COLLECTION_GITHUB

    def __init__(self, mongo_uri, mongo_db, mongo_options=None):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_options = mongo_options or {}
        self.items_processed = 0
        self.batch_size = 100
        self.retry_delay = 1
        self.max_retries = 3

    @classmethod
    def from_crawler(cls, crawler):
        # Use the same connection pool settings as the main pipeline
        mongo_options = {
            'maxPoolSize': 50,
            'minPoolSize': 10, 
            'maxIdleTimeMS': 30000,
            'socketTimeoutMS': 10000,
            'connectTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 10000,
            'waitQueueTimeoutMS': 10000,
            'retryWrites': True,
            'w': 1,
            'journal': False
        }
        
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_URI', 'mongodb://127.0.0.1:27017'),
            mongo_db=crawler.settings.get('MONGODB_DATABASE', MONGODB_DATABASE),
            mongo_options=mongo_options
        )

    def open_spider(self, spider):
        # Use the singleton client instead of creating a new one
        self.client = MongoDBSingleton.get_client(self.mongo_uri, self.mongo_options)
        self.db = self.client[self.mongo_db]
        
        # Create compound index
        try:
            self.db[self.collection_name].create_index(
                [("repo_name", pymongo.ASCENDING), ("file_path", pymongo.ASCENDING)],
                unique=True
            )
            spider.logger.info(f"Connected to MongoDB GitHub collection")
        except Exception as e:
            spider.logger.error(f"Error creating MongoDB index: {e}")

    def close_spider(self, spider):
        spider.logger.info(f"Processed {self.items_processed} GitHub files in MongoDB")

    def should_process_file(self, file_path, file_extension):
        # Skip common directories and files that should be excluded
        excluded_dirs = ['.git', '__pycache__', 'node_modules', '.venv', '.idea', '.vscode']
        excluded_extensions = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.obj', '.o']
        
        # Check if file is in an excluded directory - more efficient path checking
        for excluded_dir in excluded_dirs:
            excluded_pattern = f'/{excluded_dir}/'
            if excluded_pattern in file_path or file_path.startswith(f'{excluded_dir}/'):
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
        
        # Try with retries
        for attempt in range(self.max_retries):
            try:
                # Get a lightweight version of the item
                document = ItemAdapter(item).asdict()
                
                # Don't store content if it's too large
                if 'file_content' in document and len(document.get('file_content', '')) > 1_000_000:
                    document['file_content'] = document['file_content'][:100000] + '... [truncated]'
                
                self.db[self.collection_name].update_one(
                    {
                        "repo_name": item["repo_name"],
                        "file_path": item["file_path"]
                    },
                    {"$set": document},
                    upsert=True
                )
                
                # Increment counter and log progress
                self.items_processed += 1
                if self.items_processed % self.batch_size == 0:
                    spider.logger.info(f"Saved {self.items_processed} GitHub files to MongoDB")
                
                return item
                
            except DuplicateKeyError:
                # This is normal, just return the item
                return item
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    spider.logger.warning(f"MongoDB connection error in GitHub pipeline: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    spider.logger.error(f"Failed to connect to MongoDB after {self.max_retries} attempts")
                    return item
                    
            except Exception as e:
                spider.logger.error(f"Error saving GitHub file to MongoDB: {e}")
                return item
                
        return item
