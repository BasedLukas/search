import json
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Load selectors from JSON
def load_selectors(config_file: str) -> dict:
    with open(config_file, "r", encoding="utf-8") as file:
        return json.load(file)

# Extract domain from URL
def get_domain(url: str) -> str:
    return urlparse(url).netloc


def scrape_page(url: str, selectors: dict):
    domain = get_domain(url)
    
    if domain not in selectors:
        print(f"No selectors defined for {domain}")
        return None
    
    # Fetch page content
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    if response.status_code != 200:
        print(f"Failed to fetch {url} (Status {response.status_code})")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract data using selectors
    page_data = {}
    for key, selector in selectors[domain].items():
        if key in ["topics"]:
            # Handle multiple elements
            elements = soup.select(selector)
            page_data[key] = [el.get_text(strip=True) for el in elements] if elements else []
        else:
            # Handle single elements
            element = soup.select_one(selector)
            page_data[key] = element.get_text(strip=True) if element else None

    return page_data

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract page content using CSS selectors")
    parser.add_argument("url")
    parser.add_argument("--selectors", required=True, help="Your domain-to-CSS-selector JSON configuration")
    args = parser.parse_args()
    selectors = load_selectors(args.selectors)
    test_url = args.url
    data = scrape_page(test_url, selectors)

    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
