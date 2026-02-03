import json 
from src.schemas.extraction import Extraction, ENTITY_TYPES, RELATIONSHIP_TYPES

def build_extraction_prompt(chunk_text: str, running_extraction: Extraction) -> str: 

    # Builds upon the running extraction
    # Retruns the json string response from the LLM

    schema_hint = {
        "entities": [
            {"name": "string", "entity_type": "Paper|Person|Technology|Article", "properties": {}}
        ],
        "relationships": [
            {"from_entity": "string", "to_entity": "string", "relationship_type": "AUTHORED|CITES|IMPLEMENTS|EXTENDS|DISCUSSES|RELATES_TO|COMPARED_IN|INTRODUCED", "properties": {}}
        ],
        "references": ["arxiv:1234.5678", "doi:10.xxxx/xxxx"]
    }

    return f"""
    You are an information extraction agent for AI/ML research papers.

    Your task: extract entities and relationships from the given text chunk.
    You must build on the running extraction and avoid duplicates.

    Allowed entity types: {sorted(ENTITY_TYPES)}
    Allowed relationship types (UPPERCASE only): {sorted(RELATIONSHIP_TYPES)}

    IMPORTANT:
    - Use EXACT keys: from_entity, to_entity, relationship_type
    - Do NOT use subject/object/predicate keys
    - Return ONLY valid JSON, no extra text, no markdown
    - If nothing is found, return empty arrays

    Return **only valid JSON** in this format:
    {json.dumps(schema_hint, indent=2)}

    Running extraction so far:
    {running_extraction.model_dump_json(indent=2)}

    Text chunk:
    \"\"\"
    {chunk_text}
    \"\"\"
    """


def build_repair_prompt(bad_text: str) -> str:
    """Repair non-JSON model output into valid Extraction JSON."""
    schema_hint = {
        "entities": [
            {"name": "string", "entity_type": "Paper|Person|Technology|Article", "properties": {}}
        ],
        "relationships": [
            {"from_entity": "string", "to_entity": "string", "relationship_type": "AUTHORED|CITES|IMPLEMENTS|EXTENDS|DISCUSSES|RELATES_TO|COMPARED_IN|INTRODUCED", "properties": {}}
        ],
        "references": ["arxiv:1234.5678", "doi:10.xxxx/xxxx"]
    }

    return f"""
    Convert the following text into valid JSON matching this schema.
    Return ONLY JSON, no extra text, no markdown.

    Schema:
    {json.dumps(schema_hint, indent=2)}

    Text:
    \"\"\"
    {bad_text}
    \"\"\"
    """
