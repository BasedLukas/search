import logging
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
    bing_results, my_results = search(query)

    return render_template(
        'results.html', 
        query=query, 
        engine1_results=bing_results,
        engine2_results=my_results
        )


