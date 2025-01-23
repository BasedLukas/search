import os
import gzip
import dotenv
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from huggingface_hub import login
from typing import List, Tuple, Set

MODEL_ID = "BAAI/bge-base-en-v1.5"

def load_environment():
    env = dotenv.dotenv_values()
    hf_token = env.get("HF_TOKEN", "")
    if not hf_token:
        raise ValueError("HF_TOKEN is not set in the environment file.")
    login(token=hf_token, add_to_git_credential=True)

def initialize_model(device: str = "cpu") -> SentenceTransformer:
    return SentenceTransformer(MODEL_ID, device=device)

def parse_wet_file(file_path: str) -> List[Tuple[str, str]]:
    url_content_pairs = []
    open_func = gzip.open if file_path.endswith('.gz') else open
    with open_func(file_path, 'rt', encoding='utf-8') as file:
        url = None
        content = []
        for line in file:
            line = line.strip()
            if line.startswith("WARC-Target-URI:"):
                if url and content:
                    url_content_pairs.append((url, "\n".join(content)))
                url = line.replace("WARC-Target-URI:", "").strip()
                content = []
            elif url:
                content.append(line)
        if url and content:
            url_content_pairs.append((url, "\n".join(content)))
    return url_content_pairs

def embed_content(
    model: SentenceTransformer,
    url_content_pairs: List[Tuple[str, str]],
    working_file: str,
    embedding_dim: int,
    batch_size: int,
    precision: str
):
    with open(working_file, "w", encoding="utf-8") as wf:
        for i in range(0, len(url_content_pairs), batch_size):
            print(f"Processing batch {i}")
            batch = url_content_pairs[i : i + batch_size]
            contents = [text for _, text in batch]
            batch_embeddings = model.encode(
                contents,
                convert_to_tensor=True,
                batch_size=batch_size,
                precision=precision
            )
            for idx, (url, _) in enumerate(batch):
                truncated_emb = batch_embeddings[idx][:embedding_dim].tolist()
                data = {"url": url, "embedding": truncated_emb}
                json.dump(data, wf, ensure_ascii=False)
                wf.write("\n")

def load_processed_files(metadata_file: str) -> Set[str]:
    if not os.path.exists(metadata_file):
        return set()
    with open(metadata_file, "r", encoding="utf-8") as f:
        return {line.strip() for line in f}

def append_working_to_permanent(working_file: str, permanent_file: str):
    with open(working_file, "r", encoding="utf-8") as wf, \
         open(permanent_file, "a", encoding="utf-8") as pf:
        for line in wf:
            pf.write(line)
    # Clear the working file
    open(working_file, "w").close()

def process_directory(
    input_dir: str,
    permanent_file: str,
    working_file: str,
    metadata_file: str,
    device: str = "cpu",
    batch_size: int = 32,
    embedding_dim: int = 768,
    precision: str = "float32"
):
    processed_files = load_processed_files(metadata_file)
    model = initialize_model(device)

    for file_name in os.listdir(input_dir):
        full_path = os.path.join(input_dir, file_name)
        # Skip if not a WET file or if already processed
        if not os.path.isfile(full_path) or not file_name.endswith(".wet.gz"):
            continue
        if file_name in processed_files:
            print(f"Skipping already processed file: {file_name}")
            continue

        print(f"Processing new file: {file_name}")
        url_content_pairs = parse_wet_file(full_path)
        embed_content(
            model,
            url_content_pairs,
            working_file=working_file,
            embedding_dim=embedding_dim,
            batch_size=batch_size,
            precision=precision
        )
        append_working_to_permanent(working_file, permanent_file)
        with open(metadata_file, "a", encoding="utf-8") as mf:
            mf.write(file_name + "\n")
        processed_files.add(file_name)


def normalize_embeddings(input_file: str, output_file: str):
    embeddings = []
    urls = []

    # Read and parse all embeddings from the input file
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            urls.append(data["url"])
            embeddings.append(data["embedding"])

    arr = np.array(embeddings, dtype=np.float32)  # shape: (num_samples, dims)

    # Compute summary statistics
    mean = arr.mean(axis=0)  # dimension-wise mean
    min_ = arr.min(axis=0)
    max_ = arr.max(axis=0)
    range_ = np.where(max_ == min_, 1, max_ - min_)  # Avoid division by zero

    # Normalize dimension-wise
    arr = (arr - mean) / range_

    # Scale to 0-255 and convert to uint8
    global_min = arr.min()
    global_max = arr.max()
    arr = (arr - global_min) / (global_max - global_min) * 255
    arr = arr.astype(np.uint8)

    # Write summary statistics and normalized embeddings to the output file
    statistics = {
        "mean": mean.tolist(),
        "min": min_.tolist(),
        "max": max_.tolist(),
        "global_min": global_min,
        "global_max": global_max
    }

    with open(output_file, "w", encoding="utf-8") as wf:
        # Write the summary statistics as the first line
        json.dump({"statistics": statistics}, wf, ensure_ascii=False)
        wf.write("\n")

        # Write the normalized embeddings
        for url, embedding in zip(urls, arr):
            data_out = {"url": url, "embedding": embedding.tolist()}
            json.dump(data_out, wf, ensure_ascii=False)
            wf.write("\n")

    # Print summary information
    print("Normalization complete.")
    print(f"Number of vectors processed: {len(embeddings)}")
    print(f"Number of dimensions per vector: {arr.shape[1]}")
    print("Summary statistics written to the output file.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process WET files and embed content with restart capability.")
    parser.add_argument("--input_dir", type=str, default="downloaded_wets", help="Directory containing WET files.")
    parser.add_argument("--output_file", type=str, default="out.json", help="Permanent JSON lines file.")
    parser.add_argument("--working_file", type=str, default="temp.json", help="Working JSON lines file.")
    parser.add_argument("--metadata_file", type=str, default="processing_metadata", help="File listing processed WET files.")
    parser.add_argument("--device", type=str, default="cuda", help="Device to run the model on (e.g., 'cpu', 'cuda').")
    parser.add_argument("--batch_size", type=int, default=128, help="Batch size for embedding.")
    parser.add_argument("--embedding_dim", type=int, default=256, help="Size of the embedding to store.")
    parser.add_argument("--precision", type=str, default="float32", help="Precision for the embeddings.")

    args = parser.parse_args()
    load_environment()

    # process_directory(
    #     input_dir=args.input_dir,
    #     permanent_file=args.output_file,
    #     working_file=args.working_file,
    #     metadata_file=args.metadata_file,
    #     device=args.device,
    #     batch_size=args.batch_size,
    #     embedding_dim=args.embedding_dim,
    #     precision=args.precision
    # )

    normalize_embeddings(
        input_file=args.output_file,
        output_file="../backend/embeddings.json"
    )
