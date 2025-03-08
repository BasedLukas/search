import requests
import os
import json
from src.post_process import post_process
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

def valid_query(query: str)->bool:
    """test that query exists and is max 400 chars and 50 words"""
    if not query:
        return False
    if len(query) > 400:
        return False
    if len(query.split()) > 50:
        return False
    return True


def process_results(query: str)->str:
    """get user query, query brave and post process the result to return a paragraph of text"""
    if not BRAVE_API_KEY:
        return "Backend error; please tell us that out env variable is not set"
    if not valid_query(query):
        return "Invalid query; query must be less than 400 chars and 50 words"

    # Make request to Brave Search API
    brave_api_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    result_filter = 'web'
    goggles = 'https://example.invalid'
    params = {
        'q': query,
        'count': 1,
        'offset': 0,
        'text_decorations': False,
        'spellcheck': False,
        'result_filter': result_filter,
        'goggles': goggles,
        'extra_snippets': False,
        'summary': False,
    }
    
    response = requests.get(
        brave_api_url,
        params=params,
        headers=headers,
        timeout=5
    )
    if response.status_code == 200:
        url = response.json()['web']['results'][0]['url']
        data = post_process(url)
        return data
    else:
        return f"Error: please tell us that our search engine is down."


if __name__ == "__main__":
    print(process_results("What is the capital of France?"))
