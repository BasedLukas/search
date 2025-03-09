import requests
import json
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv
import os

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")

def fetch_data_post(search_query: Optional[str] = None, url: Optional[str] = None) -> requests.Response:
    """
    Sends a POST request to the API endpoint with either a search query or URL.
    
    Args:
        search_query (str, optional): The search term to include in the request body.
        url (str, optional): The URL to include in the request body.
        
    Returns:
        requests.Response: The HTTP response from the API.
    """
    if not MY_API_KEY:
        raise ValueError("MY_API_KEY is not set")
    
    api_endpoint = "https://example.invalid"
    headers = {
        "x-api-key": MY_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Create request body with either query or url parameter
    body = {}
    if search_query:
        body["query"] = search_query
    if url:
        body["url"] = url
    
    response = requests.post(api_endpoint, headers=headers, json=body)
    return response

def test_search_query(query: str) -> None:
    """Test the API with a search query."""
    print(f"\n--- Testing with search query: '{query}' ---")
    response = fetch_data_post(search_query=query)
    
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response Data: {json.dumps(response.json(), indent=2)[:500]}...")
    except:
        print(f"Response Text: {response.text[:500]}...")

def test_url_endpoint(url: str) -> None:
    """Test the API with a URL."""
    print(f"\n--- Testing with URL: '{url}' ---")
    response = fetch_data_post(url=url)
    
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response Data: {json.dumps(response.json(), indent=2)[:500]}...")
    except:
        print(f"Response Text: {response.text[:500]}...")

if __name__ == "__main__":
    # Test with a search query
    search_term = "Converting a sympy polynomial into a list of coefficients"
    test_search_query(search_term)
    
    # Test with a URL
    test_url = "https://example.invalid"
    test_url_endpoint(test_url)