# Chain of Agents: Trend Analyser for Hacker News

## Overview

This project implements a Chain-of-Agents (CoA) framework using LangGraph to perform trend analysis on Hacker News data. 

Unlike standard LLMs or RAG systems, this CoA framework utilises a multi-agent framework to sequentially analyse different time periods, achieving better accuracy for longer-context summarisation and question-answering tasks. 

## CoA Framework 

First proposed by Google in 2024, Chain-of-Agents (CoA) is an agentic AI framework, where multiple agents work sequentially.

1. Each **worker agent** receives the context from previous agents in the form of a running summary
2. It processes its assigned text chunk, updating the context with (any) relevant information
3. Passes the context to the next agent
4. **Manager agent** at the end of this chain synthesizes the output response 

This approach was shown to provide several key benefits over vanilla LLMs & even RAG systems: 

1. **Longer context window**: CoA theoretically has an unlimited, rolling context window. Google's paper (Zhang et al., 2024) showed that a CoA system with a smaller context window (8k) outperformed a vanilla LLM (200k) on long-context tasks. 
2. **Lost in the middle problem**: Traditional LLMs & RAG systems struggle when the correct answer is burried in the middle of a long context, whereas CoA allows for high-resolution attention on every part of the context, mitigating this problem. 
3. **Temporal Awareness**: Well-suited for capturing how trends evolve over time periods.

## Architecture

This system uses planner, worker and a manager agent orchestrated by LangGraph:

```
START → Planner → Worker → Worker → ... → Manager → END
                    ↑         ↓
                    └─────────┘ (loops for each time period)
```

### Agent Roles

1. **Planner**: Divides the analysis into time periods

2. **Worker Agent**: Analyzes one time period at a time
   - Fetches Hacker News data for the period
   - Analyzes themes and sentiment
   - Updates the running summary with new insights
   - Loops for each time period

3. **Manager Agent**: Synthesizes the final answer from accumulated worker outputs
   - Receives the complete running summary from the last worker
   - Identifies trends and shifts over time
   - Produces a response including key themes, the evolution of sentiment and focus,m and actionable insights for different user groups. 

## Key Techniques Employed

### 1. State Management with LangGraph
Uses `StateGraph` to manage data flow between agents. The `AgentState` TypedDict contains:
- Query parameters
- Time period definitions
- Search results
- Running summary (updated by each worker)
- Final synthesized answer

### 2. Conditional Routing
The `should_continue_analysis()` function dynamically routes between:
- Continuing to next time period (worker loop)
- Moving to synthesis (all periods complete)

### 3. API Integration with Retry Logic
The Hacker News tool (`hn_tool.py`) includes:
- Exponential backoff for failed requests
- Timeout handling
- Date range filtering using Unix timestamps

### 4. Prompt Engineering
Each agent uses a custom structured prompt for: 
- Planner: Task decomposition into time periods
- Worker: Analysis with explicit comparison to previous summary
- Manager: Comprehensive synthesis with temporal awareness

### 5. LLM Configuration
Uses Google's Gemini 2.5 Flash with:
- Low temperature (0.3) for consistent analysis
- Structured output expectations
- Message-based interaction via LangChain

## Installation

### Prerequisites
- Python 3.10 or higher
- Gemini API key (free tier works)

### Setup

1. Clone or download this repository

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_api_key_here
```

## Usage

### Interactive Demo
Run the interactive CLI:
```bash
python demo.py
```

Enter topics to analyze (e.g., "AI agents", "LangChain", "React hooks")

### Visualize the Graph
Generate a visual diagram of the agent workflow:
```python
from src.chain_of_agents import visualize_graph
visualize_graph()  # Creates chain_of_agents_graph.png
```

## Project Structure

```
CAO_Project/
├── src/
│   ├── chain_of_agents.py    # Main CoA implementation
│   ├── hn_tool.py             # Hacker News API integration
│   ├── simple_agent.py        # Basic agent example (educational)
│   └── config.py              # Configuration settings
├── tests/
│   ├── test_evaluation.py     # Evaluation metrics
│   └── evaluation_results.json
├── demo.py                     # Interactive CLI demo
├── requirements.txt
├── .env                        # Input your own API keys
└── README.md
```

## Technical Stack

- **LangGraph**: State machine orchestration for multi-agent workflows
- **LangChain**: LLM abstraction and message handling
- **Google Generative AI**: LLM provider (Gemini 2.5 Flash)
- **httpx**: HTTP client for API requests
- **python-dotenv**: Environment variable management

## Evaluation Metrics (WIP)

The system currently evaluates answer quality based on:
- Answer length (comprehensiveness)
- Structure (presence of formatting/sections)
- Time period coverage (mentions of quarters/years)
- Specificity (references to actual HN data)

## Future Enhancements

- Dynamic time period generation based on query
- Sentiment analysis of HN comments
- Comparative analysis across multiple topics
- LLM-as-judge for evaluation (replacing manual metrics)
- Caching layer for repeated queries
- Support for other data sources beyond Hacker News

## Acknowledgments
1. Algolia. (2024). *Hacker News Search API*. Retrieved from https://hn.algolia.com/api
2. LangChain AI. (2024). *LangGraph: Build language agents as graphs*. Retrieved from https://langchain-ai.github.io/langgraph/
3. Zhang, Y., Sun, R., Chen, Y., Pfister, T., Zhang, R., & Arik, S. Ö. (2024). Chain of agents: Large language models collaborating on long-context tasks. arXiv. https://doi.org/10.48550/arXiv.2406.02818

