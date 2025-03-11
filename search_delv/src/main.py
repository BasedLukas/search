import os
import logging
import time
from typing import Dict, Any, List, Generator
from pymongo import MongoClient
from meilisearch import Client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "scraping_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "webpages")
mongo_client = MongoClient(MONGODB_URI, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False, maxPoolSize=50)
mongo_db = mongo_client[MONGODB_DB]
mongo_collection = mongo_db[MONGODB_COLLECTION]

# Meilisearch settings
MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "")
MEILI_INDEX = os.getenv("MEILI_INDEX", "snowflake")
meili_client = Client(MEILI_URL, MEILI_API_KEY)

def create_index() -> None:
    """Ensure the Meilisearch index exists before adding documents."""
    try:
        # Get existing indexes
        indexes_response = meili_client.get_indexes()
        
        # Handle the dictionary response format
        if isinstance(indexes_response, dict) and "results" in indexes_response:
            existing_indexes = [idx.get("uid") for idx in indexes_response["results"]]
        else:
            logger.warning(f"Unexpected response format from get_indexes(): {type(indexes_response)}")
            existing_indexes = []
            
        logger.info(f"Existing indexes: {existing_indexes}")
        
        # Check if our index already exists
        if MEILI_INDEX not in existing_indexes:
            logger.info(f"Creating index '{MEILI_INDEX}'...")
            response = meili_client.create_index(uid=MEILI_INDEX, options={"primaryKey": "id"})
            logger.info(f"Index '{MEILI_INDEX}' creation task started (Task UID: {response.task_uid}).")
        else:
            logger.info(f"Index '{MEILI_INDEX}' already exists.")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise

def extract_text_from_html(html: str) -> str:
    """
    Extracts visible text from raw HTML.

    Args:
        html (str): Raw HTML content.

    Returns:
        str: Extracted visible text.
    """
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        logger.warning(f"Error extracting text from HTML: {e}")
        return ""

def fetch_documents_batch(batch_size: int = 500, skip: int = 0) -> List[Dict[str, Any]]:
    """
    Fetches a batch of documents from MongoDB and extracts text from raw HTML.

    Args:
        batch_size (int): Number of documents to fetch.
        skip (int): Number of documents to skip.

    Returns:
        List of dictionaries with 'id' and 'text' fields.
    """
    cursor = mongo_collection.find({}, {"_id": 1, "raw_html": 1}).skip(skip).limit(batch_size)

    documents = []
    for doc in cursor:
        raw_html = doc.get("raw_html", "")
        extracted_text = extract_text_from_html(raw_html)
        
        # Only add documents with actual content
        if extracted_text:
            documents.append({
                "id": str(doc["_id"]),
                "text": extracted_text
            })

    return documents

def count_documents() -> int:
    """Count the total number of documents to be processed."""
    try:
        return mongo_collection.count_documents({})
    except Exception as e:
        logger.error(f"Error counting documents: {e}")
        return 0

def index_batch(batch: List[Dict[str, Any]]) -> bool:
    """
    Indexes a batch of documents into Meilisearch.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if not batch:
        return True
        
    try:
        response = meili_client.index(MEILI_INDEX).add_documents(batch)
        logger.debug(f"Indexed batch (Task UID: {response.task_uid})")
        return True
    except Exception as e:
        logger.error(f"Error indexing batch: {e}")
        return False

def setup_searchable_fields(fields: List[str]) -> None:
    """Configures searchable attributes in Meilisearch."""
    try:
        logger.info(f"Setting searchable fields: {fields}")
        response = meili_client.index(MEILI_INDEX).update_searchable_attributes(fields)
        logger.info(f"Searchable fields updated (Task UID: {response.task_uid})")
    except Exception as e:
        logger.error(f"Error setting searchable fields: {e}")

def process_all_documents(batch_size: int = 500, max_retries: int = 3) -> None:
    """
    Process all documents in the MongoDB collection in batches.
    
    Args:
        batch_size (int): Size of batches to process
        max_retries (int): Maximum number of retries for failed batches
    """
    total_docs = count_documents()
    if total_docs == 0:
        logger.warning("No documents found in MongoDB collection.")
        return

    logger.info(f"Starting to process {total_docs} documents in batches of {batch_size}...")
    
    processed = 0
    retries = {}  # track retry attempts per batch start position
    
    while processed < total_docs:
        # Check if we've exceeded retry limit for this position
        if retries.get(processed, 0) >= max_retries:
            logger.error(f"Skipping batch at position {processed} after {max_retries} failed attempts")
            processed += batch_size
            continue
        
        try:
            logger.info(f"Fetching batch {processed//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} (docs {processed}-{min(processed + batch_size, total_docs)})")
            batch = fetch_documents_batch(batch_size, processed)
            
            if batch:
                success = index_batch(batch)
                if success:
                    processed += len(batch)
                    # Clear retry counter on success
                    retries.pop(processed - len(batch), None)
                    logger.info(f"Progress: {processed}/{total_docs} documents processed ({(processed/total_docs)*100:.2f}%)")
                else:
                    # Increment retry counter
                    retries[processed] = retries.get(processed, 0) + 1
                    logger.warning(f"Retrying batch at position {processed} (attempt {retries[processed]})")
                    time.sleep(2)  # Add delay before retry
            else:
                # No documents returned but no error - just move on
                processed += batch_size
                logger.info(f"No valid documents found in batch starting at {processed}, moving to next batch")
        
        except Exception as e:
            logger.error(f"Error processing batch at position {processed}: {e}")
            retries[processed] = retries.get(processed, 0) + 1
            if retries[processed] < max_retries:
                logger.info(f"Will retry batch at position {processed} (attempt {retries[processed]})")
                time.sleep(5)  # Longer delay for exceptions
            else:
                logger.error(f"Skipping batch at position {processed} after {max_retries} failed attempts")
                processed += batch_size

if __name__ == "__main__":
    logger.info("Starting Meilisearch indexing process...")
    
    try:
        # Ensure the index exists
        create_index()
        
        # Process all documents with appropriate batch size
        # Adjust batch_size based on your document size and available memory
        process_all_documents(batch_size=1000)
        
        # Configure searchable fields
        setup_searchable_fields(["text"])
        
        logger.info("Meilisearch setup completed successfully.")
    except Exception as e:
        logger.error(f"Fatal error in indexing process: {e}")