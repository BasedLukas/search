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
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
from dataclasses import dataclass
from bs4 import BeautifulSoup
from backend.logs import logger as log

# ---------------- CONFIGURATION ----------------
env = dotenv.dotenv_values()
DEV = env.get("DEV") == "True"

if DEV:
    log.warning("ON DEV MODE")
    HTML_BASE_PREFIX = None
    INDEX_FILE = "backend/index.bin"
    URL_MAPPING_FILE = "backend/url_mapping.json"
    HTML_BASE_PATH = "/path/to/project"
else:
    log.warning("ON PROD MODE")
    HTML_BASE_PREFIX = "docs/"  # Folder inside the bucket where HTML files are stored
    S3_BUCKET = "example-resource"
    INDEX_FILE = f"s3://{S3_BUCKET}/index.bin"
    URL_MAPPING_FILE = f"s3://{S3_BUCKET}/url_mapping.json"
    HTML_BASE_PATH = "/path/to/project"


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
    html:str
    distance: float

@dataclass
class Stats:
    embedding_time: float
    query_time: float
    retrieval_time: float
    n_urls_searched: int


def load_json_from_file(path: str) -> Dict[str, str]:
    """ Load a JSON file from a local path or S3. """
    if path.startswith("s3://"):
        s3 = boto3.client("s3")
        bucket, key = path[5:].split("/", 1)
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read().decode("utf-8")
        return json.loads(content)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def load_faiss_index(path: str) -> faiss.Index:
    """Load a FAISS index from a local file or from S3."""
    if path.startswith("s3://"):
        s3 = boto3.client("s3")
        bucket, key = path[5:].split("/", 1)
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj["Body"].read()
        # Convert the raw bytes into a numpy array of uint8
        data_arr = np.frombuffer(data, dtype=np.uint8)
        index = faiss.deserialize_index(data_arr)
        return index
    else:
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
        
        file_path = url_mapping.get(str(idx), "Unknown URL")
        if not DEV:
            file_path = file_path.replace(HTML_BASE_PATH, "")
            file_path = f"s3://{S3_BUCKET}/{HTML_BASE_PREFIX}{file_path}"
        fulltext = get_html_text(file_path)

        try:
            if file_path.startswith("s3://"):
                s3 = boto3.client("s3")
                bucket, key = file_path[5:].split("/", 1)
                obj = s3.get_object(Bucket=bucket, Key=key)
                html_content = obj["Body"].read().decode("utf-8")
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
        except Exception as e:
            log.warning(f"Failed to extract title from {file_path}: {e}")

        results.append(Result(
            title="",
            url=file_path,
            snippet=fulltext,
            text=fulltext[:250],
            html=html_content,
            distance=float(distances[0][i])
        ))
    return results


def create_search_engine() -> Tuple[callable, Stats]:
    """
    Create and return a search function that loads:
    - FAISS index
    - URL mapping
    - SentenceTransformer model
    """

    log.info("Loading faiss index...")
    index = load_faiss_index(INDEX_FILE)
    log.info(f"Loaded FAISS index from {INDEX_FILE}.")
    log.info("Loading URL mapping...")
    url_mapping: Dict[str, str] = load_json_from_file(URL_MAPPING_FILE)
    total_urls = len(url_mapping)
    log.info(f"Loaded URL mapping from {URL_MAPPING_FILE} with {total_urls} entries.")
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
