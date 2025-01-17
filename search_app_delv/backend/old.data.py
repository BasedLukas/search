import os
import re
import boto3
import requests
import pandas as pd
from warcio.archiveiterator import ArchiveIterator

def sanitize_url(url: str) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '_', url)

def get_warc_content(warc_file_url: str, record_offset: int) -> str:
    response = requests.get(warc_file_url, stream=True)
    response.raise_for_status()
    with response.raw as raw_stream:
        raw_stream.seek(int(record_offset))
        for record in ArchiveIterator(raw_stream):
            if record.rec_type == "response":
                return record.content_stream().read().decode("utf-8", errors="ignore")
    return ""



def main():
    database = "ccindex"
    table = "sampled_results_table"
    s3_output = "s3://example-bucket/temp/"
    session = boto3.Session(region_name="us-east-1")
    athena_client = session.client("athena")

    query = f"SELECT * FROM {table} LIMIT 100;"
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
        df.to_csv("results.csv", index=False)
        if not os.path.exists("pages"):
            os.makedirs("pages")
        base_url = "https://data.commoncrawl.org/"
        for idx, row in df.iterrows():
            warc_filename = row.get("warc_filename")
            warc_record_offset = row.get("warc_record_offset")
            url = row.get("url", "unknown_url")
            if not pd.isna(warc_filename) and not pd.isna(warc_record_offset):
                warc_file_url = f"{base_url}{warc_filename}"
                page_content = get_warc_content(warc_file_url, int(warc_record_offset))
                filename = sanitize_url(url) + ".html"
                filepath = os.path.join("pages", filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(page_content)
                print(f"Saved: {filepath}")
            else:
                print(f"Skipping row {idx}, missing WARC info.")
    else:
        print("Query failed with status:", status)

if __name__ == "__main__":
    main()
