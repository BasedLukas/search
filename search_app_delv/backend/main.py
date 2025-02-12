# File: main.py
import dotenv
import time
from typing import List, Dict, Any
from dataclasses import dataclass

# Import the search engine and the dataclasses from search.py.
from backend.logs import logger as log
from backend.search import create_search_engine, Result, Stats




# Load environment variables
env = dotenv.dotenv_values()
N_RESULTS = int(env.get("N_RESULTS", 5))

# Initialize the search engine. All file I/O is done in search.py.
log.info("Loading search engine vectors...")
search_engine = create_search_engine()
log.info("Loaded search engine vectors.")

def search(query: str) ->Dict[Result,Stats]:
    """
    Perform a search and return a list of Result objects along with stats.
    """
    start_time = time.time()  # Start timer
    # search_engine now returns (results, stats)
    results, stats = search_engine(query, k=N_RESULTS)
    query_time = time.time() - start_time  # Calculate query time

    log.info(f"Query completed in {query_time:.4f} seconds. Searched {stats.n_urls_searched} URLs.")

    # Update the stats with the measured query time.
    stats.query_time = query_time
    return {
        "results": results,
        "stats": stats
    }