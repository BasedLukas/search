import logging
from flask import Flask, request, render_template, jsonify
from backend.main import search
from backend.logs import logger as log
from typing import Any

log.info("App init")
app = Flask(__name__)

@app.route('/')
def search_page() -> Any:
    return render_template('index.html', n=0)

@app.route('/search')
def results_page() -> Any:
    query = request.args.get('query')
    if not query:
        return render_template('index.html', n=0)
    # Get search results and stats from the backend.
    search_results = search(query)
    my_results = search_results["results"]
    stats = search_results["stats"]
    # Allow a query parameter "lines" to set how many lines to show by default (default is 3).
    default_lines = request.args.get('lines', 3, type=int)
    return render_template(
        'results.html',
        query=query,
        my_results=my_results,
        stats=stats,
        default_lines=default_lines
    )

@app.route("/api", methods=["POST"])
def api_endpoint():
    data = request.get_json(silent=True)
    query = data.get("query") if isinstance(data, dict) else None
    if not isinstance(query, str) or not query.strip():
        log.info("Error, no query provided")
        return jsonify({"error": "No query provided"}), 400

    results = search(query)["results"]
    if results:
        log.info(f"search result (truncated):{results[0].text[:50]}")
    return jsonify({f"result{i}": result.html for i, result in enumerate(results[:3])})

if __name__ == '__main__':
    app.run(debug=True)
