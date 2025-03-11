import os
import logging
from typing import Dict, Any, List
from pymongo import MongoClient
from meilisearch import Client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "scraping_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "search")
mongo_client = MongoClient(MONGODB_URI)
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
            logging.warning(f"Unexpected response format from get_indexes(): {type(indexes_response)}")
            existing_indexes = []
            
        logging.info(f"Existing indexes: {existing_indexes}")
        
        # Check if our index already exists
        if MEILI_INDEX not in existing_indexes:
            logging.info(f"Creating index '{MEILI_INDEX}'...")
            response = meili_client.create_index(uid=MEILI_INDEX, options={"primaryKey": "id"})
            logging.info(f"Index '{MEILI_INDEX}' creation task started (Task UID: {response.task_uid}).")
        else:
            logging.info(f"Index '{MEILI_INDEX}' already exists.")
    except Exception as e:
        logging.error(f"Error creating index: {e}")

def extract_text_from_html(html: str) -> str:
    """
    Extracts visible text from raw HTML.

    Args:
        html (str): Raw HTML content.

    Returns:
        str: Extracted visible text.
    """
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_documents(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetches documents from MongoDB and extracts text from raw HTML.

    Returns:
        List of dictionaries with 'id' and 'text' fields.
    """
    logging.info("Fetching documents from MongoDB...")
    cursor = mongo_collection.find({}, {"_id": 1, "raw_html": 1}).limit(limit)

    documents = []
    for doc in cursor:
        raw_html = doc.get("raw_html", "")
        extracted_text = extract_text_from_html(raw_html)
        documents.append({
            "id": str(doc["_id"]),
            "text": extracted_text
        })

    logging.info(f"Fetched and processed {len(documents)} documents.")
    return documents

def index_documents(documents: List[Dict[str, Any]], batch_size: int = 500) -> None:
    """Indexes the provided documents into Meilisearch in smaller batches."""
    if not documents:
        logging.warning("No documents to index.")
        return

    logging.info(f"Indexing {len(documents)} documents in batches of {batch_size}...")
    try:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            response = meili_client.index(MEILI_INDEX).add_documents(batch)
            logging.info(f"Indexed batch {i // batch_size + 1} (Task UID: {response.task_uid})")
    except Exception as e:
        logging.error(f"Error indexing documents: {e}")

def setup_searchable_fields(fields: List[str]) -> None:
    """Configures searchable attributes in Meilisearch."""
    try:
        logging.info(f"Setting searchable fields: {fields}")
        response = meili_client.index(MEILI_INDEX).update_searchable_attributes(fields)
        logging.info(f"Searchable fields updated (Task UID: {response.task_uid})")
    except Exception as e:
        logging.error(f"Error setting searchable fields: {e}")

if __name__ == "__main__":
    logging.info("Starting Meilisearch indexing process...")

    create_index()
    docs = fetch_documents()
    index_documents(docs)
    setup_searchable_fields(["text"])

    logging.info("Meilisearch setup completed successfully.")