#!/usr/bin/env python3
"""
Build a FAISS index from a JSONL file of embeddings.
Each line in the input JSONL file should contain a JSON object with:
    "url": a string (the file path or URL for the document)
    "embedding": a list of floats representing the embedding vector

This script supports several FAISS index types:
    - flat:        IndexFlatL2 (exact search)
    - ivf_flat:    IndexIVFFlat (coarse partitioning with exact vectors)
    - ivf_pq:      IndexIVFPQ (coarse partitioning with product quantization)
    - hnsw:        IndexHNSWFlat (graph-based approximate search)

Usage:
    python build_faiss_index.py --jsonl_file out.json --index_type ivf_pq

The URL mapping (from vector ID to document path) is saved in a separate JSON file.
"""

import argparse
import json
from typing import List, Dict, Any, Tuple, Optional
import faiss
import numpy as np
from multiprocessing import Pool


def process_line(line: str) -> Tuple[np.ndarray, str]:
    """
    Process a single JSONL line.
      {"url": "<url>", "embedding": [<float>, <float>, ...]}
    """
    data = json.loads(line)
    url = data["url"]
    vector = np.array(data["embedding"], dtype=np.float32)
    return vector, url


def parse_jsonl_file(filepath: str) -> Tuple[List[np.ndarray], List[str]]:
    """
    Parse a JSONL file using multiprocessing.
    Returns:
      A tuple (vectors, urls) where each vector corresponds to its URL.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        with Pool() as pool:
            # Adjust chunksize to balance performance and IPC overhead.
            pairs = pool.imap(process_line, f, chunksize=50)
            pairs = list(pairs)
    vectors, urls = zip(*pairs)
    return np.array(vectors), list(urls)


def build_faiss_index(
    d: int,
    index_type: str,
    num_vectors: int,
    nlist: int = 100,      # For IVF indices
    m: int = 8,            # For IVF-PQ: number of subquantizers
    nbits: int = 8,        # For IVF-PQ: bits per subvector
    hnsw_M: int = 64,      # For HNSW: number of neighbors per node
    efConstruction: int = 64,  # For HNSW: graph construction depth
    efSearch: int = 64,        # For HNSW: search depth
    metric: str = "L2"         # Currently only L2 supported; could extend to IP.
) -> faiss.Index:
    """
    Creates and returns a FAISS index according to the requested type.
    
    Parameters:
      d          : Dimension of the vectors.
      index_type : Type of index ("flat", "ivf_flat", "ivf_pq", or "hnsw").
      num_vectors: Total number of vectors (used for sanity checks/training sample size).
      nlist      : Number of clusters (cells) for IVF indices.
      m          : Number of subquantizers (only for ivf_pq).
      nbits      : Number of bits per subvector (only for ivf_pq).
      hnsw_M     : Maximum number of connections per node in HNSW.
      efConstruction: Exploration depth at index build time for HNSW.
      efSearch   : Exploration depth at query time for HNSW.
      metric     : Distance metric; "L2" is used by default.
      
    Returns:
      A FAISS Index instance.
    """
    # Choose metric type (only L2 is implemented here)
    metric_type = faiss.METRIC_L2

    if index_type == "flat":
        index = faiss.IndexFlatL2(d)
        print("Created Flat index (exact search).")
    elif index_type == "ivf_flat":
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist, metric_type)
        print(f"Created IVF-Flat index with nlist={nlist}.")
    elif index_type == "ivf_pq":
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFPQ(quantizer, d, nlist, m, nbits, metric_type)
        print(f"Created IVF-PQ index with nlist={nlist}, m={m}, nbits={nbits}.")
    elif index_type == "hnsw":
        index = faiss.IndexHNSWFlat(d, hnsw_M, metric_type)
        # Set HNSW-specific parameters
        index.hnsw.efConstruction = efConstruction
        index.hnsw.efSearch = efSearch
        print(f"Created HNSW index with M={hnsw_M}, efConstruction={efConstruction}, efSearch={efSearch}.")
    else:
        raise ValueError(f"Unknown index type: {index_type}")
    return index


def train_index_if_required(index: faiss.Index, training_vectors: np.ndarray) -> None:
    """
    For indexes that require training (IVF-based), train them.
    """
    if not index.is_trained:
        print("Training index on {} vectors...".format(training_vectors.shape[0]))
        index.train(training_vectors)
        print("Index training completed.")


def add_embeddings_to_index(
    index: faiss.Index,
    embeddings: np.ndarray,
    url_mapping: List[str],
    batch_size: int = 100000
) -> Dict[int, str]:
    """
    Adds embeddings to the FAISS index in batches.
    Also creates a mapping from vector id to URL.
    
    Parameters:
      index       : The FAISS index (already trained if needed).
      embeddings  : 2D numpy array of shape (n_vectors, d).
      url_mapping : List of URLs (one per vector).
      batch_size  : Batch size for adding embeddings.
    
    Returns:
      A dictionary mapping vector id (int) to URL.
    """
    n_vectors = embeddings.shape[0]
    id_to_url: Dict[int, str] = {}
    cur_index = 0
    for start in range(0, n_vectors, batch_size):
        end = min(start + batch_size, n_vectors)
        batch = embeddings[start:end]
        index.add(batch)
        # Map the new vectors to their URL; vector IDs are assigned sequentially.
        for i in range(start, end):
            id_to_url[i] = url_mapping[i]
        cur_index += (end - start)
        print(f"Added vectors {start} to {end} (total so far: {cur_index}).")
    return id_to_url


def main(args: argparse.Namespace) -> None:
    # Read embeddings and URL mapping from the JSONL file.
    print(f"Reading embeddings from {args.jsonl_file} ...")
    embeddings, urls = parse_jsonl_file(args.jsonl_file)
    n_vectors, d = embeddings.shape
    print(f"Loaded {n_vectors} embeddings of dimension {d}.")

    # Build the chosen index.
    index = build_faiss_index(
        d=d,
        index_type=args.index_type,
        num_vectors=n_vectors,
        nlist=args.nlist,
        m=args.m,
        nbits=args.nbits,
        hnsw_M=args.hnsw_M,
        efConstruction=args.efConstruction,
        efSearch=args.efSearch,
        metric=args.metric,
    )

    # For IVF-based indexes, we must train before adding vectors.
    if hasattr(index, "is_trained") and not index.is_trained:
        # Use a random subset (or the first batch) as training data.
        train_size = min(n_vectors, args.train_size)
        train_vectors = embeddings[:train_size]
        train_index_if_required(index, train_vectors)

    # Add embeddings (in batches) and build URL mapping.
    print("Adding embeddings to index...")
    id_to_url = add_embeddings_to_index(index, embeddings, urls, batch_size=args.batch_size)

    # Save the index and URL mapping to files.
    print(f"Writing index to {args.index_file} ...")
    faiss.write_index(index, args.index_file)
    print(f"Saving URL mapping to {args.url_file} ...")
    with open(args.url_file, "w", encoding="utf-8") as f:
        json.dump(id_to_url, f, indent=2)
    print(f"Index saved to {args.index_file}.")
    print(f"URL mapping saved to {args.url_file}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a FAISS index from a JSONL file of embeddings.")
    parser.add_argument("--jsonl_file", type=str, default="out.json", help="Path to JSONL file with embeddings.")
    parser.add_argument("--index_file", type=str, default="../backend/index.bin", help="Path to output FAISS index file.")
    parser.add_argument("--url_file", type=str, default="../backend/url_mapping.json", help="Path to output URL mapping JSON file.")
    parser.add_argument("--index_type", type=str, default="flat",
                        choices=["flat", "ivf_flat", "ivf_pq", "hnsw"],
                        help="Type of FAISS index to create.")
    parser.add_argument("--batch_size", type=int, default=100000, help="Number of vectors to process in a batch.")
    # IVF/IVFPQ parameters
    parser.add_argument("--nlist", type=int, default=100, help="Number of clusters for IVF indices.")
    parser.add_argument("--m", type=int, default=8, help="Number of subquantizers for IVF-PQ.")
    parser.add_argument("--nbits", type=int, default=8, help="Number of bits per subvector for IVF-PQ.")
    # HNSW parameters
    parser.add_argument("--hnsw_M", type=int, default=64, help="Number of connections per node for HNSW.")
    parser.add_argument("--efConstruction", type=int, default=64, help="efConstruction for HNSW (index build exploration depth).")
    parser.add_argument("--efSearch", type=int, default=64, help="efSearch for HNSW (search exploration depth).")
    # Metric and training size for IVF indexes
    parser.add_argument("--metric", type=str, default="L2", help="Distance metric to use (default L2).")
    parser.add_argument("--train_size", type=int, default=1000000, help="Number of vectors to use for training IVF indices.")
    args = parser.parse_args()
    main(args)
