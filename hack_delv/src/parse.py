from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html
import requests


def build_structured_content(soup, base_url, selector_config):
    """
    Build structured XML content from a BeautifulSoup object based on provided selector configuration.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        base_url (str): Original URL of the page (for resolving relative links)
        selector_config (dict): Configuration for content extraction with the following keys:
            - include: List of CSS selectors for elements to include
            - exclude: List of CSS selectors for elements to exclude
            - hierarchies: List of hierarchical paths in the format ["parent", "child", "grandchild"]
            - containers: List of objects with "selector" and "elements" keys
        
    Returns:
        str: An XML document with the extracted content
    """
    # Create a container for the content
    content_soup = BeautifulSoup("<div></div>", 'html.parser')
    root_div = content_soup.div
    
    # Process include selectors
    if "include" in selector_config:
        for selector in selector_config["include"]:
            for element in soup.select(selector):
                # Create a copy of the element
                element_copy = BeautifulSoup(str(element), 'html.parser').contents[0]
                root_div.append(element_copy)
    
    # Process hierarchies
    if "hierarchies" in selector_config:
        for hierarchy in selector_config["hierarchies"]:
            if len(hierarchy) < 2:
                continue  # Need at least a parent and child
                
            parent_selector = hierarchy[0]
            parent_elements = soup.select(parent_selector)
            
            for parent in parent_elements:
                current_elements = [parent]
                
                # Process each level in the hierarchy
                for i in range(1, len(hierarchy)):
                    child_selector = hierarchy[i]
                    next_elements = []
                    
                    for element in current_elements:
                        matching_children = element.select(child_selector)
                        next_elements.extend(matching_children)
                    
                    current_elements = next_elements
                
                # Add the final elements to the content
                for element in current_elements:
                    element_copy = BeautifulSoup(str(element), 'html.parser').contents[0]
                    root_div.append(element_copy)
    
    # Process containers
    if "containers" in selector_config:
        for container_config in selector_config["containers"]:
            container_selector = container_config["selector"]
            element_selectors = container_config["elements"]
            
            for container in soup.select(container_selector):
                # Create a copy of the container
                container_copy = BeautifulSoup(str(container), 'html.parser').contents[0]
                
                # Track which elements to keep (including their parents)
                to_keep = set()
                
                # Add elements matching selectors and their ancestors to the keep set
                for selector in element_selectors:
                    for element in container_copy.select(selector):
                        to_keep.add(element)
                        for parent in element.parents:
                            if parent == container_copy or parent is None:
                                break
                            to_keep.add(parent)
                
                # Remove elements not in the keep set
                for element in list(container_copy.find_all()):
                    if element != container_copy and element not in to_keep:
                        element.decompose()
                
                # Add the filtered container to the content
                root_div.append(container_copy)
    
    # Process exclude selectors
    if "exclude" in selector_config:
        for selector in selector_config["exclude"]:
            for element in root_div.select(selector):
                element.decompose()
    
    # Process links and clean elements
    all_urls = set()
    for link in root_div.find_all("a", href=True):
        href = link.get("href", "")
        if href and not href.startswith(("#", "javascript:")):
            abs_url = urljoin(base_url, href)
            link["href"] = abs_url
            all_urls.add(abs_url)
    
    # Clean elements
    for tag in root_div.find_all(["script", "style", "noscript"]):
        tag.decompose()
        
    for tag in root_div.find_all():
        if tag.name == "a" and tag.get("href"):
            href = tag["href"]
            tag.attrs = {"href": href}
        else:
            tag.attrs = {}
    
    # Generate XML from the filtered content
    xml_content = "<document>\n"
    xml_content += f"  <url>{html.escape(base_url)}</url>\n"
    
    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if title:
        xml_content += f"  <title>{html.escape(title)}</title>\n"
    
    # Extract description
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    else:
        meta_desc = soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()
    
    if description:
        xml_content += f"  <description>{html.escape(description)}</description>\n"
    
    # Add content section
    xml_content += "  <content>\n"
    for element in root_div.children:
        if hasattr(element, 'name'):  # Check if it's a tag and not a string
            xml_content += f"    {str(element)}\n"
    xml_content += "  </content>\n"
    
    # Add URLs section
    if all_urls:
        xml_content += "  <urls>\n"
        for url in sorted(all_urls):
            xml_content += f"    <url>{html.escape(url)}</url>\n"
        xml_content += "  </urls>\n"
    
    xml_content += "</document>"
    
    return xml_content

selector_config = {
    # Basic inclusion/exclusion with CSS selectors
    "include": [
        "main article",
        ".content"
    ],
    "exclude": [
        ".sidebar", 
        ".ads", 
        "nav", 
        "footer"
    ],
    
    # Hierarchical selection (similar to your div->h1->p idea)
    "hierarchies": [
        ["div.article", "h1", "p"],         # Select paragraphs under h1 under div.article
        ["section.main", "article", ".body"] # Select .body elements in articles in section.main
    ],
    
    # Container-based selection (keep structure but only specific elements)
    "containers": [
        {
            "selector": "article.post",
            "elements": ["h1", "p", "img"]  # Keep only these elements within article.post
        }
    ]
}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract structured content using CSS rules")
    parser.add_argument("url")
    args = parser.parse_args()
    url = args.url
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    xml = build_structured_content(soup, url, selector_config)
    with open("output.xml", "w", encoding="utf-8") as f:
        f.write(xml)
