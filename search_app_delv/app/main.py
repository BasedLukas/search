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
    default_lines = int(request.args.get('lines', 3))
    return render_template(
        'results.html',
        query=query,
        my_results=my_results,
        stats=stats,
        default_lines=default_lines
    )

@app.route("/api", methods=["POST"])
def api_endpoint():
    data = request.get_json()
    query = data.get("query")
    if not query:
        log.info("Error, no query provided")
        return jsonify({"error": "No query provided"}), 400

    results = search(query)
    log.info(f"search result (truncated):{results.text[:50]}")
    return jsonify({
        "result0": results["results"][0].html,
        "result1": results["results"][1].html,
        "result2": results["results"][2].html,
    })

if __name__ == '__main__':
    app.run(debug=True)
