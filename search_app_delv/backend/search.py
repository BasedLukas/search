#!/usr/bin/env python3
"""
Search engine that loads a FAISS index, a URL mapping, and a SentenceTransformer model.
Search encodes queries, performs a nearest-neighbor lookup, retrieves corresponding HTML (from S3 or local),
extracts text (for the snippet), and attempts to extract the title.

Each result is returned as a `Result` object with title, URL, snippet, text, and distance.
"""
import time
import json
import faiss
import boto3
import io
import dotenv
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
from dataclasses import dataclass
from bs4 import BeautifulSoup
from backend.logs import logger as log

# ---------------- CONFIGURATION ----------------
env = dotenv.dotenv_values()
USE_LOCAL = True  # Set to True to use local files (with download if needed)

# S3 configuration
S3_BUCKET = os.getenv("DELV_S3_BUCKET", env.get("DELV_S3_BUCKET", ""))
HTML_BASE_PREFIX = "docs/"  # Folder inside the bucket where HTML files are stored

# Local file paths
LOCAL_INDEX_FILE = "backend/index.bin"
LOCAL_URL_MAPPING_FILE = "backend/url_mapping.json"
HTML_BASE_PATH = os.getenv("DELV_HTML_BASE_PATH", env.get("DELV_HTML_BASE_PATH", ""))

# S3 paths
S3_INDEX_FILE = f"s3://{S3_BUCKET}/index.bin"
S3_URL_MAPPING_FILE = f"s3://{S3_BUCKET}/url_mapping.json"

# SentenceTransformer model settings
MODEL_ID = "BAAI/bge-base-en-v1.5"  # Model for text embeddings
DEVICE = "cpu"  # Change to 'cuda' if running on GPU

# FAISS index settings
FAISS_VECTOR_DIM = 768  # Dimensionality of the embeddings
TOP_K_RESULTS = 10  # Number of top results to return
# ----------------------------------------------


@dataclass
class Result:
    title: str
    url: str
    snippet: str
    text: str
    html: str
    distance: float
    source: str = ""

@dataclass
class Stats:
    embedding_time: float
    query_time: float
    retrieval_time: float
    n_urls_searched: int


def download_from_s3(s3_path: str, local_path: str) -> bool:
    """Download a file from S3 to a local path. Returns True if successful."""
    try:
        s3 = boto3.client("s3")
        bucket, key = s3_path[5:].split("/", 1)
        log.info(f"Downloading {s3_path} to {local_path}")
        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(Bucket=bucket, Key=key, Filename=local_path)
        log.info(f"Successfully downloaded {s3_path} to {local_path}")
        return True
    except Exception as e:
        log.error(f"Failed to download {s3_path}: {e}")
        return False


def load_json_from_file(path: str) -> Dict[str, str]:
    """Load a JSON file from a local path or S3."""
    if USE_LOCAL and path.startswith("s3://"):
        # Use local file with download if needed
        if not os.path.exists(LOCAL_URL_MAPPING_FILE):
            log.info(f"URL mapping not found locally, downloading from {path}")
            download_from_s3(path, LOCAL_URL_MAPPING_FILE)
        
        log.info(f"Loading URL mapping from local file: {LOCAL_URL_MAPPING_FILE}")
        with open(LOCAL_URL_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    elif path.startswith("s3://"):
        # Direct S3 access
        s3 = boto3.client("s3")
        bucket, key = path[5:].split("/", 1)
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read().decode("utf-8")
        return json.loads(content)
    else:
        # Local file
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def load_faiss_index(path: str) -> faiss.Index:
    """Load a FAISS index from a local file or from S3."""
    if USE_LOCAL and path.startswith("s3://"):
        # Use local file with download if needed
        if not os.path.exists(LOCAL_INDEX_FILE):
            log.info(f"Index not found locally, downloading from {path}")
            download_from_s3(path, LOCAL_INDEX_FILE)
        
        log.info(f"Loading index from local file: {LOCAL_INDEX_FILE}")
        index = faiss.read_index(LOCAL_INDEX_FILE)
        return index
    elif path.startswith("s3://"):
        # Direct S3 access
        s3 = boto3.client("s3")
        bucket, key = path[5:].split("/", 1)
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj["Body"].read()
        data_arr = np.frombuffer(data, dtype=np.uint8)
        index = faiss.deserialize_index(data_arr)
        return index
    else:
        # Local file
        return faiss.read_index(path)


def get_html_text(file_path: str) -> str:
    """
    Retrieve an HTML file (from S3 or local), parse it with BeautifulSoup,
    and return its text content.
    """
    try:
        if file_path.startswith("s3://"):
            s3 = boto3.client("s3")
            bucket, key = file_path[5:].split("/", 1)
            obj = s3.get_object(Bucket=bucket, Key=key)
            html_content = obj["Body"].read().decode("utf-8")
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except:
        return "This document cannot be found on the server right now. ;-("


def fetch_results(distances, indices, url_mapping):
    results: List[Result] = []
    for i, idx in enumerate(indices[0]):
        if idx < 0:
            continue
        
        file_path = url_mapping.get(str(idx))
        if not file_path:
            continue
        # HTML content always from S3 regardless of USE_LOCAL setting
        s3_file_path = file_path.replace(HTML_BASE_PATH, "")
        s3_file_path = f"s3://{S3_BUCKET}/{HTML_BASE_PREFIX}{s3_file_path}"
        try:
            s3 = boto3.client("s3")
            bucket, key = s3_file_path[5:].split("/", 1)
            obj = s3.get_object(Bucket=bucket, Key=key)
            html_content = obj["Body"].read().decode("utf-8")
        except Exception as e:
            log.warning(f"Failed to retrieve {s3_file_path}: {e}")
            continue

        soup = BeautifulSoup(html_content, "html.parser")
        heading = soup.find("title") or soup.find("h1")
        title = heading.get_text(" ", strip=True) if heading else file_path
        fulltext = soup.get_text(separator=" ", strip=True)

        results.append(Result(
            title=title,
            url=s3_file_path,
            snippet=fulltext,
            text=fulltext[:250],
            html=html_content,
            distance=float(distances[0][i]),
            source=s3_file_path
        ))
    return results


def create_search_engine() -> Tuple[callable, Stats]:
    """
    Create and return a search function that loads:
    - FAISS index
    - URL mapping
    - SentenceTransformer model
    """
    if not S3_BUCKET:
        raise RuntimeError("Set DELV_S3_BUCKET to the bucket containing the index, URL mapping and HTML documents.")
    log.info("Loading faiss index...")
    faiss.omp_set_num_threads(1)
    index = load_faiss_index(S3_INDEX_FILE)
    log.info(f"Loaded FAISS index successfully.")
    
    log.info("Loading URL mapping...")
    url_mapping: Dict[str, str] = load_json_from_file(S3_URL_MAPPING_FILE)
    total_urls = len(url_mapping)
    log.info(f"Loaded URL mapping with {total_urls} entries.")
    
    log.info("Loading model....")
    model = SentenceTransformer(MODEL_ID, device=DEVICE)
    log.info(f"Loaded model '{MODEL_ID}' on device {DEVICE}.")

    def search(query: str, k: int = TOP_K_RESULTS) -> Tuple[List[Result], Stats]:
        """ Perform a search query and return top-k results. """
        start_time = time.perf_counter()

        prefix = "Represent this sentence for searching relevant passages: "
        query_vector = model.encode(
            prefix + query, 
            convert_to_tensor=False, 
            normalize_embeddings=True
            )[:FAISS_VECTOR_DIM]
        embedding_time = time.perf_counter()
        query_vector = query_vector.astype("float32").reshape(1, -1)
        distances, indices = index.search(query_vector, k)
        query_time = time.perf_counter()
        results = fetch_results(distances, indices, url_mapping)
        retrieval_time = time.perf_counter()
        stats = Stats(
            embedding_time=embedding_time-start_time,
            query_time=query_time-embedding_time,
            retrieval_time=retrieval_time-embedding_time, 
            n_urls_searched=total_urls)
        return results, stats

    return search

# Run search interactively if executed directly
if __name__ == "__main__":
    search_func = create_search_engine()

    while True:
        query = input("Enter a query (or 'exit' to quit): ")
        if query.lower() == "exit":
            break

        results, stats = search_func(query, k=TOP_K_RESULTS)
        print(f"\nQuery took {stats.query_time:.4f} seconds, searched {stats.n_urls_searched} URLs.\n")
        for res in results:
            print(f"Title: {res.title}")
            print(f"URL: {res.url}")
            print(f"Distance: {res.distance}")
            print(f"Snippet: {res.snippet}\n")
