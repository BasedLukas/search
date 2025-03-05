# Search Delv API

A FastAPI-based search service that provides an endpoint for searching documentation and other resources.


## Running the Service

Start the FastAPI server:
```bash
python src/main.py
```

The server will start running on `http://localhost:8000`.

## API Usage

The service exposes a single POST endpoint at `/search` that accepts search queries and returns text responses.

### Example Request

Here's a Python function you can use to make requests to the endpoint:

```python
import requests

API_ENDPOINT = "http://localhost:8000/search"

def search_delv(search_query: str) -> dict:
    """
    Search for coding docs, bug reports, issues, API references, get started guides, etc.
    Use this when interacting with any external library, or when you need to find information
    about a specific function, class, or concept.
    
    Args:
        search_query (str): The search query string
        
    Returns:
        dict: JSON response containing the search result text
    """
    response = requests.post(API_ENDPOINT, json={"search_query": search_query})
    return response.json()

# Example usage
results = search_delv("how to use pandas")
print(results["text"])
```

```bash
➜  ~ curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"search_query": "hello"}'
```

### Response Format

The API returns a JSON response in the following format:

```json
{
    "text": "This is the search result text..."
}
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`