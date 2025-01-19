import requests
import dotenv
import logging
from typing import List, Optional
from dataclasses import dataclass

from custom_search_client import CustomSearchClient
from azure.core.credentials import AzureKeyCredential

from data.search import create_search_engine

log = logging.Logger(name="search")
env = dotenv.dotenv_values()
N_RESULTS = env.get("N_RESULTS")


@dataclass
class Result:
    title: str
    url: str
    snippet: str = ""
    text: str = ""

log.info("Loading search engine vectors...")
search_engine = create_search_engine("data/out.json")
log.info("Loaded vectors")


def get_bing(query:str):
    ENDPOINT = "https://api.bing.microsoft.com/v7.0/custom/search"
    SUBSCRIPTION_KEY = env.get("SUBSCRIPTION_KEY")
    CUSTOM_CONFIG = env.get("CUSTOM_CONFIG")
    client = CustomSearchClient(
        endpoint=ENDPOINT, 
        credential=AzureKeyCredential(SUBSCRIPTION_KEY)
    )
    result = client.custom_instance.search(
        query=query, 
        custom_config=CUSTOM_CONFIG,
        count=N_RESULTS
    )
    
    if not result or not result.web_pages or not result.web_pages.value:
        return []
    return [
        Result(
                title=page.name,
                url=page.url,
                snippet=page.snippet,
            )
        for page in result.web_pages.value
    ]

    
def get_my_results(query:str)->List[Result]:
    results  = search_engine(query)
    return [
        Result(
            title=result[0],
            url=result[0],
            snippet="snippet goes here")
        for result in results
    ]


def search(query:str)->List[dict]:
    bing_results = get_bing(query)
    my_results = get_my_results(query)
    return [bing_results, my_results]

