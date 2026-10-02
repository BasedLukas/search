# GetDelv

Documentation search and retrieval for AI coding agents. This repository contains the crawlers, retrieval pipelines, APIs, MCP integration and product website developed for GetDelv.

## Components

| Folder | Implementation |
|---|---|
| [search_app_delv](search_app_delv/) | Semantic search with BGE embeddings, FAISS, S3 document storage and a Flask UI; Common Crawl download scripts. |
| [search_delv](search_delv/) | MongoDB/Meilisearch indexing, FastAPI document search and HTML-to-XML context processing. |
| [scrape_delv](scrape_delv/) | Documentation and GitHub crawlers with filtering, metadata extraction and MongoDB storage. |
| [hack_delv](hack_delv/) | Brave search, Groq URL selection, page extraction and an AWS Lambda API. |
| [mcp_delv](mcp_delv/) | An MCP search tool connecting coding agents to the retrieval API. |
| [getdelv](getdelv/) | Product landing site and UI design styles. |

## Suggested reading

1. [Semantic retrieval](search_app_delv/backend/search.py): model encoding, FAISS results and source-document retrieval.
2. [Document API](search_delv/src/api.py): content shaping, indexing, search and reindex workflows.
3. [GitHub ingestion](scrape_delv/src/src/spiders/snowflake_github.py): repository files and metadata collection.
4. [Web retrieval](hack_delv/src/process.py): result selection and content extraction.
5. [MCP server](mcp_delv/src/server.py): the agent-facing integration.

Component READMEs describe dependencies, configuration and entry points. Corpora, generated indexes, database contents and credentials are not included.

[MIT license](LICENSE).
