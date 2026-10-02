import os
import logging
import time
import json
import requests
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from meilisearch import Client
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from xml.sax.saxutils import escape


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "scraping_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "webpages")
mongo_client = MongoClient(MONGODB_URI, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False, maxPoolSize=50)
mongo_db = mongo_client[MONGODB_DB]
mongo_collection = mongo_db[MONGODB_COLLECTION]

# Meilisearch settings
MEILI_URL = os.getenv("MEILI_URL", "http://127.0.0.1:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "")
MEILI_INDEX = os.getenv("MEILI_INDEX", "demo")
meili_client = Client(MEILI_URL, MEILI_API_KEY)

# FastAPI app
app = FastAPI(title="Search Delv API", 
              description="A search service for documentation and other resources")
# Add this after creating the app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Pydantic models
class SearchQuery(BaseModel):
    search_query: str

class SearchResult(BaseModel):
    text: str

def create_index() -> None:
    """Ensure the Meilisearch index exists before adding documents."""
    try:
        # Check if our index already exists and create it if not
        try:
            # Try to get the index - if this succeeds, the index exists
            meili_client.index(MEILI_INDEX).get_settings()
            logger.info(f"Index '{MEILI_INDEX}' already exists.")
        except Exception:
            # If we get an error, the index probably doesn't exist
            logger.info(f"Creating index '{MEILI_INDEX}'...")
            meili_client.create_index(MEILI_INDEX, {'primaryKey': 'id'})
            logger.info(f"Index '{MEILI_INDEX}' created successfully.")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise

def valid_url(url: str) -> bool:
    """
    Validate if a URL has a proper format.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return result.scheme in {"http", "https"} and bool(result.netloc)
    except Exception:
        return False


def generate_xml_document(html: str, url: str) -> str:
    """
    Generate a simplified XML document from HTML content that preserves
    basic structure and converts links to absolute URLs.
    
    Args:
        html (str): Raw HTML content
        url (str): Original URL of the page
        
    Returns:
        str: Simplified XML document with text content and links
    """
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        
        # Extract description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()
        else:
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
        
        # Locate main content
        main_content = soup.find("main") or soup.find("article") or soup.body or soup
        
        if not main_content:
            return f"<document>\n  <title>{escape(title)}</title>\n  <description>{escape(description)}</description>\n  <content></content>\n</document>"
        
        # Remove unwanted tags
        for tag in main_content.find_all(["script", "style", "noscript", "iframe", "form", "input", "button"]):
            tag.decompose()
        
        # Extract links with their text and absolute URLs
        links = []
        for link in main_content.find_all("a", href=True):
            href = link.get("href", "")
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                link_text = link.get_text().strip()
                if link_text:  # Only include links with text
                    absolute_url = urljoin(url, href)
                    links.append((link_text, absolute_url))
        
        # Extract structured text content
        content_sections = []
        
        # Process headings and their following content
        headings = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        for heading in headings:
            heading_text = heading.get_text().strip()
            if heading_text:
                section_content = []
                
                # Get all elements until the next heading
                elem = heading.next_sibling
                while elem and not (elem.name and elem.name.startswith('h')):
                    if hasattr(elem, 'get_text'):
                        text = elem.get_text().strip()
                        if text:
                            section_content.append(text)
                    elif isinstance(elem, str) and elem.strip():
                        section_content.append(elem.strip())
                    elem = elem.next_sibling
                
                if section_content:
                    content_sections.append({
                        "type": heading.name,
                        "heading": heading_text,
                        "content": " ".join(section_content)
                    })
        
        # If no sections found, extract paragraph texts
        if not content_sections:
            paragraphs = main_content.find_all("p")
            for p in paragraphs:
                text = p.get_text().strip()
                if text:
                    content_sections.append({
                        "type": "p",
                        "content": text
                    })
        
        # If still no content, get all text
        if not content_sections:
            text = main_content.get_text().strip()
            if text:
                content_sections.append({
                    "type": "text",
                    "content": text
                })
        
        # Build the final XML structure
        result = f"<document>\n  <url>{escape(url)}</url>\n  <title>{escape(title)}</title>\n"
        if description:
            result += f"  <description>{escape(description)}</description>\n"
        
        # Add content
        result += "  <content>\n"
        for section in content_sections:
            if "heading" in section:
                result += f"    <section type=\"{section['type']}\">\n"
                result += f"      <heading>{escape(section['heading'])}</heading>\n"
                result += f"      <text>{escape(section['content'])}</text>\n"
                result += f"    </section>\n"
            else:
                result += f"    <{section['type']}>{escape(section['content'])}</{section['type']}>\n"
        result += "  </content>\n"
        
        # Add links
        if links:
            result += "  <links>\n"
            for link_text, link_url in links:
                result += f"    <link>\n      <text>{escape(link_text)}</text>\n      <url>{escape(link_url)}</url>\n    </link>\n"
            result += "  </links>\n"
        
        result += "</document>"
        
        return result
    except Exception as e:
        return f"<document>\n  <error>Error processing HTML: {escape(str(e))}</error>\n</document>"


def update_document_with_xml(doc_id, xml_content):
    """
    Update a MongoDB document with its XML representation.
    
    Args:
        doc_id: The MongoDB document ID
        xml_content (str): The XML content to store
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = mongo_collection.update_one(
            {"_id": doc_id},
            {"$set": {"xml": xml_content}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating document {doc_id} with XML: {e}")
        return False

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
    Fetches a batch of documents from MongoDB and processes them into structured XML documents.
    Also stores the XML content in MongoDB.

    Args:
        batch_size (int): Number of documents to fetch.
        skip (int): Number of documents to skip.

    Returns:
        List of dictionaries with 'id', 'url', and 'xml_content' fields.
    """
    cursor = mongo_collection.find({}, {"_id": 1, "raw_html": 1, "url": 1}).skip(skip).limit(batch_size)

    documents = []
    for doc in cursor:
        raw_html = doc.get("raw_html", "")
        url = doc.get("url", "")
        
        if not raw_html or not url:
            continue
            
        # Generate structured XML document
        xml_content = generate_xml_document(raw_html, url)
        
        # Only add documents with actual content
        if xml_content:
            # Store XML in MongoDB
            update_document_with_xml(doc["_id"], xml_content)
            
            documents.append({
                "id": str(doc["_id"]),
                "url": url,
                "xml_content": xml_content,
                # Include plain text for search capabilities
                "text": extract_text_from_html(raw_html)
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
        logger.info(f"Indexed batch of {len(batch)} documents")
        return True
    except Exception as e:
        logger.error(f"Error indexing batch: {e}")
        return False

def setup_searchable_fields(fields: List[str]) -> None:
    """Configures searchable attributes in Meilisearch."""
    try:
        logger.info(f"Setting searchable fields: {fields}")
        meili_client.index(MEILI_INDEX).update_settings({
            'searchableAttributes': fields
        })
        logger.info(f"Searchable fields updated")
    except Exception as e:
        logger.error(f"Error setting searchable fields: {e}")

def process_all_documents(batch_size: int = 500, max_retries: int = 3, limit: int = None) -> None:
    """
    Process all documents in the MongoDB collection in batches.
    
    Args:
        batch_size (int): Size of batches to process
        max_retries (int): Maximum number of retries for failed batches
        limit (int, optional): Maximum number of documents to process
    """
    total_docs = count_documents()
    if total_docs == 0:
        logger.warning("No documents found in MongoDB collection.")
        return

    # Apply limit if specified
    if limit is not None and limit < total_docs:
        total_docs = limit
        logger.info(f"Limiting processing to {limit} documents")
    
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
            # Calculate this batch size (might be smaller for the last batch)
            current_batch_size = min(batch_size, total_docs - processed)
            
            logger.info(f"Fetching batch {processed//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} (docs {processed}-{min(processed + current_batch_size, total_docs)})")
            batch = fetch_documents_batch(current_batch_size, processed)
            
            if batch:
                success = index_batch(batch)
                if success:
                    processed += current_batch_size
                    # Clear retry counter on success
                    retries.pop(processed - current_batch_size, None)
                    logger.info(f"Progress: {processed}/{total_docs} documents processed ({(processed/total_docs)*100:.2f}%)")
                else:
                    # Increment retry counter
                    retries[processed] = retries.get(processed, 0) + 1
                    logger.warning(f"Retrying batch at position {processed} (attempt {retries[processed]})")
                    time.sleep(2)  # Add delay before retry
            else:
                # No documents returned but no error - just move on
                processed += current_batch_size
                logger.info(f"No valid documents found in batch starting at {processed}, moving to next batch")

            # Check if we've hit the limit
            if limit is not None and processed >= limit:
                logger.info(f"Reached processing limit of {limit} documents")
                break
        
        except Exception as e:
            logger.error(f"Error processing batch at position {processed}: {e}")
            retries[processed] = retries.get(processed, 0) + 1
            if retries[processed] < max_retries:
                logger.info(f"Will retry batch at position {processed} (attempt {retries[processed]})")
                time.sleep(5)  # Longer delay for exceptions
            else:
                logger.error(f"Skipping batch at position {processed} after {max_retries} failed attempts")
                processed += min(batch_size, total_docs - processed)

@app.post("/search", response_model=SearchResult)
async def search(query: SearchQuery):
    """
    Search endpoint that searches the Meilisearch index.
    
    Args:
        query (SearchQuery): The search query
        
    Returns:
        SearchResult: The search result with text
    """
    try:
        search_results = meili_client.index(MEILI_INDEX).search(
            query.search_query,
            {
                "limit": 1,
                "attributesToRetrieve": ["id", "url", "xml_content"]
            }
        )
        
        if search_results["hits"]:
            # Get the top result
            top_result = search_results["hits"][0]
            
            # For demonstration, we'll return the structured XML content
            # In a real application, you might want to process this further
            return SearchResult(text=top_result.get("xml_content", "No content found"))
        else:
            return SearchResult(text="No results found for your query.")
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/process_document")
async def process_document(url: str):
    """
    Endpoint to manually process a document from a URL.
    This fetches the document, processes it, and adds it to the search index.
    
    Args:
        url (str): URL of the webpage to process
        
    Returns:
        dict: Status of the processing
    """
    if not valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    try:
        # Fetch the document
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Generate XML content
        xml_content = generate_xml_document(response.text, url)
        
        if not xml_content:
            raise HTTPException(status_code=500, detail="Failed to generate XML document")
        
        # Extract plain text for search
        plain_text = extract_text_from_html(response.text)
        
        # Generate a unique ID for this document
        doc_id = f"manual-{int(time.time())}"
        
        # Store in MongoDB
        mongo_doc = {
            "_id": doc_id,
            "url": url,
            "raw_html": response.text,
            "xml": xml_content,
            "crawled_at": time.time()
        }
        
        mongo_collection.insert_one(mongo_doc)
        
        # Add to Meilisearch
        document = {
            "id": doc_id,
            "url": url,
            "xml_content": xml_content,
            "text": plain_text
        }
        
        meili_client.index(MEILI_INDEX).add_documents([document])
        
        return {
            "status": "success",
            "message": f"Document processed and added to index",
            "url": url
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing document from URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/reindex")
async def reindex_all_documents(batch_size: int = 100, limit: int = None):
    """
    Endpoint to manually trigger reindexing of all documents in MongoDB.
    This processes documents in batches and adds them to the search index.
    
    Args:
        batch_size (int): Size of batches to process
        limit (int, optional): Maximum number of documents to process
        
    Returns:
        dict: Status of the reindexing process
    """
    try:
        # Start the reindexing process in a background task or thread
        # For simplicity in this example, we'll do it synchronously
        # In a production app, you'd want to make this asynchronous
        
        total_docs = count_documents()
        if total_docs == 0:
            return {"status": "warning", "message": "No documents found in MongoDB collection."}

        # Apply limit if specified
        if limit is not None and limit < total_docs:
            total_docs = limit
            logger.info(f"Limiting reindexing to {limit} documents")

        # First, clean the existing index
        try:
            meili_client.index(MEILI_INDEX).delete_all_documents()
            logger.info("Cleared existing index documents")
        except Exception as e:
            logger.warning(f"Error clearing index: {e}")
            # Continue anyway - we'll just add new documents

        # Process documents
        processed = 0
        successful = 0
        
        for skip in range(0, total_docs, batch_size):
            # Calculate this batch size (might be smaller for the last batch)
            current_batch_size = min(batch_size, total_docs - skip)
            
            batch = fetch_documents_batch(current_batch_size, skip)
            
            if batch:
                success = index_batch(batch)
                if success:
                    successful += len(batch)
                    logger.info(f"Progress: {skip+len(batch)}/{total_docs} documents processed")
            
            processed += current_batch_size
            if processed >= total_docs:
                break
        
        return {
            "status": "success",
            "message": f"Reindexing completed: {successful}/{total_docs} documents successfully processed",
            "total_documents": total_docs,
            "successful": successful
        }
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Reindexing error: {str(e)}")

# Command line function to process a MongoDB entry and save it to disk for inspection
def process_mongo_doc_to_file(doc_id: str, output_file: str) -> None:
    """
    Process a specific MongoDB document by ID and save the XML output to a file.
    Useful for debugging and validation.
    
    Args:
        doc_id (str): MongoDB document ID
        output_file (str): Path to save the output XML
    """
    try:
        # Convert string ID to ObjectId if it's in the proper format
        from bson.objectid import ObjectId
        
        try:
            if len(doc_id) == 24:  # ObjectId is 24 hex chars
                obj_id = ObjectId(doc_id)
            else:
                obj_id = doc_id
        except Exception:
            obj_id = doc_id
            
        doc = mongo_collection.find_one({"_id": obj_id})
        
        if not doc:
            logger.error(f"Document with ID {doc_id} not found")
            return
            
        raw_html = doc.get("raw_html", "")
        url = doc.get("url", "")
        
        if not raw_html or not url:
            logger.error(f"Document with ID {doc_id} has no HTML or URL")
            return
            
        # Generate structured XML document
        xml_content = generate_xml_document(raw_html, url)
        
        if not xml_content:
            logger.error(f"Failed to generate XML document for ID {doc_id}")
            return
        
        # Update MongoDB with XML content
        update_document_with_xml(obj_id, xml_content)
        logger.info(f"Document {doc_id} updated with XML content in MongoDB")
            
        # Save to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xml_content)
            
        logger.info(f"Successfully processed document {doc_id} and saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        raise

if __name__ == "__main__":
    import argparse
    import uvicorn
    
    # Create command line argument parser
    parser = argparse.ArgumentParser(description="Search Delv API Server")
    parser.add_argument("--process-doc", type=str, help="Process a MongoDB document by ID and save XML")
    parser.add_argument("--output", type=str, default="output.xml", help="Output file for processed document")
    parser.add_argument("--reindex", action="store_true", help="Reindex all MongoDB documents to Meilisearch")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for reindexing (default: 100)")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of documents to process")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--no-server", action="store_true", help="Don't start the API server after processing")
    
    args = parser.parse_args()
    
    try:
        # Ensure the index exists
        create_index()
        
        # Configure searchable fields - include xml_content for structured search
        setup_searchable_fields(["text", "xml_content"])
        
        # Special processing modes
        if args.process_doc:
            logger.info(f"Processing MongoDB document {args.process_doc} to {args.output}")
            process_mongo_doc_to_file(args.process_doc, args.output)
            exit(0)
            
        if args.reindex:
            logger.info(f"Reindexing MongoDB documents with batch size {args.batch_size} and limit {args.limit or 'none'}")
            process_all_documents(batch_size=args.batch_size, limit=args.limit)
            logger.info("Reindexing completed")
            if args.no_server:
                exit(0)
        
        # If no specific command was given, reindex a small set and start the server
        if not args.process_doc and not args.reindex:
            # Default behavior: reindex a small sample (10 docs) and start the server
            default_limit = 50
            logger.info(f"No specific command given. Reindexing {default_limit} documents as a sample...")
            # process_all_documents(batch_size=args.batch_size, limit=default_limit)
            logger.info("Sample reindexing completed")
        
        # Normal API server mode (unless --no-server was specified)
        if not args.no_server:
            logger.info(f"Starting Search Delv API server on port {args.port}...")
            uvicorn.run(app, host="0.0.0.0", port=args.port)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
