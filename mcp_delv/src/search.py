import requests
import os
import dotenv

dotenv.load_dotenv()

API_ENDPOINT = "https://example.invalid"

def search_delv(search_query: str) -> str:
    """
    Search for coding docs, bug reports, issues, API references, get started guides, etc.
    Use this when interacting with any external library, or when you need to find information
    about a specific function, class, or concept.
    """
    headers = {
        "x-api-key": os.getenv("API_KEY")
    }
    response = requests.get(API_ENDPOINT, params={"q": search_query}, headers=headers)
    return response.text


