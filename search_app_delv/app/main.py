import logging
import json
from flask import Flask, request, render_template
from backend.main import search

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)



@app.route('/')
def search_page():
    return render_template('index.html')

@app.route('/search')
def results_page():
    query = request.args.get('query')

    if not query:
        return render_template('index.html', n=0)

    # Perform the search and get stats
    search_results = search(query)
    my_results = search_results["results"]
    stats = search_results["stats"]

    return render_template(
        'results.html',
        query=query,
        my_results=my_results,
        stats=stats
    )
