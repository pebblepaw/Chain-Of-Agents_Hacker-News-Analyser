import json
import re

from src.llm.provider import get_llm
from src.schemas.extraction import Extraction 
from src.tools.pdf_processor import process_arxiv_pdf
from src.prompts.extraction import build_extraction_prompt, build_repair_prompt

def process_paper(arxiv_id: str) -> Extraction: 
    
    llm = get_llm()

    chunks = process_arxiv_pdf(arxiv_id)

    # Define empty extraction first 
    # This won't work, cause "..." in Field means must be filled
    running_extraction = Extraction(source_id = arxiv_id) 

    for chunk in chunks: 
        prompt = build_extraction_prompt(
            chunk_text=chunk.text,
            running_extraction=running_extraction
        )

        response = llm.invoke(prompt)
        response_text = getattr(response, "content", "") or ""

        # Parse the response into an Extraction dataclass
        try:
            parsed = _parse_llm_json(response_text)
        except ValueError:
            repair_prompt = build_repair_prompt(response_text)
            repair_response = llm.invoke(repair_prompt)
            repair_text = getattr(repair_response, "content", "") or ""
            parsed = _parse_llm_json(repair_text)
        normalized = _normalize_extraction_dict(parsed)
        new_extraction = Extraction.model_validate(normalized)

        # Merge with running extraction
        # This might be redundant, since the LLM already edits off of 
        # previous extraction *** 
        running_extraction = running_extraction.merge(new_extraction)

        running_extraction = _filter_top_entities(running_extraction, max_per_type=20)

    return running_extraction

def _parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM response, tolerating extra text."""
    if not text or not text.strip():
        raise ValueError("LLM returned empty response text. Check Ollama server/model.")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: extract first JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"LLM response was not valid JSON. Response start: {text[:300]!r}")
        return json.loads(match.group(0))


def _normalize_extraction_dict(data: dict) -> dict:
    """Normalize keys and relationship schema to match Extraction model."""
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    references = data.get("references", [])

    normalized_rels = []
    for rel in relationships:
        # Support alternative keys from LLMs
        from_entity = rel.get("from_entity") or rel.get("subject") or rel.get("from")
        to_entity = rel.get("to_entity") or rel.get("object") or rel.get("to")
        relationship_type = rel.get("relationship_type") or rel.get("relation") or rel.get("predicate")

        if relationship_type:
            relationship_type = relationship_type.upper()

        normalized_rels.append({
            "from_entity": from_entity,
            "to_entity": to_entity,
            "relationship_type": relationship_type,
            "properties": rel.get("properties", {})
        })

    return {
        "entities": entities,
        "relationships": normalized_rels,
        "references": references,
        "source_id": data.get("source_id")
    }


## Maybe at a later date we can count the number of counts/mentions of each entity
# and use that as a filter? ***
def _filter_top_entities(extraction: Extraction, max_per_type: int = 20) -> Extraction:
    """
    Keep only top-N entities by simple heuristics.
    For now: limit Technology to top 20.
    """

    # Basic quality filter for noisy tokens
    def is_valid_name(name: str) -> bool:
        name = name.strip()
        if len(name) < 4:
            return False
        # if any(ch.isdigit() for ch in name) and len(name) < 6:
        #     return False
        if name.lower() in {"document", "article", "paper"}:
            return False
        # if name.isupper() and len(name) <= 4:
        #     return False
        return True

    # Only filter Technology for now
    tech_entities = [e for e in extraction.entities if e.entity_type == "Technology"]
    other_entities = [e for e in extraction.entities if e.entity_type != "Technology"]

    # Score by name length (simple proxy for significance)
    tech_entities = [e for e in tech_entities if is_valid_name(e.name)]
    tech_entities.sort(key=lambda e: len(e.name), reverse=True)

    # Keep top N
    tech_entities = tech_entities[:max_per_type]

    extraction.entities = other_entities + tech_entities
    return extraction


