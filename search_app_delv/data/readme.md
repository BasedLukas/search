# Corpus and index preparation

- `model.py`: recursively embeds HTML files with `BAAI/bge-base-en-v1.5` and appends document paths and vectors to a JSONL file.
- `post_processing.py`: builds a FAISS index and vector-to-document mapping. It supports flat, IVF, IVF-PQ and HNSW indexes; the default is flat L2 search.
- `download.py`: downloads Common Crawl WET files. Its `download_wat_files()` function also supports WAT downloads. These downloads are separate from the HTML input used by the embedding pipeline.

After installing the parent project's dependencies, run from this directory. Put `HF_TOKEN` in a local `.env` and set `DELV_HTML_DIR` to your HTML corpus directory. `model.py` defaults to CUDA; CPU use requires setting `device="cpu"` in its `process_directory` call.

```sh
uv run python model.py
uv run python post_processing.py --jsonl_file out.json --index_type flat
```

Embeddings default to `out.json`; `DELV_EMBEDDINGS_FILE` changes that path. Pass the same path to `--jsonl_file`. Index generation defaults to `../backend/index.bin` and `../backend/url_mapping.json`; override them with `--index_file` and `--url_file`. The mapping records input file paths, which must correspond to the HTML objects used by search.

For Common Crawl downloads, `uv run python download.py` fetches up to 100 WET files from the configured crawl into `downloaded_wets/`. It uses AWS credentials to list objects in the public Common Crawl bucket. Adjust the function's crawl prefix and download limit as needed.
