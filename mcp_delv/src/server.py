
from search import search_delv, get_url_content
from mcp.server.fastmcp import FastMCP


# Initialize the MCP server
mcp = FastMCP("getdelv")

@mcp.tool()
def search(search_query: str) -> str:
    """
    Search for coding docs, bug reports, github issues, API references, get started guides, etc.
    Use this when interacting with unfamiliar coding libraries, or when you need to find up to date information
    Args:
        search_query (str):This should be a keyword heavy query specifying exactly what you're looking for such as "snowflake snowpark 1.28.0 modin.pandas.DataFrame.dtypes" 
    Returns:
        A str containing a list of relevant URLs.
    """
    return search_delv(search_query)

@mcp.tool()
def get_url(url: str) -> str:
    """
    Get the content of a URL. 
    You can enter any URL; one you are already familiar with, one provided by the user, or one from a search result.
    Args:
        url (str): Any valid URL.
    Returns:
        A short str containing the content of the webpage.
    """
    return get_url_content(url)

if __name__ == "__main__":
    mcp.run(transport='stdio')

