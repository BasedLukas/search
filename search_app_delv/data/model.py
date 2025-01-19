import os
import gzip
import dotenv
import json
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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process WET files and embed content with restart capability.")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing WET files.")
    parser.add_argument("--output_file", type=str, required=True, help="Permanent JSON lines file.")
    parser.add_argument("--working_file", type=str, default="temp.json", help="Working JSON lines file.")
    parser.add_argument("--metadata_file", type=str, default="processing_metadata", help="File listing processed WET files.")
    parser.add_argument("--device", type=str, default="cuda", help="Device to run the model on (e.g., 'cpu', 'cuda').")
    parser.add_argument("--batch_size", type=int, default=128, help="Batch size for embedding.")
    parser.add_argument("--embedding_dim", type=int, default=256, help="Size of the embedding to store.")
    parser.add_argument("--precision", type=str, default="float32", help="Precision for the embeddings.")

    args = parser.parse_args()
    load_environment()

    process_directory(
        input_dir=args.input_dir,
        permanent_file=args.output_file,
        working_file=args.working_file,
        metadata_file=args.metadata_file,
        device=args.device,
        batch_size=args.batch_size,
        embedding_dim=args.embedding_dim,
        precision=args.precision
    )
