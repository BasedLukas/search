import requests
import argparse
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time

def clean_html(html_content):
    """
    Clean HTML by removing elements that don't contain text or URLs.
    Returns a simplified HTML structure.
    """
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for tag in ['script', 'style', 'svg', 'path', 'meta', 'link']:
        for element in soup.find_all(tag):
            element.decompose()
    
    # Find and remove comments - using 'string' instead of 'text'
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()
    
    # Function to check if an element contains text or URLs
    def has_text_or_url(element):
        # Check if element has text
        if element.get_text(strip=True):
            return True
        
        # Check if element has href, src, or data-* attributes that might contain URLs
        for attr in ['href', 'src']:
            if element.has_attr(attr) and element[attr]:
                return True
                
        # Check data-* attributes
        for attr in element.attrs:
            if attr.startswith('data-') and element[attr]:
                return True
        
        return False
    
    # Remove elements without text or URLs, except structural elements
    structural_elements = ['html', 'body', 'head', 'div', 'section', 'article', 'header', 'footer', 'main', 'aside', 'nav']
    
    # Find all elements and filter them
    all_elements = list(soup.find_all(True))
    for element in all_elements:
        try:
            if (element.name not in structural_elements and 
                not has_text_or_url(element) and 
                not any(has_text_or_url(child) for child in element.find_all(True))):
                element.decompose()
        except Exception as e:
            print(f"Error processing element {element.name}: {e}")
            continue
    
    # Remove empty attributes to reduce size
    for element in soup.find_all(True):
        try:
            attrs_to_remove = []
            for attr, value in element.attrs.items():
                if not value or (isinstance(value, str) and len(value) > 200):
                    attrs_to_remove.append(attr)
            
            for attr in attrs_to_remove:
                del element[attr]
        except Exception as e:
            print(f"Error removing attributes: {e}")
            continue
            
    # Remove empty class attributes
    for element in soup.find_all(attrs={"class": True}):
        try:
            if not element["class"]:
                del element["class"]
        except Exception as e:
            print(f"Error removing class: {e}")
            continue
            
    # Convert to string
    return str(soup)

def fetch_and_clean_url(url):
    """Fetch a URL and clean its HTML content"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # GitHub often requires cookies for scraping
    session = requests.Session()
    
    try:
        # First request to get cookies
        session.get("https://github.com/", headers=headers, timeout=15)
        
        # Small delay to avoid triggering rate limits
        time.sleep(1)
        
        # Main request
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if response.text:
            return clean_html(response.text)
        else:
            print("Empty response received")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def save_to_file(content, url):
    """Save cleaned HTML to file"""
    if not content:
        print("No content to save")
        return None
        
    domain = urlparse(url).netloc
    filename = f"cleaned_{domain.replace('.', '_')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean page HTML for selector development")
    parser.add_argument("url")
    url = parser.parse_args().url
    
    print(f"Fetching and cleaning: {url}")
    cleaned_html = fetch_and_clean_url(url)
    
    if cleaned_html:
        filename = save_to_file(cleaned_html, url)
        
        try:
            # Create a new session for size comparison
            session = requests.Session()
            response = session.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            }, timeout=15)
            response.raise_for_status()
            original_size = len(response.text)
            cleaned_size = len(cleaned_html)
            reduction = 100 - (cleaned_size / original_size * 100)
            
            print(f"Original size: {original_size:,} bytes")
            print(f"Cleaned size: {cleaned_size:,} bytes")
            print(f"Size reduction: {reduction:.2f}%")
            print(f"Saved to: {filename}")
        except Exception as e:
            print(f"Error calculating size: {e}")
            if filename:
                print(f"Cleaned HTML saved to: {filename}")
    else:
        print("Failed to clean HTML")