"""
HackerNews Algolia API wrapper
Docs: https://hn.algolia.com/api
"""

import httpx
from typing import Optional
from dataclasses import dataclass

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

@dataclass
class HNArticle:
    hn_id: str
    title: str
    url: Optional[str]
    author: str
    points: int
    num_comments: int
    created_at: str
    
    def to_dict(self) -> dict:
        return {
            "hn_id": self.hn_id,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "points": self.points,
            "num_comments": self.num_comments,
            "created_at": self.created_at,
            "hn_url": f"https://news.ycombinator.com/item?id={self.hn_id}"
        }


def search_hackernews(
    query: str,
    max_results: int = 5,
    tags: str = "story", # filter by story online, also hv comment, poll, show_hn, ask_hn on the website
) -> list[HNArticle]:
   
    params = {
        "query": query,
        "tags": tags,
        "hitsPerPage": max_results,
    }
    
    response = httpx.get(HN_SEARCH_URL, params=params, timeout=30.0)
    response.raise_for_status()
    
    data = response.json()
    articles = []
    
    for hit in data.get("hits", []):
        articles.append(HNArticle(
            hn_id=str(hit.get("objectID", "")),
            title=hit.get("title", ""),
            url=hit.get("url"),  
            author=hit.get("author", ""),
            points=hit.get("points", 0),
            num_comments=hit.get("num_comments", 0),
            created_at=hit.get("created_at", ""),
        ))
    
    return articles

if __name__ == "__main__":
    print("Searching HackerNews...")
    articles = search_hackernews("GPT-4 agents", max_results=3)
    for a in articles:
        print(f"\n{a.title}")
        print(f"  Points: {a.points} | Comments: {a.num_comments}")
        print(f"  URL: {a.url or 'N/A'}")