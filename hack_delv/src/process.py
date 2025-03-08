import requests
import os
import json
import groq
import re
from src.post_process import post_process

BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = groq.Client(api_key=GROQ_API_KEY)


def get_best_url(query: str, urls: list[str], titles: list[str], descriptions: list[str]) -> str:
    """
    Get the best URLs from the list of URLs using the groq chat completion.
    Each URL is numbered. The system message instructs the model to return only the numbers corresponding to the best URLs.
    """
    system_message = (
        "You select URLs to answer a given query. Select the 3 most relevant URLs in order of relevance and enclose your response in '<url>' tags."
        "Example response: <url>4</url> <url>2</url> <url>1</url>"
    )
    # Create a numbered list for each URL with its title and description.
    formatted_urls = "\n".join(
        [
            f"{i+1}. URL: {url}\n   Title: {title}\n   Description: {description}"
            for i, (url, title, description) in enumerate(zip(urls, titles, descriptions))
        ]
    )
    user_message = (
        f"<URLs>\n{formatted_urls}\n</URLs>\n\n"
        f"<query> {query} </query>"
        f"<task> Please reply with the number corresponding to the best URL. </task>"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=25
    )
    # Extract and parse the returned number.
    response_text = response.choices[0].message.content.strip()
    url_numbers = re.findall(r'<url>(\d+)</url>', response_text)
    
    if not url_numbers:
        return "Error: No valid URL found"
    # Convert to integers and validate
    chosen_numbers = []
    for num_str in url_numbers:
        try:
            num = int(num_str)
            if 1 <= num <= len(urls):
                chosen_numbers.append(num - 1)  # Convert to 0-based index
        except ValueError:
            continue
            
    if not chosen_numbers:
        return "Error: No valid URL numbers in range"
        
    # Build result string with URLs, titles and descriptions
    result = []
    for idx in chosen_numbers:
        result.append(
            f"URL: {urls[idx]}\n"
            f"Title: {titles[idx]}\n" 
            f"Description: {descriptions[idx]}\n"
        )
    
    return "\n".join(result)


def valid_query(query: str)->bool:
    """test that query exists and is max 400 chars and 50 words"""
    if not query:
        return False
    if len(query) > 400:
        return False
    if len(query.split()) > 50:
        return False
    return True


def valid_url(url: str)->bool:
    """test that url exists and is a valid URL format"""
    if not url:
        return False
    # Basic URL validation - should start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    return True


def process_url(url: str)->str:
    """directly process a URL through post_process"""
    if not valid_url(url):
        return "Invalid URL; URL must start with http:// or https://"
    
    try:
        return post_process(url)
    except Exception as e:
        return f"Error processing URL: {str(e)}"


def process_results(query: str)->str:
    """get user query, query brave and return the best matching url"""
    if not BRAVE_API_KEY or not GROQ_API_KEY:
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
        'count': 15,
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
        urls = [result['url'] for result in response.json()['web']['results']]
        titles = [result['title'] for result in response.json()['web']['results']]
        descriptions = [result['description'] for result in response.json()['web']['results']]
        return get_best_url(query, urls, titles, descriptions)
    else:
        return f"Error: please tell us that our search engine is down."


if __name__ == "__main__":
    print(process_results("Who is Lukas Bogacz"))
