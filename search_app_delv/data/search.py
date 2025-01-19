import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Iterator


def load_embeddings_in_batches(
    file_path: str, 
    batch_size: int
) -> Iterator[Tuple[List[str], List[List[float]]]]:
    """
    Loads embeddings from a file in batches. Each line in the file is a JSON object
    of the form: {"url": <url_string>, "embedding": [floats]}.

    Args:
        file_path: Path to the embeddings file.
        batch_size: Number of embeddings per batch.
        max_vectors: Maximum number of vectors to process (useful for dev mode).

    Yields:
        A tuple of (urls, embeddings) for each batch.
    """
    urls, vectors = [], []
    total_vectors = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            urls.append(data["url"])
            vectors.append(data["embedding"])
            total_vectors += 1

            # Yield batch if size matches
            if len(urls) == batch_size:
                yield urls, vectors
                urls, vectors = [], []

            # Stop if max vector count is reached
            if total_vectors >= 100_000:
                print(f"WARNING: In dev mode, max vectors reached.")
                break

    # Yield any remaining vectors in the last batch
    if urls:
        yield urls, vectors


def initialize_faiss_index(dimension: int) -> faiss.IndexFlatL2:
    """
    Initializes a FAISS L2 distance index with the given dimension.
    """
    index = faiss.IndexFlatL2(dimension)
    return index


def add_embeddings_to_index(index: faiss.IndexFlatL2, embeddings: List[List[float]]):
    """
    Adds a batch of embeddings to the FAISS index.
    """
    vectors = np.array(embeddings, dtype='float32')
    index.add(vectors)


def query_faiss_index(
    index: faiss.IndexFlatL2,
    query_vector: List[float],
    urls: List[str],
    k: int = 5
) -> List[Tuple[str, float]]:
    """
    Queries the FAISS index for the top-k nearest embeddings and returns
    (url, distance) tuples.
    """
    query_vector = np.array([query_vector], dtype='float32')
    distances, indices = index.search(query_vector, k)
    return [(urls[i], distances[0][j]) for j, i in enumerate(indices[0])]


def create_search_engine(
    embeddings_file: str,
    model_id: str = "BAAI/bge-base-en-v1.5",
    device: str = "cpu",
    dim: int = 256,
    n_results: int = 6,
    batch_size: int = 1000
):
    """
    Loads embeddings incrementally, creates a FAISS index, and loads the model.
    Returns a `search(query, k=5)` function that can be used repeatedly.
    """
    index = initialize_faiss_index(dim)
    model = SentenceTransformer(model_id, device=device)
    all_urls = []

    for urls, embeddings in load_embeddings_in_batches(embeddings_file, batch_size):
        add_embeddings_to_index(index, embeddings)
        all_urls.extend(urls)

    def search(query: str, k: int = n_results) -> List[Tuple[str, float]]:
        # Encode query
        query_vector = model.encode(query, convert_to_tensor=False)[:dim]
        query_vector = np.array(query_vector, dtype='float32').reshape(1, -1)
        # Perform search
        try:
            distances, indices = index.search(query_vector, k)
        except Exception as e:
            print("ERROR: Faiss index search failed.")
            print(f"Query vector: {query_vector}")
            print(f"Error: {e}")
            return []

        # Map results
        results = [(all_urls[idx], distances[0][i]) for i, idx in enumerate(indices[0])]
        return results

    return search


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="FAISS similarity lookup.")
    parser.add_argument("--embeddings_file", type=str, required=True, help="Path to line-based JSON embeddings file.")
    parser.add_argument("--model_id", type=str, default="BAAI/bge-base-en-v1.5", help="SentenceTransformer model ID.")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run the model on (e.g., 'cpu', 'cuda').")
    parser.add_argument("--k", type=int, default=5, help="Number of top similar results to return.")
    args = parser.parse_args()

    # Create the search engine
    search_func = create_search_engine(
        embeddings_file=args.embeddings_file,
        model_id=args.model_id,
        device=args.device
    )

    # Interactive loop for testing
    while True:
        query = input("Enter a query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break

        results = search_func(query, k=args.k)
        print("\nTop results:")
        for url, dist in results:
            print(f"URL: {url}, Distance: {dist}")


if __name__ == "__main__":
    main()
