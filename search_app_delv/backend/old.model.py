import os
import re
import boto3
import requests
import pandas as pd
from warcio.archiveiterator import ArchiveIterator
import tempfile
import dotenv
from huggingface_hub import login
import torch
from sentence_transformers import SentenceTransformer

def sanitize_url(url: str) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '_', url)


def get_warc_content(warc_file_url: str, record_offset: int) -> str:
    """
    Fetch and return the text content of a WARC record.
    The WARC file is downloaded locally before accessing.
    """
    # Create a temporary file to store the WARC file
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        # Download the WARC file
        response = requests.get(warc_file_url, stream=True)
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
            temp_file.write(chunk)
        
        temp_file.flush()  # Ensure all content is written
        
        # Seek to the specified offset in the downloaded file
        temp_file.seek(record_offset)
        for record in ArchiveIterator(temp_file):
            if record.rec_type == "response":
                return record.content_stream().read().decode("utf-8", errors="ignore")
    return ""

def query_athena_and_save_csv(
    database: str,
    table: str,
    s3_output: str,
    region_name: str = "us-east-1",
    limit: int = 100,
    local_csv_path: str = "results.csv"
) -> pd.DataFrame:
    session = boto3.Session(region_name=region_name)
    athena_client = session.client("athena")

    query = f"SELECT * FROM {table} LIMIT {limit};"
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": s3_output},
    )
    query_execution_id = response["QueryExecutionId"]
    status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)["QueryExecution"]["Status"]["State"]

    while status in ["RUNNING", "QUEUED"]:
        status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)["QueryExecution"]["Status"]["State"]

    if status == "SUCCEEDED":
        csv_url = f"{s3_output}{query_execution_id}.csv"
        df = pd.read_csv(csv_url)
        df.to_csv(local_csv_path, index=False)
        return df
    else:
        raise RuntimeError(f"Query failed with status: {status}")

def fetch_warc_files_from_csv(
    df: pd.DataFrame,
    base_url: str = "https://data.commoncrawl.org/",
    pages_dir: str = "pages"
) -> None:
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)
    for _, row in df.iterrows():
        warc_filename = row.get("warc_filename")
        warc_record_offset = row.get("warc_record_offset")
        url = row.get("url", "unknown_url")
        if pd.notna(warc_filename) and pd.notna(warc_record_offset):
            warc_file_url = f"{base_url}{warc_filename}"
            page_content = get_warc_content(warc_file_url, int(warc_record_offset))
            filename = sanitize_url(url) + ".html"
            filepath = os.path.join(pages_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(page_content)
        else:
            print(f"Skipping row with missing WARC info for URL: {url}")

def fetch_and_embed_warc_with_matryoshka(
    warc_filename: str,
    warc_record_offset: int,
    base_url: str = "https://data.commoncrawl.org/"
) -> dict[int, list[float]]:
    """
    1) Fetches WARC content.
    2) Logs in to Hugging Face Hub (.env with HF_TOKEN).
    3) Loads a model.
    4) Generates matryoshka embeddings (truncated at multiple dimensions).
    5) Returns a dict of dimension -> embedding.
    """
    warc_file_url = f"{base_url}{warc_filename}"
    warc_content = get_warc_content(warc_file_url, warc_record_offset=warc_record_offset)

    env = dotenv.dotenv_values()
    hf_token = env.get("HF_TOKEN", "")
    if hf_token:
        login(token=hf_token, add_to_git_credential=True)

    model_id = "BAAI/bge-base-en-v1.5"
    matryoshka_dimensions = [768, 512, 256, 128, 64]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_id, device=device)

    # Encode returns a 2D array [batch, embedding_dim], so we take the first row
    embedding = model.encode([warc_content], show_progress_bar=False)[0]
    embedding_dict = {}
    for dim in matryoshka_dimensions:
        embedding_dict[dim] = embedding[:dim].tolist()

    return embedding_dict

def main():
    database = "ccindex"
    table = "sampled_results_table"
    s3_output = "s3://example-bucket/temp/"
    df = query_athena_and_save_csv(
        database=database,
        table=table,
        s3_output=s3_output,
        limit=100,
        local_csv_path="results.csv"
    )

    # Optionally fetch WARC files (if you still need them on disk):
    fetch_warc_files_from_csv(
        df,
        base_url="https://data.commoncrawl.org/",
        pages_dir="pages"
    )

    # Show how you could embed a single file
    example_row = df.iloc[0]
    if pd.notna(example_row["warc_filename"]) and pd.notna(example_row["warc_record_offset"]):
        embedding_dict = fetch_and_embed_warc_with_matryoshka(
            warc_filename=example_row["warc_filename"],
            warc_record_offset=int(example_row["warc_record_offset"]),
            base_url="https://data.commoncrawl.org/"
        )
        print("Matryoshka embeddings for example row:")
        print(embedding_dict)

if __name__ == "__main__":
    main()
