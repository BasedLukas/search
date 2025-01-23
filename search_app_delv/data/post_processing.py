import faiss
import numpy as np
import json

# Paths for the embedding file and output index file
jsonl_file = "out.json"
index_file = "../backend/index.bin"
url_file = "../backend/url_mapping.json"

# Parameters
embedding_dim = 256  # Dimension of your embeddings
m = 16  # Number of sub-vectors for PQ (embedding_dim must be divisible by m)
batch_size = 100000  # Number of vectors to process in a batch

# Create a Product Quantization (PQ) index
index = faiss.IndexPQ(embedding_dim, m, 8)  # 8 bits per sub-vector

# Save URLs in a list for mapping
url_mapping = []

# Collect a subset of embeddings for training
print("Training the index...")
training_samples = []
with open(jsonl_file, "r") as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        embedding = np.array(data["embedding"], dtype=np.float32)
        training_samples.append(embedding)
        if len(training_samples) >= batch_size:  # Use the first batch for training
            break
training_samples = np.vstack(training_samples)  # Combine into a single NumPy array
index.train(training_samples)  # Train the index
print("Index training complete.")

# Add embeddings to the index incrementally and save URLs
print("Adding embeddings to the index...")
with open(jsonl_file, "r") as f:
    batch = []
    for line in f:
        data = json.loads(line)
        embedding = np.array(data["embedding"], dtype=np.float32)
        batch.append(embedding)
        url_mapping.append(data["url"])  # Save URL
        if len(batch) >= batch_size:
            batch = np.vstack(batch)  # Stack batch into a single NumPy array
            index.add(batch)  # Add batch to the index
            batch = []  # Reset batch
    if batch:  # Add remaining embeddings
        batch = np.vstack(batch)
        index.add(batch)

print("All embeddings added to the index.")

# Save the index and URL mapping to files
faiss.write_index(index, index_file)
with open(url_file, "w") as f:
    json.dump(url_mapping, f)

print(f"Index saved to {index_file}.")
print(f"URL mapping saved to {url_file}.")
