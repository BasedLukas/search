import requests
from typing import Any, Dict
from dotenv import load_dotenv
import os

load_dotenv()

MY_API_KEY = os.getenv("MY_API_KEY")


def fetch_data(search_term: str) -> requests.Response:
    """
    Sends a GET request to the specified API endpoint with the given search term.
    
    Args:
        search_term (str): The search term to include in the query parameter.
        
    Returns:
        requests.Response: The HTTP response from the API.
    """
    url: str = "https://example.invalid"
    params: Dict[str, str] = {"q": search_term}
    headers: Dict[str, str] = {"x-api-key": MY_API_KEY}
    
    response: requests.Response = requests.get(url, params=params, headers=headers)
    return response

if __name__ == "__main__":
    term: str = "Converting a sympy polynomial into a list of coefficients"
    response: requests.Response = fetch_data(term)
    
    print("Status Code:", response.status_code)
    print("Response Data:", response.text)