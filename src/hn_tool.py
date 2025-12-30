import httpx
from datetime import datetime
from typing import Optional

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"

def search_hn_stories(
    query: str,
    limit: int = 10) -> str:

    with httpx.Client() as client: 
        response = client.get(
            HN_SEARCH_URL,
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": limit
            }
        )
    
        if response.status_code != 200:
            return f"Error: API unable to fetch stories. Status code {response.status_code}"
        
        data = response.json()
    results = []
    results.append(f"=== Hacker News Search Results for '{query}' ===")
    results.append(f"Found {data.get('nbHits', 0)} total results. Showing top {limit}:\n")
    
    for i, hit in enumerate(data.get("hits", []), start=1):
        title = hit.get("title", "No Title")
        url = hit.get("url", "No URL")
        points = hit.get("points", 0)
        author = hit.get("author", "Unknown Author")
        num_comments = hit.get("num_comments", 0)
        created_at = hit.get("created_at", "Unknown Date")
        story_id = hit.get("objectID", "")
        url = hit.get("url",f"https://news.ycombinator.com/item?id={story_id}")

        results.append(f"{i}. {title}")
        results.append(f"   Points: {points} | Comments: {num_comments} | Author: {author}")
        results.append(f"   Date: {created_at}")
        results.append(f"   URL: {url}")
        # results.append(f"_all results: {data.get('hits')[0].get('created_at')}") ## debugging line
        results.append("")  # Blank line for readability

    return "\n".join(results)

def search_hn_by_date_range(
        query:str,
        start_date: str,
        end_date: str,
        limit: int = 15) -> str:

    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    except ValueError as e: 
        return f"invalid date format. Use YYYY-MM-DD. Details: {str(e)}"

    numeric_filtres = f"created_at_i>={start_ts},created_at_i<={end_ts}"

    with httpx.Client() as client: 
        response = client.get(
            HN_SEARCH_BY_DATE_URL,
            params={
                "query": query, 
                "tags": "story",
                "numericFilters": numeric_filtres,
                "hitsPerPage": limit
            }
        )
    
        if response.status_code != 200:
            return f"Error: API unable to fetch stories. Status code {response.status_code}"
        
        data = response.json()

    results = []
    results.append(f"=== Hacker News Search Results for '{query}' from {start_date} to {end_date} ===")
    results.append(f"Found {data.get('nbHits', 0)} total results. Showing top {limit}:\n")

    for i, hit in enumerate(data.get("hits", []), start=1):
        title = hit.get("title", "No Title")
        points = hit.get("points", 0)
        num_comments = hit.get("num_comments", 0)
        created_at = hit.get("created_at", "Unknown Date")

        # url = hit.get("url", "No URL")
        # author = hit.get("author", "Unknown Author")
        # story_id = hit.get("objectID", "")
        # url = hit.get("url",f"https://news.ycombinator.com/item?id={story_id}") 
        
        results.append(f"{i}. {title}")
        results.append(f"   Points: {points} | Comments: {num_comments} | Date: {created_at}")
        # results.append("   Date: {created_at}")
        # results.append(f"   URL: {url}")
        results.append("")  # Blank line for readability

    if not data.get("hits"):
        results.append("No stories found in the specified date range.")
    return "\n".join(results)

def get_hn_comments(story_id: str, limit: int = 10) -> str:
    # HN_ITEM_URL = "https://hn.algolia.com/api/v1/items/"

    with httpx.Client() as client: 
        response = client.get(
            HN_SEARCH_URL,
            params={
                "tags": f"comment,story_{story_id}",
                "hitsPerPage": limit
            }
        )
    
        if response.status_code != 200:
            return f"Error: API unable to fetch comments. Status code {response.status_code}"
        
        data = response.json()

    # comments = data.get("children", [])
    results = []
    results.append(f"=== Top {limit} Comments for Story ID {story_id} ===\n")

    for i, comment in enumerate(data.get("hits", []), start=1):

        author = comment.get("author", "Unknown Author")
        text = comment.get("text", "[No Text]").replace("\n", " ")
        text = text[:500]
        # created_at = comment.get("created_at", "Unknown Date")

        results.append(f"{i}. Author: {author}: {text}")
        # results.append(f"   Comment: {text}")
        results.append("")  # Blank line for readability

    return "\n".join(results)

if __name__ == '__main__': 
    print("\n"+"="*60)
    print("Hacker News Search Tool Test")
    print("\n"+"="*60)

    print("\nTest 1: Search for 'LLM'\n")
    result = search_hn_stories("LLM", limit=5)
    print(result)

    print("\nTest 2: Search for 'GPT' in Q1 2024--")
    result = search_hn_by_date_range("GPT", "2024-01-01", "2024-03-31", limit=5)
    print(result)

    print("\nTest 3: Search for 'GPT' in Q4 2024--")
    result = search_hn_by_date_range("GPT", "2024-10-01", "2024-12-31", limit=5)
    print(result)

    print("\nTest 4: Get comments for top story from above\n")
    result = get_hn_comments("53612345", limit=5)
    print(result)

    print("\n"+"="*60)
    print("End of Hacker News Search Tool Test")
    print("\n"+"="*60)