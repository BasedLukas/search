import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import groq
from typing import List, Dict, Any, Tuple, Optional

from src.helpers import (
    SearchResult, ApiError, valid_query, valid_url,
    BRAVE_API_KEY, GROQ_API_KEY, logger, extract_url_numbers
)

# Initialize Groq client if API key exists
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = groq.Client(api_key=GROQ_API_KEY, timeout=10)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")


def post_process(url: str) -> str:
    """
    Fetch a webpage and extract structured content including title, description, 
    and main text elements. Links are preserved in their original context with
    absolute URLs.
    
    Args:
        url (str): URL of the webpage to process.
        
    Returns:
        str: An XML-like string with title, description, and content tags.
        
    Raises:
        requests.exceptions.RequestException: If the URL request fails
        ValueError: If the URL is invalid
    """
    if not valid_url(url):
        raise ValueError("Invalid URL format")
        
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract description
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    else:
        meta_desc = soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

    # Locate main content
    main_content = soup.find("main") or soup.find("article") or soup.body or soup
    
    if not main_content:
        logger.warning(f"No main content found for URL: {url}")
        # Return minimal document structure with just title and description
        return f"<document>\n  <title>{title}</title>\n  <description>{description}</description>\n  <content></content>\n</document>"

    # Remove unwanted tags
    for tag in main_content.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # Define allowed tags
    allowed_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "blockquote", "pre", "code", "a"}
    
    # Process all tags
    for tag in main_content.find_all():
        if tag.name == "a" and tag.get("href"):
            # Convert relative URLs to absolute URLs for links
            href = tag["href"]
            absolute_url = urljoin(url, href)
            if absolute_url.startswith(('http://', 'https://')):
                tag.attrs = {"href": absolute_url}
            else:
                tag.unwrap()
        elif tag.name not in allowed_tags:
            tag.unwrap()
        else:
            # For non-link tags in allowed_tags, remove all attributes
            if tag.name != "a":
                tag.attrs = {}

    # Get the cleaned inner HTML of the main content
    content_html = main_content.decode_contents()

    # Build the final XML-like structure
    result = f"<document>\n  <title>{title}</title>\n"
    if description:
        result += f"  <description>{description}</description>\n"
    result += "  <content>\n" + content_html + "\n  </content>\n</document>"

    return result

def get_search_results(query: str) -> List[SearchResult]:
    """
    Query Brave Search API and return results.
    
    Args:
        query (str): Search query string
        
    Returns:
        List[SearchResult]: List of search results
        
    Raises:
        ApiError: If the search request fails
        ValueError: If query is invalid
    """
    if not valid_query(query):
        raise ValueError("Invalid query: must be less than 400 chars and 50 words")
        
    if not BRAVE_API_KEY:
        raise ApiError("Brave API key not configured", 500)
    
    # Make request to Brave Search API
    brave_api_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    result_filter = 'web'
    goggles = os.getenv("BRAVE_GOGGLES_URL")
    params = {
        'q': query,
        'count': 15,
        'offset': 0,
        'text_decorations': False,
        'spellcheck': False,
        'result_filter': result_filter,
        'extra_snippets': False,
        'summary': False,
    }
    if goggles:
        params["goggles"] = goggles

    try:
        response = requests.get(
            brave_api_url,
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if 'web' not in data or 'results' not in data['web']:
            raise ApiError("Invalid search response format", 500)
            
        results = []
        for result in data['web']['results']:
            results.append(SearchResult(
                url=result.get('url', ''),
                title=result.get('title', ''),
                description=result.get('description', '')
            ))
        
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Search API request failed: {str(e)}")
        raise ApiError("Failed to fetch search results", 500)

def rank_urls(query: str, search_results: List[SearchResult]) -> List[int]:
    """
    Rank URLs using Groq API.
    
    Args:
        query (str): The original search query
        search_results (List[SearchResult]): List of search results to rank
        
    Returns:
        List[int]: List of indices of ranked search results (in order of relevance)
        
    Raises:
        ApiError: If the ranking request fails
    """
    if not GROQ_API_KEY or not groq_client:
        raise ApiError("Groq API key not configured", 500)
        
    if not search_results:
        return []
    
    system_message = (
        "You select URLs to answer a given query. Select the 3 most relevant URLs in order of relevance and enclose your response in '<url>' tags."
        "Example response: <url>4</url> <url>2</url> <url>1</url>"
    )
    
    # Create a numbered list for each URL with its title and description
    formatted_urls = "\n".join(
        [
            f"{i+1}. URL: {result.url}\n   Title: {result.title}\n   Description: {result.description}"
            for i, result in enumerate(search_results)
        ]
    )
    
    user_message = (
        f"<URLs>\n{formatted_urls}\n</URLs>\n\n"
        f"<query> {query} </query>"
        f"<task> Please reply with the numbers corresponding to the best URLs. </task>"
    )
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=25
        )
        
        response_text = response.choices[0].message.content.strip()
        valid_indices = extract_url_numbers(response_text, len(search_results))
        
        if not valid_indices:
            logger.warning(f"No valid URL indices found in Groq response: {response_text}")
            # Fallback to the first result if no valid indices
            return [0] if search_results else []
        
        return valid_indices
    except Exception as e:
        logger.error(f"Groq ranking failed: {str(e)}")
        raise ApiError("Failed to rank search results", 500)

def process_url_request(url: str) -> Dict[str, Any]:
    """
    Process a URL directly and return its content.
    
    Args:
        url (str): URL to process
        
    Returns:
        Dict[str, Any]: Processed result
        
    Raises:
        ApiError: If URL processing fails
    """
    if not valid_url(url):
        raise ApiError("Invalid URL format", 400)
    
    try:
        content = post_process(url)
        return {
            "processed_content": content,
            "source_url": url
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"URL request failed: {str(e)}")
        raise ApiError(f"Failed to fetch URL: {str(e)}", 500)
    except Exception as e:
        logger.error(f"URL processing failed: {str(e)}")
        raise ApiError(f"Failed to process URL: {str(e)}", 500)


def process_query_request(query: str) -> Dict[str, Any]:
    """
    Process a search query, find and rank URLs, and return processed content.
    
    Args:
        query (str): Search query
        
    Returns:
        Dict[str, Any]: Processed result with top URL content and other ranked URLs
        
    Raises:
        ApiError: If processing fails at any stage
    """
    if not valid_query(query):
        raise ApiError("Invalid query format: must be less than 400 chars and 50 words", 400)
    
    # Get search results
    search_results = get_search_results(query)
    if not search_results:
        return {
            "message": "No search results found",
            "processed_content": "",
            "top_result": None,
            "other_results": []
        }
    
    # Rank the URLs
    try:
        ranked_indices = rank_urls(query, search_results)
        if not ranked_indices:
            # If ranking fails, use the first result as a fallback
            ranked_indices = [0]
    except ApiError as e:
        # If ranking fails, fall back to using the first search result
        logger.warning(f"URL ranking failed, using first result as fallback: {str(e)}")
        ranked_indices = [0]
    
    # Process the top-ranked URL
    top_result = search_results[ranked_indices[0]]
    other_results = [search_results[idx] for idx in ranked_indices[1:] if idx < len(search_results)]
    remaining_results = [result for i, result in enumerate(search_results) 
                         if i not in ranked_indices and i != ranked_indices[0]]
    
    # Add any remaining results after the ranked ones
    other_results.extend(remaining_results)
    
    try:
        processed_content = post_process(top_result.url)
        
        return {
            "processed_content": processed_content,
            "top_result": top_result.to_dict(),
            "other_results": [r.to_dict() for r in other_results]
        }
    except Exception as e:
        logger.error(f"Top URL processing failed: {str(e)}")
        # Return the results without processed content in case of failure
        return {
            "message": f"Failed to process top URL: {str(e)}",
            "processed_content": "",
            "top_result": top_result.to_dict(),
            "other_results": [r.to_dict() for r in other_results]
        }