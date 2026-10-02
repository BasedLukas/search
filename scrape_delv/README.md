# Documentation and repository crawlers

Collects technical documentation HTML and GitHub source files using Scrapy, with link filtering, metadata extraction, retries and MongoDB storage. A Jina Reader crawler extracts OpenAI Agents documentation into local files.

## Files

- [snowflake_docs.py](src/src/spiders/snowflake_docs.py): follows Snowflake documentation links and collects page titles, language and HTTP metadata.
- [snowflake_github.py](src/src/spiders/snowflake_github.py): enumerates a GitHub organization, shallow-clones repositories and extracts source files.
- [agent_docs.py](src/src/spiders/agent_docs.py): crawls OpenAI Agents documentation through Jina Reader.
- [pipelines.py](src/src/pipelines.py): MongoDB storage for documentation pages and repository files.
- [items.py](src/src/items.py), [middlewares.py](src/src/middlewares.py) and [settings.py](src/src/settings.py): record definitions, filtering and crawler configuration.
- [.env.example](.env.example): connection settings and the Jina API key variable.

## Setup

Requires Python 3.13+, uv and MongoDB. The GitHub crawler also uses Git. From this directory:

```sh
uv sync
export MONGODB_URI=mongodb://127.0.0.1:27017
export MONGODB_DATABASE=snowflake
cd src
uv run scrapy crawl snowflake_docs
uv run scrapy crawl github_repo
```

The GitHub crawler defaults to the `snowflakedb` organization; select another with `-a organization=NAME`. To run the Jina crawler, set `JINA_API_KEY` and use `uv run scrapy crawl simple_crawler` from `src/`. Its output is written to `crawled_pages/` in the working directory.

## Storage

The default MongoDB database is `snowflake`. Documentation pages go into `docs` with `url` and `raw_html` fields; repository files go into `github` with `file_content`. [search_delv](../search_delv/README.md) reads HTML records and selects its collection through `MONGODB_DB` and `MONGODB_COLLECTION`.
