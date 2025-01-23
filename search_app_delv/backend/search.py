import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple


def create_search_engine(
    embeddings_file: str = "backend/index.bin",
    url_file: str = "backend/url_mapping.json",
    model_id: str = "BAAI/bge-base-en-v1.5",
    device: str = "cpu",
    dim: int = 256,
    n_results: int = 6
):
    """
    Loads embeddings and URL mapping, creates a FAISS index, and loads the model.
    Returns a `search(query, k=5)` function that can be used repeatedly.
    """
    # Load the FAISS index
    index = faiss.read_index(embeddings_file)

    # Load the URL mapping
    with open(url_file, "r") as f:
        url_mapping = json.load(f)

    # Load the model
    model = SentenceTransformer(model_id, device=device)

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

        # Map results to URLs
        results = [
            (url_mapping[idx], distances[0][i])
            for i, idx in enumerate(indices[0])
            if idx < len(url_mapping)  # Ensure valid index
        ]
        return results

    return search


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FAISS similarity lookup.")
    parser.add_argument("--embeddings_file", type=str, default="index.bin", help="Path to FAISS index file.")
    parser.add_argument("--url_file", type=str, default="url_mapping.json", help="Path to URL mapping file.")
    parser.add_argument("--model_id", type=str, default="BAAI/bge-base-en-v1.5", help="SentenceTransformer model ID.")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run the model on (e.g., 'cpu', 'cuda').")
    parser.add_argument("--k", type=int, default=5, help="Number of top similar results to return.")
    args = parser.parse_args()

    # Create the search engine
    search_func = create_search_engine(
        embeddings_file=args.embeddings_file,
        url_file=args.url_file,
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
