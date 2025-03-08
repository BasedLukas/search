import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def post_process(url: str) -> str:
    """
    Fetch a webpage and extract structured content including title, description, 
    and main text elements. Links are preserved in their original context with
    absolute URLs. It removes irrelevant tags (like scripts and styles) and 
    unwraps non-essential container tags while preserving a clean structure.

    Args:
        url (str): URL of the webpage to process.

    Returns:
        str: An XML-like string with title, description, and content tags.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title from <title> tag if available.
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract description from meta tags (first trying "description", then "og:description")
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    else:
        meta_desc = soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

    # Locate main content container. Fallback to <body> if not found.
    main_content = soup.find("main") or soup.find("article") or soup.body
    if main_content is None:
        main_content = soup

    # Remove unwanted tags
    for tag in main_content.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # Define a set of allowed tags that preserve layout.
    allowed_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "blockquote", "pre", "code", "a"}
    
    # Process all tags
    for tag in main_content.find_all():
        if tag.name == "a" and tag.get("href"):
            # Convert relative URLs to absolute URLs for links
            href = tag["href"]
            absolute_url = urljoin(url, href)
            if absolute_url.startswith(('http://', 'https://')):
                # Keep only the href attribute with the absolute URL
                tag.attrs = {"href": absolute_url}
            else:
                # Remove non-http(s) links but preserve their text
                tag.unwrap()
        elif tag.name not in allowed_tags:
            tag.unwrap()
        else:
            # For non-link tags in allowed_tags, remove all attributes
            if tag.name != "a":
                tag.attrs = {}

    # Get the cleaned inner HTML of the main content.
    content_html = main_content.decode_contents()

    # Build the final XML-like structure with title, description, and content
    result = f"<document>\n  <title>{title}</title>\n"
    if description:
        result += f"  <description>{description}</description>\n"
    result += "  <content>\n" + content_html + "\n  </content>\n</document>"

    return result


if __name__ == "__main__":
    url = ("https://example.invalid")
    structured_text = post_process(url)
    print(structured_text)

