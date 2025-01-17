import os
import boto3
import requests
from requests.exceptions import RequestException

def download_wat_files(
    bucket_name: str = 'commoncrawl',
    prefix: str = 'crawl-data/CC-MAIN-2024-51/segments/',
    download_limit: int = 100,
    download_dir: str = "downloaded_wats"
) -> None:
    """Download up to 'download_limit' WAT files from the given prefix."""

    os.makedirs(download_dir, exist_ok=True)
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    # Discover WAT keys
    wat_keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wat.gz'):
                wat_keys.append(key)
            if len(wat_keys) >= download_limit:
                break
        if len(wat_keys) >= download_limit:
            break

    # Download
    for key in wat_keys:
        filename = os.path.basename(key)
        local_path = os.path.join(download_dir, filename)

        if os.path.exists(local_path):
            print(f"{filename} already exists, skipping.")
            continue

        wat_url = f"https://data.commoncrawl.org/{key}"
        print(f"Downloading {wat_url}")

        try:
            with requests.get(wat_url, stream=True) as response:
                response.raise_for_status()
                with open(local_path, "wb") as file_out:
                    for chunk in response.iter_content(chunk_size=8192):
                        file_out.write(chunk)
            print(f"Saved {local_path}")
        except RequestException as e:
            print(f"Failed to download {wat_url}: {e}")


def download_wet_files(
    bucket_name: str = 'commoncrawl',
    prefix: str = 'crawl-data/CC-MAIN-2024-51/segments/',
    download_limit: int = 100,
    download_dir: str = "downloaded_wets"
) -> None:
    """
    Download up to 'download_limit' WET files from the specified prefix
    and save them to the 'download_dir'.
    """
    os.makedirs(download_dir, exist_ok=True)
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    # Discover WET keys
    wet_keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wet.gz'):
                wet_keys.append(key)
            if len(wet_keys) >= download_limit:
                break
        if len(wet_keys) >= download_limit:
            break

    # Download WET files
    for key in wet_keys:
        filename = os.path.basename(key)
        local_path = os.path.join(download_dir, filename)

        if os.path.exists(local_path):
            print(f"{filename} already exists, skipping.")
            continue

        wet_url = f"https://data.commoncrawl.org/{key}"
        print(f"Downloading {wet_url}")

        try:
            with requests.get(wet_url, stream=True) as response:
                response.raise_for_status()
                with open(local_path, "wb") as file_out:
                    for chunk in response.iter_content(chunk_size=8192):
                        file_out.write(chunk)
            print(f"Saved {local_path}")
        except RequestException as e:
            print(f"Failed to download {wet_url}: {e}")


if __name__ == "__main__":
    download_wet_files()
