# GetDelv MCP server

Connect a coding agent to GetDelv's web retrieval API over MCP stdio.

- [src/server.py](src/server.py): exposes `search(search_query)` for technical documentation queries.
- [src/search.py](src/search.py): implements the HTTP client, including direct URL retrieval through `get_delv(url=...)`.

The client sends POST requests as `{"body": "<JSON containing query or url>"}` and returns the API response as text. The MCP tool accepts a `search_query` string and instructs the agent to make one search per turn.

Requires Python 3.13+ and MCP SDK v1. In this directory, run `uv sync`, configure `DELV_API_ENDPOINT` and `API_KEY`, then start with `uv run python src/server.py`. Configuration can also come from a local `.env`.

For a desktop MCP client, set its command to your Python environment and its argument to this directory's `src/server.py`. Supply `DELV_API_ENDPOINT` and `API_KEY` in the client's environment.
