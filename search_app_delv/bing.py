import dotenv
import requests
from pprint import pprint
from requests import HTTPError
import json
from custom_search_client import CustomSearchClient
from azure.core.credentials import AzureKeyCredential

env = dotenv.dotenv_values()

ENDPOINT = "https://api.bing.microsoft.com/v7.0/custom/search"
SUBSCRIPTION_KEY = env.get("SUBSCRIPTION_KEY")
CUSTOM_CONFIG = env.get("CUSTOM_CONFIG")

client = CustomSearchClient(
    endpoint=ENDPOINT, 
    credential=AzureKeyCredential(SUBSCRIPTION_KEY)
)

def custom_search_web_page_result_lookup(query:str):
    """CustomSearch.

    This will look up a single query (Xbox) and print out name and url for first web result.
    """


    try:
        web_data = client.custom_instance.search(query=query, custom_config=CUSTOM_CONFIG)
        if web_data.web_pages.value:
            first_web_result = web_data.web_pages.value[0]
            print("Web Pages result count: {}".format(len(web_data.web_pages.value)))
            print("First Web Page name: {}".format(first_web_result.name))
            print("First Web Page url: {}".format(first_web_result.url))
            print("First Web Page snippet: {}".format(first_web_result.snippet))
            print("First Web Page text: {}".format(first_web_result.text))
            for attr in dir(first_web_result):
                print(attr)
                print(eval("first_web_result."+attr))
                print()
        else:
            print("Didn't see any web data..")
    except Exception as err:
        print("Encountered exception. {}".format(err))

def custom_search_basic(
    query,
    subscription_key,
    custom_config_id,
    auth_header_name="Ocp-Apim-Subscription-Key",
    mkt="en-us",
):
    """Bing Custom Search Basic REST call

    This sample uses the Bing Custom Search API to search for a query topic and
    get back user-controlled web page results.
    Documentation: https://example.invalid

    May throw HTTPError in case of invalid parameters or a server error.

    Args:
        subscription_key (str): Azure subscription key of Bing Custom Search service
        custom_config_id (str): Custom Configuation ID obtained from the portal
        auth_header_name (str): Name of the authorization header
        query (str): Query to search for
        mkt (str): Market to search in
    """
    # Construct a request
    endpoint = "https://api.bing.microsoft.com/v7.0/custom/search"
    params = {"q": query, "mkt": mkt, "customconfig": custom_config_id}
    headers = {auth_header_name: subscription_key}

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response
    except HTTPError as ex:
        print(ex)
        print("++The above exception was thrown and handled succesfully++")
        return response


response = custom_search_basic("Microsoft", SUBSCRIPTION_KEY, CUSTOM_CONFIG)
print("\nResponse Headers:\n")
pprint(dict(response.headers))

print("\nJSON Response:\n")
print(json.dumps(response.json(), indent=4))
