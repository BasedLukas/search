import os
import random
import gzip
import json
from pprint import pprint

def inspect_random_wat(directory: str = "downloaded_wats") -> None:
    """
    Select a random .wat.gz file from 'directory', open it,
    and print out detailed information about the JSON structure.
    """
    wat_files = [f for f in os.listdir(directory) if f.endswith('.wat.gz')]
    if not wat_files:
        print("No .wat.gz files found in this directory.")
        return

    random_wat = random.choice(wat_files)
    wat_path = os.path.join(directory, random_wat)
    print(f"Selected random WAT file: {random_wat}")

    with gzip.open(wat_path, 'rt', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                record = json.loads(line)
                print(f"\nRecord {i+1}:")
                # Print top-level keys
                pprint(record.keys())
                # Drill down into the 'Envelope'
                envelope = record.get('Envelope', {})
                pprint(envelope.keys())
                # Explore WARC metadata and the target URI
                warc_metadata = envelope.get('WARC-Header-Metadata', {})
                pprint(warc_metadata)
                # Explore HTTP response metadata
                http_metadata = envelope.get('Payload-Metadata', {}).get('HTTP-Response-Metadata', {})
                pprint(http_metadata)
                # Stop after printing one record (or continue as needed)
                
            except json.JSONDecodeError:
                continue

inspect_random_wat()
