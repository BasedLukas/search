import requests
from bs4 import BeautifulSoup

def extract_structured_content(url: str) -> str:
    """
    Fetch a webpage and extract structured content including title, description, 
    and main text elements. It removes irrelevant tags (like scripts and styles) 
    and unwraps non-essential container tags to preserve a clean structure of 
    paragraphs, headings, lists, and other relevant elements.

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
    allowed_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "blockquote", "pre", "code"}
    # Unwrap any tag not in allowed_tags so that inner content remains.
    for tag in main_content.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()
        else:
            tag.attrs = {}  # Remove attributes for a cleaner structure

    # Get the cleaned inner HTML of the main content.
    content_html = main_content.decode_contents()

    # Debug: write the cleaned HTML structure to a file.
    with open("cleaned_soup.html", "w", encoding="utf-8") as f:
        f.write(main_content.prettify())

    # Build the final XML-like structure with title, description, and content.
    result = f"<document>\n  <title>{title}</title>\n"
    if description:
        result += f"  <description>{description}</description>\n"
    result += "  <content>\n" + content_html + "\n  </content>\n</document>"

    return result


if __name__ == "__main__":
    url = ("https://docs.snowflake.com/en/developer-guide/snowflake-python-api/"
           "reference/latest/_autosummary/snowflake.core.Root")
    structured_text = extract_structured_content(url)
    print(structured_text)