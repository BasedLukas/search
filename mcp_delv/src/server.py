from search import get_delv
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("getdelv")

@mcp.tool()
def search(search_query: str = None, url: str = None) -> str:
    """
    Get API documentation or other coding related information.
    This tool has two modes of operation:
    
    1. SEARCH MODE (provide search_query parameter only):
       - Searches for coding docs, bug reports, GitHub issues, API references, code snippets etc.
       - Returns some text as well as a list of relevant URLs for further research
       
    2. URL MODE (provide url parameter only):
       - Retrieves and processes the content of any valid URL
       - Returns the structured content from that URL
    
    Args:
        search_query (str, optional): A keyword-rich query specifying what you're looking for
                                     (e.g., "snowflake snowpark 1.28.0 modin.pandas.DataFrame.dtypes")
        url (str, optional): Any valid URL to retrieve content from
                            
    Returns:
        A str containing the processed content and/or relevant search results.
        
    Note:
        - You must provide EITHER search_query OR url, not both
        - If both parameters are provided, url takes precedence
    """
    # Input validation
    if not search_query and not url:
        return "Error: You must provide either a search_query or url parameter."
        
    return get_delv(search_query=search_query, url=url)

if __name__ == "__main__":
    mcp.run(transport='stdio')