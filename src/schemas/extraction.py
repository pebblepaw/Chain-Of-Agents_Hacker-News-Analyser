'''
Defines the sturcture of data flowing thru agent chain 
'''

from pydantic import BaseModel, Field
from typing import List, Optional

class Entity(BaseModel): 
    # nodes in the knowledge graph

    # the ... indicates this Field is required when initializing an "Entity" object
    name: str = Field(..., description = "Name of the entity")
    entity_type: str = Field(..., description = "Type: Paper, Person, Technology, Article")
    properties: dict = Field(default_factory=dict, description = "Additional properties of the entity")

    class Config: 
        json_schema_extra = {
            "example": {
                "name": "LangChain",
                "entity_type": "Technology",
                "properties": {
                    "description": "A framework for developing applications powered by language models."}
            }
        }
    
class Relationship(BaseModel):
    # edges in the knowledge graph

    from_entity: str = Field(..., description = "Name of the source entity")
    to_entity: str = Field(..., description = "Name of the target entity")
    relationship_type: str = Field(..., description = "Type of relationship, e.g., 'authored', 'cites', 'implements','related_to'")
    properties: dict = Field(default_factory=dict, description = "Additional properties of the relationship")

    class Config: 
        json_schema_extra = {
            "example": {
                "from_entity": "LangChain",
                "to_entity": "LlamaIndex",
                "relationship_type": "related_to",
                "properties": {
                    "description": "Both are frameworks for building applications with language models.",
                    "year": 2023}
            }
        }

class Extraction(BaseModel):
    # the complete result after processing a document 

    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list, description = "List of ArXiv IDs or DOIs cited")  
    source_id: Optional[str] = Field(None, description = "ArXiv ID or URL of source document")

    def merge(self, other: "Extraction") -> "Extraction":

        # Merge another Extraction into this one

        existing_entity_names = {entity.name.lower() for entity in self.entities}
        existing_rel_keys = {
            (rel.from_entity.lower(), rel.to_entity.lower(), rel.relationship_type.lower())
            for rel in self.relationships
        }

        new_entities = [
            e for e in other.entities 
            if e.name.lower() not in existing_entity_names
        ]

        new_relationships = [
            r for r in other.relationships 
            if (r.from_entity.lower(), r.to_entity.lower(), r.relationship_type.lower()) not in existing_rel_keys
        ]

        new_references = [
            ref for ref in other.references 
            if ref not in self.references
        ]

        return Extraction(
            entities = self.entities + new_entities,
            relationships = self.relationships + new_relationships,
            references = self.references + new_references,
            source_id = self.source_id or other.source_id
        )
class ValidationResult(BaseModel): 

    # result of validating an extraction

    valid: bool = Field(..., description = "Whether the extraction passed validation")
    errors: List[str] = Field(default_factory=list, description = "List of validation error messages")
    suggestions: List[str] = Field(default_factory=list, description = "List of suggestions for fixing the extraction")

ENTITY_TYPES = ['Paper','Person','Technology','Article']
RELATIONSHIP_TYPES = {
    'Authored', # Person -> Paper
    'Cites', # Paper -> Paper
    'Implements', # Paper -> Technology
    'Extends', # Paper -> Paper
    'Discusses', # Article -> Paper/Technology
    'Related_To', # Technology -> Technology
    'Introduced' # Paper -> Technology
}