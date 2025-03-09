# src/helpers.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Optional
import os
import re
import logging
import json

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

@dataclass
class SearchResult:
    """Represents a search result with URL, title, and description."""
    url: str
    title: str
    description: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description
        }

@dataclass
class ApiError:
    """Represents an API error response."""
    message: str
    status_code: int = 500
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for JSON response."""
        return {"error": self.message}

def valid_query(query: str) -> bool:
    """Validate that query exists and is max 400 chars and 50 words."""
    if not query:
        return False
    if len(query) > 400:
        return False
    if len(query.split()) > 50:
        return False
    return True

def valid_url(url: str) -> bool:
    """Validate that url exists and is a valid URL format."""
    if not url:
        return False
    # Basic URL validation - should start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    return True

def api_response(data: Union[Dict[str, Any], ApiError], status_code: int = 200) -> Dict[str, Any]:
    """Create a standard API Gateway response object."""
    if isinstance(data, ApiError):
        status_code = data.status_code
        body = data.to_dict()
    else:
        body = data
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def extract_url_numbers(response_text: str, max_urls: int) -> List[int]:
    """Extract URL numbers from Groq response text and validate them."""
    url_numbers = re.findall(r'<url>(\d+)</url>', response_text)
    
    # Convert to integers and validate
    valid_indices = []
    for num_str in url_numbers:
        try:
            num = int(num_str)
            if 1 <= num <= max_urls:  # 1-based indexing in the response
                valid_indices.append(num - 1)  # Convert to 0-based index
        except ValueError:
            continue
            
    return valid_indices