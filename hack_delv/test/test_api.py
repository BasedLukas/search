import requests
from typing import Any, Dict
from dotenv import load_dotenv
import os
import json

load_dotenv()

API_ENDPOINT = os.getenv("DELV_API_ENDPOINT", "")
MY_API_KEY = os.getenv("MY_API_KEY")


def fetch_data(payload: Dict[str, str]) -> requests.Response:
    """
    Sends a POST request to the specified API endpoint with the given payload inside a "body" key.

    Args:
        payload (Dict[str, str]): The data containing either "query" or "url" inside the request body.

    Returns:
        requests.Response: The HTTP response from the API.
    """
    if not API_ENDPOINT:
        raise ValueError("Set DELV_API_ENDPOINT to your deployed API")
    headers: Dict[str, str] = {
        "x-api-key": MY_API_KEY,
        "Content-Type": "application/json"
    }
    data: Dict[str, Any] = {
        "body": json.dumps(payload)  # The API expects the "body" key to contain a JSON string
    }

    response: requests.Response = requests.post(API_ENDPOINT, json=data, headers=headers, timeout=15)
    return response


if __name__ == "__main__":
    # First call: using "query"
    query_term: str = "Converting a sympy polynomial into a list of coefficients"
    response_query: requests.Response = fetch_data({"query": query_term})

    print("Query Request:")
    print("Status Code:", response_query.status_code)
    print("Response Data:", response_query.text)
    print("-" * 50)

    # Second call: using "url"
    valid_url: str = "https://example.com/"
    response_url: requests.Response = fetch_data({"url": valid_url})

    print("URL Request:")
    print("Status Code:", response_url.status_code)
    print("Response Data:", response_url.text)