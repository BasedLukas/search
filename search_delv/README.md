# Document search

Reads documentation HTML from MongoDB, extracts text and XML context, and indexes it in Meilisearch. A FastAPI endpoint returns the XML context for the highest-ranked search result.

## Files

- [src/api.py](src/api.py): HTML extraction, indexing, search, URL ingestion and XML export.
- [query_mongo.py](query_mongo.py): helpers for inspecting stored documents and metadata.
- [pyproject.toml](pyproject.toml): Python dependencies.
- [.env.example](.env.example): MongoDB and Meilisearch configuration.

## Setup

Requires Python 3.13+, uv, MongoDB and Meilisearch. Copy `.env.example` to `.env`, set the connection values and start both services. Then run these commands from this directory:

```sh
uv sync
uv run python src/api.py --reindex --no-server
uv run python src/api.py
```

The API runs on port 8000. Send `POST /search` with `{"search_query": "your query"}`; the response's `text` field contains the result's XML context. `POST /reindex` clears and rebuilds the configured Meilisearch index.

## Document configuration

The loader reads MongoDB records with `url` and `raw_html` fields. Its default collection is `scraping_db.webpages`. To use documentation collected by [scrape_delv](../scrape_delv/README.md) with its default settings, set `MONGODB_DB=snowflake` and `MONGODB_COLLECTION=docs`. The crawler's GitHub source records use the separate `snowflake.github` collection and a `file_content` field.
