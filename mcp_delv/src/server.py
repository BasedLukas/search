from search import get_delv
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("getdelv")

@mcp.tool()
def search(search_query: str = None) -> str:
    """
    Get API documentation or other coding related information.
    Only make one search per chat!

    - Searches for coding docs, bug reports, GitHub issues, API references, code snippets etc.

    Args:
        search_query (str, optional): A keyword-rich query specifying what you're looking for
                                     (e.g., "snowflake snowpark 1.28.0 modin.pandas.DataFrame.dtypes")

                            
    Returns:
        A str containing the processed content .
        
    Note:
        - Never make more than one search per chat turn!!!
    """

    return get_delv(search_query=search_query)

if __name__ == "__main__":
    mcp.run(transport='stdio')