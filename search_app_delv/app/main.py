import logging
import json
import uuid
from flask import Flask, request, render_template
from backend.main import search
from backend.logs import logger as log
from typing import Any, Dict

log.info("App init")
app = Flask(__name__)

# Global cache to store HTML content for each result by unique ID.
html_cache: Dict[str, str] = {}

@app.route('/')
def search_page() -> Any:
    """Render the search page."""
    return render_template('index.html', n=0)

@app.route('/search')
def results_page() -> Any:
    """Perform search using the query and render the results page."""
    query = request.args.get('query')
    if not query:
        return render_template('index.html', n=0)
    # Get search results and stats from the backend.
    search_results = search(query)
    my_results = search_results["results"]
    stats = search_results["stats"]

    # For each result, generate a unique ID and store its HTML content.
    for result in my_results:
        unique_id = str(uuid.uuid4())
        html_cache[unique_id] = result.html
        # Add a new attribute to the result for the template.
        result.html_id = unique_id

    return render_template(
        'results.html',
        query=query,
        my_results=my_results,
        stats=stats
    )

@app.route('/view_html')
def view_html() -> Any:
    """
    Render a template that displays the HTML content of a search result.
    The HTML content is retrieved from the server-side cache using an ID.
    """
    result_id = request.args.get('id')
    if not result_id:
        return "No result ID provided.", 400
    html_content = html_cache.get(result_id)
    if not html_content:
        return "HTML content not found.", 404
    return render_template('view_html.html', html_content=html_content)

if __name__ == '__main__':
    app.run(debug=True)
