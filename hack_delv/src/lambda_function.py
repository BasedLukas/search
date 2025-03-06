import json
import logging
import os
import requests
from typing import Dict, Any
from src.process import process_results
# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function that processes search queries and returns results.
    
    Args:
        event: AWS Lambda event object containing the API Gateway request
        context: AWS Lambda context object
    
    Returns:
        Dict containing the response with status code and body
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        query_params = event.get('queryStringParameters', {})
        search_query = query_params.get('q', '')
        
        if not search_query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Search query parameter "q" is required'})
            }
        

        processed_results = process_results(search_query)
        logger.info(f"Successfully processed search query: {search_query}")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': processed_results
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making external API request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to fetch search results'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        } 