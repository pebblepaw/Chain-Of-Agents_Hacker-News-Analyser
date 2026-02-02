# Brave search API wrapper for web search
# Docs: https://api.search.brave.com/app/documentation/web-search

import httpx
from typing import Optional 
from ..config import BRAVE_API_KEY, MAX_SEARCH_RESULTS

# should i add this to config instead *** 
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

def search_web(
    query: str,
    count: int = MAX_SEARCH_RESULTS,
    freshness: Optional[str] = None
    ) -> list[dict]:

    """
    Args: 
        query: search query string
        count: no. of results to return
        freshness: filter by time, pd, pw, pm, py (day, week, mth, yr)
    """

    if not BRAVE_API_KEY:
        return ValueError("Error: BRAVE_API_KEY not set.")
    
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }

    params = {
        "q": query,
        "count": min(count, 20), # the brave API max is 20 
    }

    if freshness: 
        params['freshness'] = freshness 

    response = httpx.get(
        BRAVE_SEARCH_URL,
        headers=headers,
        params=params,
        timeout=30.0
        )

    response.raise_for_status() 

    data = response.json()

    results = []
    for item in data.get("web",{}).get("results", []): 
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "description": item.get("description",""),
            "published": item.get("page_age","") # if avaialable
        })

    return results

if __name__ == "__main__":
    results = search_web("Artificial Intelligence", count=3)
    for i, res in enumerate(results, start=1):
        print(f"{i}. {res['title']}\n   URL: {res['url']}\n   Description: {res['description']}\n") 


