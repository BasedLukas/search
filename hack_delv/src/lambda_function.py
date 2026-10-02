import json
from typing import Any, Dict

from src.helpers import ApiError, api_response, logger
from src.process import process_query_request, process_url_request


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Dispatch search and URL requests from API Gateway."""
    try:
        query_params = event.get("queryStringParameters") or {}
        search_query = query_params.get("q", "")
        url = query_params.get("url", "")
        body = event.get("body")
        if body:
            body = json.loads(body) if isinstance(body, str) else body
            # The MCP client sends a JSON string inside a body field.
            if isinstance(body, dict) and "body" in body:
                body = json.loads(body["body"]) if isinstance(body["body"], str) else body["body"]
            if not isinstance(body, dict):
                return api_response(ApiError("Request body must be a JSON object", 400))
            search_query = body.get("query", search_query)
            url = body.get("url", url)
        if not search_query and not url:
            return api_response(ApiError('Either search query "q"/"query" or "url" is required', 400))
        if url:
            return api_response(process_url_request(url))
        return api_response(process_query_request(search_query))
    except ApiError as error:
        return api_response(error)
    except (ValueError, TypeError) as error:
        return api_response(ApiError("Invalid request", 400))
    except Exception:
        logger.exception("Unexpected search API error")
        return api_response(ApiError("Internal server error", 500))
