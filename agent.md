# Agentic Research Dashboard - Implementation Plan

## Project Overview
**Goal**: Build an agentic search dashboard for AI/ML research that extracts knowledge from papers, articles, and discussions into a Neo4j knowledge graph with interactive visualization.

**Key Demo Feature**: Chain of Agents processing PDFs with iterative refinement.

---

## Architecture

```
User Query → Orchestrator → Searcher → [Paper Agents (sequential per chunk)] → Validator → Synthesizer → Neo4j → Streamlit UI
```

---

## Phase 1: Foundation

### 1.1 Schemas (`src/schemas/extraction.py`)
- [ ] `Entity` model (name, type, properties)
- [ ] `Relationship` model (from, to, type, properties)
- [ ] `Extraction` model (entities, relationships, references)
- [ ] `ValidationResult` model (valid, errors, suggestions)

### 1.2 Configuration (`src/config.py`)
- [ ] Load .env variables
- [ ] LLM provider switch (ollama/gemini)
- [ ] Model settings per provider
- [ ] Neo4j connection config

### 1.3 LLM Abstraction (`src/llm/provider.py`)
- [ ] `get_llm()` function returns configured LLM
- [ ] Ollama integration (default: llama3 or mistral)
- [ ] Gemini integration (optional)
- [ ] Consistent interface for both

**Test**: Call `get_llm().invoke("Hello")` with both providers

---

## Phase 2: MCP Server & Tools

### 2.1 Neo4j MCP Server (`src/neo4j_server.py`)
- [ ] `create_entity` tool
- [ ] `create_relationship` tool
- [ ] `search_graph` tool
- [ ] `get_entity_context` tool
- [ ] `merge_entity` tool (create or update)
- [ ] `clear_graph` tool

**Test**: Run server, call each tool via MCP client

### 2.2 External API Tools (`src/tools/`)
- [ ] `brave_search.py` - search web for articles
- [ ] `arxiv_search.py` - search papers, get metadata
- [ ] `arxiv_pdf.py` - download and extract PDF text
- [ ] `hn_search.py` - search HackerNews articles

**Test**: Each tool returns expected format

---

## Phase 3: PDF Processing

### 3.1 PDF Chunker (`src/tools/pdf_processor.py`)
- [ ] Download PDF from ArXiv URL
- [ ] Extract text from PDF (use `pymupdf` or `pdfplumber`)
- [ ] Split into chunks (by pages or token count)
- [ ] Return list of chunks with metadata

**Test**: Process sample ArXiv PDF, verify chunks

### 3.2 Chunk Extraction Prompt (`src/prompts/extraction.py`)
- [ ] System prompt for entity/relationship extraction
- [ ] Include extraction schema in prompt
- [ ] Include "running extraction" context
- [ ] Output format: JSON matching Extraction schema

---

## Phase 4: Agents (LangGraph)

### 4.1 Searcher Agent (`src/agents/searcher.py`)
- [ ] Takes user query
- [ ] Calls brave_search, arxiv_search, hn_search
- [ ] Checks existing graph for known entities
- [ ] Returns ranked list of sources to process

### 4.2 Paper Processor Agent (`src/agents/paper_processor.py`)
- [ ] Takes one paper (PDF URL or content)
- [ ] Chunks the paper
- [ ] Sequentially processes each chunk (Chain of Agents)
- [ ] Each iteration: chunk + running_extraction → updated_extraction
- [ ] Returns final accumulated Extraction

### 4.3 Validator Agent (`src/agents/validator.py`)
- [ ] Takes Extraction JSON
- [ ] Checks schema validity
- [ ] Checks entity name consistency
- [ ] Checks relationship types allowed
- [ ] If invalid: returns feedback for re-extraction
- [ ] Max 2 retry attempts

### 4.4 Synthesizer Agent (`src/agents/synthesizer.py`)
- [ ] Takes validated Extraction
- [ ] Calls Neo4j MCP tools to store
- [ ] Merges with existing graph (deduplication)
- [ ] Generates human-readable summary
- [ ] Returns summary + graph stats

---

## Phase 5: Orchestration

### 5.1 Workflow Graph (`src/graph/workflow.py`)
- [ ] Define LangGraph StateGraph
- [ ] Nodes: searcher, paper_processor, validator, synthesizer
- [ ] Edges: conditional routing (valid/invalid)
- [ ] Parallel paper processing (multiple papers)
- [ ] Sequential chunk processing (within each paper)

### 5.2 Orchestrator (`src/graph/orchestrator.py`)
- [ ] Entry point for queries
- [ ] Manages workflow execution
- [ ] Handles errors/retries
- [ ] Returns final result to UI

**Test**: End-to-end query → graph storage → summary

---

## Phase 6: Streamlit UI

### 6.1 Main App (`app.py`)
- [ ] Search input box
- [ ] Provider selector (Ollama/Gemini)
- [ ] Processing status/progress
- [ ] Agent activity log (show chain execution)

### 6.2 Graph Visualization
- [ ] `streamlit-agraph` integration
- [ ] Node colors by type (Paper=blue, Person=green, Tech=orange)
- [ ] Click node → show details sidebar
- [ ] Expand node → show connections

### 6.3 Results Panel
- [ ] Summary text from Synthesizer
- [ ] Source links (ArXiv, HN, web)
- [ ] "Added X entities, Y relationships" stats

---

## Tests

### Unit Tests
- [ ] Schema validation
- [ ] Each tool function
- [ ] LLM provider switching

### Integration Tests
- [ ] MCP server connection
- [ ] Neo4j operations
- [ ] Full agent chain (mock LLM)

### End-to-End Tests
- [ ] Query → Search → Extract → Validate → Store → Display
- [ ] Test with real ArXiv paper

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Extraction accuracy | >80% entities correct | Manual review of 5 papers |
| Validation catch rate | >90% schema errors caught | Inject bad JSON, verify caught |
| Graph connectivity | Avg 3+ edges per node | Neo4j query |
| Response time | <60s for single paper | Timer in UI |
| UI usability | Graph renders, clicks work | Manual test |

---

## Dependencies

```
# requirements.txt additions
mcp>=1.0.0
neo4j>=5.0.0
langgraph>=0.1.0
langchain-google-genai>=1.0.0
langchain-ollama>=0.1.0  # or ollama
pymupdf>=1.23.0  # PDF extraction
streamlit>=1.30.0
streamlit-agraph>=0.0.45
httpx>=0.25.0  # async HTTP for APIs
python-dotenv>=1.0.0
pydantic>=2.0.0
```

---

## Implementation Order

1. **Phase 1.1-1.3**: Schemas, Config, LLM (foundation)
2. **Phase 2.2**: External tools (Brave, ArXiv, HN)
3. **Phase 3**: PDF processing
4. **Phase 4.2**: Paper processor agent (core feature)
5. **Phase 4.3**: Validator agent
6. **Phase 2.1**: Neo4j MCP server (finish)
7. **Phase 4.4**: Synthesizer agent
8. **Phase 4.1**: Searcher agent
9. **Phase 5**: Orchestration
10. **Phase 6**: Streamlit UI

---

## Current Status

- [x] Neo4j Docker running
- [x] .env configured (Gemini, Brave, GitHub, Neo4j)
- [x] docker-compose.yml created
- [x] Phase 1.1 - Schemas complete
- [x] Phase 1.2 - Config complete
- [x] Phase 1.3 - LLM Provider complete (Ollama + Gemini switching works)
- [x] Phase 2.2 - External API Tools complete (Brave, ArXiv, HN all tested)
- [ ] Phase 3 - PDF Processing (NEXT)
