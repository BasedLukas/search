import requests
import os
import dotenv
import json

dotenv.load_dotenv()
API_ENDPOINT = "https://example.invalid"

def get_delv(search_query: str = None, url: str = None) -> str:
    """
    Universal function to interact with the Delv API.
    Handles both search queries and URL content retrieval.
    
    Args:
        search_query: The search query to find relevant resources (optional)
        url: The URL to retrieve content from (optional)
        
    Returns:
        String containing either search results or URL content
    """
    headers = {
        "x-api-key": os.getenv("API_KEY"),
        "Content-Type": "application/json"
    }


    
    # Create request body instead of query parameters
    body = {}
    if search_query:
        body["query"] = search_query
    if url:
        body["url"] = url
    data = {
        "body": json.dumps(body)  # The API expects the "body" key to contain a JSON string
    }
    # Switch from GET with params to POST with JSON body
    response = requests.post(API_ENDPOINT, json=data, headers=headers)
    
    # Check for successful response
    if response.status_code != 200:
        error_msg = f"API request failed with status code {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_msg += f": {error_data['error']}"
        except:
            pass
        return error_msg
        
    return response.text