import os
import json
import dotenv
import numpy as np
from typing import List, Tuple, Set
from sentence_transformers import SentenceTransformer
from huggingface_hub import login
from tqdm import tqdm  # progress bar

MODEL_ID = "BAAI/bge-base-en-v1.5"

def load_environment() -> None:
    """
    Loads the environment variables from a .env file and logs into Hugging Face.
    Expects an environment variable HF_TOKEN to be set.
    """
    env = dotenv.dotenv_values()
    hf_token = env.get("HF_TOKEN", "")
    if not hf_token:
        raise ValueError("HF_TOKEN is not set in the environment file.")
    login(token=hf_token, add_to_git_credential=True)

def initialize_model(device: str = None) -> SentenceTransformer:
    """
    Initializes and returns the SentenceTransformer model on the specified device.
    """
    return SentenceTransformer(MODEL_ID, device=device)

def parse_file(file_path: str) -> Tuple[str, str]:
    """
    Reads the file at file_path as a plain string (including HTML tags)
    and returns a tuple of (file_path, content).
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    return file_path, content

def embed_content(
    model: SentenceTransformer,
    parsed_files: List[Tuple[str, str]],
    output_file: str,
    embedding_dim: int,
    batch_size: int,
    precision: str,
    device:str
) -> None:
    """
    Given a list of (file_path, content) tuples, computes embeddings in batch
    and appends each result as a JSON line to the output file.
    
    The embedding is truncated (if necessary) to embedding_dim and converted
    to the specified precision.
    """
    texts = [content for _, content in parsed_files]
    file_paths = [file_path for file_path, _ in parsed_files]
    
    # Compute embeddings in one batch
    embeddings = model.encode(
        texts,
        precision=precision, 
        batch_size=batch_size, 
        convert_to_numpy=True,
        device=device,
        normalize_embeddings=False
        )
    
    with open(output_file, 'a', encoding='utf-8') as wf:
        for fp, emb in zip(file_paths, embeddings):
            if len(emb) > embedding_dim:
                emb = emb[:embedding_dim]
            emb = np.array(emb, dtype=precision).tolist()
            record = {"url": fp, "embedding": emb}
            json.dump(record, wf, ensure_ascii=False)
            wf.write("\n")

def get_processed_files(output_file: str) -> Set[str]:
    """
    Reads the output file (if it exists) and returns a set of file paths that have already been processed.
    """
    processed: Set[str] = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        processed.add(record.get("url", ""))
                    except json.JSONDecodeError:
                        continue
    return processed

def process_directory(
    input_dir: str,
    output_file: str,
    device: str = "cuda",
    batch_size: int = 64,
    embedding_dim: int = 768,
    precision: str = "float32",
    num_cpu_cores: int = 7
) -> None:
    """
    Recursively walks through input_dir to find HTML files.
    Each unprocessed file (as determined by output_file) is read,
    embedded, and the result is appended to output_file.
    
    If device is 'cpu' and num_cpu_cores is specified, limits PyTorch to the specified number of CPU cores.
    """
    if device.lower() == "cpu" and num_cpu_cores is not None:
        import torch
        torch.set_num_threads(num_cpu_cores)
    model = initialize_model(device)
    processed_files = get_processed_files(output_file)
    
    # Gather unprocessed HTML files recursively
    unprocessed_files: List[str] = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".html"):
                full_path = os.path.join(root, file)
                if full_path in processed_files:
                    continue
                unprocessed_files.append(full_path)
    
    # Process files in batches with a progress bar
    for i in tqdm(range(0, len(unprocessed_files), batch_size), desc="Processing files"):
        batch_files = unprocessed_files[i:i + batch_size]
        parsed_files = [parse_file(fp) for fp in batch_files]
        embed_content(model, parsed_files, output_file, embedding_dim, batch_size, precision,device=device)

if __name__ == "__main__":
    load_environment()
    
    # Set your input directory and output file path accordingly.
    INPUT_DIR = "/path/to/project"
    OUTPUT_FILE = "/path/to/project"
    
    process_directory(INPUT_DIR, OUTPUT_FILE)
