import requests
import dotenv
from typing import List, Optional
from dataclasses import dataclass

from custom_search_client import CustomSearchClient
from azure.core.credentials import AzureKeyCredential

env = dotenv.dotenv_values()
N_RESULTS = env.get("N_RESULTS")


@dataclass
class Result:
    title: str
    url: str
    snippet: str = ""
    text: str = ""


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

    
def get_my_results(bing_results:List[Result])->List[Result]:
    return bing_results


def search(query:str)->List[dict]:
    bing_results = get_bing(query)
    my_results = get_my_results(bing_results)
    return [bing_results, my_results]
