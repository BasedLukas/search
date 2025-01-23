import requests
import dotenv
import logging
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from custom_search_client import CustomSearchClient
from azure.core.credentials import AzureKeyCredential

from backend.search import create_search_engine

# Logging setup
log = logging.getLogger("search")
log.setLevel(logging.INFO)

# Load environment variables
env = dotenv.dotenv_values()
N_RESULTS = int(env.get("N_RESULTS", 5))

@dataclass
class Result:
    title: str
    url: str
    snippet: str = ""
    text: str = ""

@dataclass
class Stats:
    query_time: float  # Time taken for the query in seconds
    n_urls_searched: int  # Number of URLs searched

# Initialize the search engine
log.info("Loading search engine vectors...")
search_engine = create_search_engine()
URL_MAPPING_FILE = "backend/url_mapping.json"
try:
    with open(URL_MAPPING_FILE, "r") as f:
        url_mapping = json.load(f)
    N_URLS = len(url_mapping)
    logging.info(f"Loaded {N_URLS} URLs from {URL_MAPPING_FILE}.")
except FileNotFoundError:
    logging.error(f"URL mapping file not found at {URL_MAPPING_FILE}.")
    N_URLS = 0
log.info("Loaded search engine vectors:")



def get_my_results(query: str) -> List[Result]:
    """
    Perform a search and return a list of Result objects.
    """
    start_time = time.time()  # Start timer
    results = search_engine(query)  # Perform the query
    query_time = time.time() - start_time  # Calculate query time

    # Log stats
    log.info(f"Query completed in {query_time:.4f} seconds. Searched {N_URLS} URLs.")

    # Convert results to a list of Result objects
    return [
        Result(
            title=result[0],  # Assuming the title is in result[0]
            url=result[0],    # Assuming the URL is in result[0]
            snippet="Snippet goes here",  # Placeholder snippet
        )
        for result in results
    ], Stats(query_time=query_time, n_urls_searched=N_URLS)


def search(query: str) -> Dict[str, Any]:
    """
    Perform a search and return my results and stats.
    """
    my_results, stats = get_my_results(query)

    return {
        "results": my_results,
        "stats": stats
    }


# def get_bing(query:str):
#     ENDPOINT = "https://api.bing.microsoft.com/v7.0/custom/search"
#     SUBSCRIPTION_KEY = env.get("SUBSCRIPTION_KEY")
#     CUSTOM_CONFIG = env.get("CUSTOM_CONFIG")
#     client = CustomSearchClient(
#         endpoint=ENDPOINT, 
#         credential=AzureKeyCredential(SUBSCRIPTION_KEY)
#     )
#     result = client.custom_instance.search(
#         query=query, 
#         custom_config=CUSTOM_CONFIG,
#         count=N_RESULTS
#     )
    
#     if not result or not result.web_pages or not result.web_pages.value:
#         return []
#     return [
#         Result(
#                 title=page.name,
#                 url=page.url,
#                 snippet=page.snippet,
#             )
#         for page in result.web_pages.value
#     ]