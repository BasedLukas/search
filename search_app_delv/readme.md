# Semantic search

Flask search interface using BGE embeddings, FAISS retrieval and HTML documents stored in S3.

- `app/`: search pages and `POST /api`.
- `backend/`: query encoding, vector lookup and document retrieval.
- [data/](data/readme.md): HTML embedding and index generation, plus Common Crawl downloads.
- `use/main.py`: OpenAI tool-calling client for the local API.
- `deploy/`: S3 upload, rsync, systemd and nginx configuration.

Running search requires a FAISS index, its document-path mapping, the corresponding HTML corpus and AWS access. These assets are supplied separately. Set `DELV_S3_BUCKET`; set `DELV_HTML_BASE_PATH` to the path prefix to remove from mapped document paths when forming S3 keys. The bucket holds `index.bin`, `url_mapping.json` and HTML objects under `docs/`.

From this directory, with storage configured:

```sh
uv sync
uv run python application.py
```

The app serves port 5000. Startup loads the index and `BAAI/bge-base-en-v1.5` model. Index and mapping files are cached in `backend/`; result HTML is fetched from S3. `POST /api` accepts `{"query": "search terms"}` and returns up to three HTML fields named `result0`, `result1` and `result2`.

Document encoding uses `normalize_embeddings=False`, while query encoding uses `True`. Align both settings before rebuilding an index.

The optional OpenAI client requires the OpenAI SDK, `OPENAI_API_KEY` and access to its configured model. Deployment requires `DELV_REMOTE_USER`, `DELV_REMOTE_HOST` and `DELV_REMOTE_DIR`; adapt the service user, paths and nginx host to the target machine.
