# GetDelv web retrieval API

Search technical documentation with Brave, rank candidate URLs with Groq, and extract page content through an AWS Lambda API.

- [src/process.py](src/process.py): search, ranking and HTML extraction.
- [src/lambda_function.py](src/lambda_function.py): API Gateway request handling.
- [src/parse.py](src/parse.py), [src/parse2.py](src/parse2.py) and [src/clean_html_to_create_selectors.py](src/clean_html_to_create_selectors.py): standalone HTML parsers.

GET requests accept `q` or `url`; POST bodies accept `query` or `url`. A JSON-string `body` wrapper is also supported. URL takes precedence when both are supplied. Search responses contain `processed_content`, `top_result` and `other_results`; URL responses contain `processed_content` and `source_url`.

Requires Python 3.12+. Run `uv sync` in this directory and configure `BRAVE_API_KEY` and `GROQ_API_KEY` in the runtime environment. `BRAVE_GOGGLES_URL` is optional. Build with `docker build -t search-api-lambda .`; the handler is `src.lambda_function.lambda_handler`. The deployment script uses `ECR_REPO` and optional `AWS_REGION`; update Lambda to the pushed image.

[test/test_api.py](test/test_api.py) sends requests to `DELV_API_ENDPOINT` using `MY_API_KEY`. Parser scripts take a URL argument; `parse2.py` also needs `--selectors PATH` for your CSS-selector configuration. `parse.py` writes `output.xml`; the HTML cleaner writes `cleaned_<domain>.html`.
