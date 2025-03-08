
from search import search_delv
from mcp.server.fastmcp import FastMCP


# Initialize the MCP server
mcp = FastMCP("getdelv")

@mcp.tool()
def search(search_query: str) -> str:
    """
    Search for coding docs, bug reports, issues, API references, get started guides, etc.
    Use this when interacting with any external library, or when you need to find information
    about a specific function, class, or concept.

    Args:
        search_query (str):This can be a keyword query such as "snowflake snowpark 1.28.0 modin.pandas.DataFrame.dtypes" or a longer paragraph containing logs and contextual information along with a question.
    Returns:
        A short str paragraph containing one or more search results.
    """
    
    return search_delv(search_query)

if __name__ == "__main__":
    mcp.run(transport='stdio')

