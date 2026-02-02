"""
ArXiv API wrapper
Docs: https://info.arxiv.org/help/api/
"""

import httpx
import xml.etree.ElementTree as ET
from typing import Optional
from dataclasses import dataclass

ARXIV_API_URL = "https://export.arxiv.org/api/query"

@dataclass
class ArxivPaper: 
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    published: str
    updated: str
    pdf_url: str
    categories: list[str]

    def to_dict(self) -> dict: 
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "published": self.published,
            "updated": self.updated,
            "pdf_url": self.pdf_url,
            "categories": self.categories
        }
    
def search_arxiv(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",  # or "lastUpdatedDate", "submittedDate"
    sort_order: str = "descending"
    ) -> list[ArxivPaper]:

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by, 
        "sortOrder": sort_order, 
    }

    response = httpx.get(ARXIV_API_URL, params=params, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    return _parse_arxiv_response(response.text)

def get_paper_metadata(arxiv_id: str) -> Optional[ArxivPaper]:
   
    arxiv_id = arxiv_id.replace("arxiv:","").strip()

    params = {
            "id_list" : arxiv_id, 
            "max_results": 1
    }

    response = httpx.get(ARXIV_API_URL, params=params, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    papers = _parse_arxiv_response(response.text)
    return papers[0] if papers else None

def _parse_arxiv_response(xml_text: str) -> list[ArxivPaper]:

    # name space 
    # atom is a web format, XML containing metadata & entries
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom"
    }

    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", ns):
        
        # get arxiv ID from id URL 
        id_url = entry.find("atom:id", ns).text
        arxiv_id = id_url.split("/abs/")[-1]

        authors = [
            author.find("atom:name", ns).text 
            for author in entry.findall("atom:author", ns)
        ]

        categories = [
            category.get("term","") 
            for category in entry.findall("atom:category", ns)
        ]

        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href","")
                break

        abstract = entry.find("atom:summary", ns).text
        abstract = " ".join(abstract.split()) if abstract else ""

        title = entry.find("atom:title", ns).text
        title = " ".join(title.split()) if title else ""

        papers.append(ArxivPaper(
            arxiv_id =  arxiv_id,
            title = title,
            abstract = abstract,
            authors = authors,
            published = entry.find("atom:published", ns).text,
            updated = entry.find("atom:updated", ns).text,
            pdf_url = pdf_url,
            categories = categories
        ))

    return papers

# Quick test
if __name__ == "__main__":
    print("Searching ArXiv...")
    papers = search_arxiv("Attention is all you need", max_results=2)
    for p in papers:
        print(f"\n{p.title}")
        print(f"  ID: {p.arxiv_id}")
        print(f"  Authors: {', '.join(p.authors[:3])}...")
        print(f"  PDF: {p.pdf_url}")






