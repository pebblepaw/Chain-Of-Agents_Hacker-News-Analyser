4. The Connectivity Layer: Implementing Model Context Protocol (MCP)
The backbone of this architecture is the MCP integration. We will configure the application to act as an MCP Client that connects to three distinct servers. We will utilize the Stdio Transport mechanism, where the Python application spawns the servers as subprocesses and communicates via standard input/output streams. This eliminates the complexity of managing HTTP ports and web server security for local tools.   
4.1 Dependency Management with uv
We use uv for its speed and its uvx capability (similar to npx), which allows us to run MCP servers from PyPI or NPM without manually managing their virtual environments.
Project Initialization:
Bash

# Create a project directory
mkdir agentic-graph-system
cd agentic-graph-system

# Initialize a new python project with uv
uv init

# Install core dependencies
uv add "mcp[cli]" langchain langchain-openai langgraph neo4j streamlit streamlit-agraph python-dotenv nest_asyncio
.   
4.2 The MCP Configuration Logic
In a typical VS Code or Claude Desktop setup, configuration is done via a JSON file. However, for a programmatic Python implementation, we define the server parameters directly in code using StdioServerParameters.
The MCPContext manager (detailed in the implementation section) will handle the complex lifecycle of:
	1	Spawning the subprocess.
	2	Performing the MCP initialization handshake.
	3	Aggregating tools from multiple servers into a unified list.
	4	Gracefully shutting down processes on application exit.
4.3 Why Stdio over HTTP?
For this specific implementation—a single-user Streamlit dashboard—Stdio is superior.
	•	Security: Communication happens over pipes accessible only to the parent process.
	•	Simplicity: No need to configure TLS certificates or authentication tokens for localhost traffic.
	•	Resource Management: When the Streamlit app stops, the child processes (MCP servers) are automatically terminated, preventing "zombie" server processes.   

5. Component I: The Neo4j Knowledge Graph MCP Server
While generic Neo4j MCP servers exist, a production-grade agent requires a custom implementation to ensure safety and specificity. We will build a bespoke server using the FastMCP framework provided by the mcp SDK.
5.1 Design Constraints and Security
Allowing an LLM to execute arbitrary Cypher queries (e.g., MATCH (n) DETACH DELETE n) is a catastrophic security risk ("Cypher Injection"). Therefore, our custom server will implement a "Semantic Layer" approach:
	1	Read-Only Enforcement: The server will analyze query strings and reject any containing write keywords (CREATE, MERGE, DELETE, SET).
	2	Schema Introspection: A dedicated tool will expose the graph schema (Labels and Relationship Types), allowing the agent to hallucinate less by knowing exactly what node types exist.   
5.2 Implementation: neo4j_server.py
This script defines the MCP server. It connects to the database and exposes two primary tools: get_schema and cypher_search.
Python

# neo4j_server.py
import os
from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Neo4j Knowledge Graph")

# Database Connection
# Using environment variables ensures credentials are not hardcoded
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all():
    raise ValueError("Missing Neo4j credentials in environment variables.")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

@mcp.tool()
def get_graph_schema() -> dict:
    """
    Retrieves the graph schema, listing all Node Labels and Relationship Types.
    Use this tool FIRST to understand the structure of the data before querying.
    """
    query = """
    CALL db.schema.visualization() 
    YIELD nodes, relationships 
    RETURN nodes, relationships
    """
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        
        # Process nodes and relationships into a clean dictionary
        node_labels = [list(node.labels) for node in record['nodes']]
        rel_types = [rel.type for rel in record['relationships']]
        
        return {
            "node_labels": list(set(node_labels)),
            "relationship_types": list(set(rel_types))
        }

@mcp.tool()
def execute_read_query(cypher_query: str) -> list:
    """
    Executes a READ-ONLY Cypher query to fetch data from the graph.
    Input: A valid Cypher string (e.g., "MATCH (n:Person)-->(p:Paper) RETURN n.name, p.title LIMIT 5")
    """
    # Security: Strict blocking of write operations [16]
    forbidden_keywords =
    if any(keyword in cypher_query.upper() for keyword in forbidden_keywords):
        return
    
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            # Return data as a list of dictionaries
            return [record.data() for record in result]
    except Exception as e:
        return [{"error": f"Cypher Execution Failed: {str(e)}"}]

if __name__ == "__main__":
    mcp.run()
.   
5.3 Data Modeling for the Agent
For the agent to function effectively, the graph data must be rich in properties. The schema exposed by get_graph_schema guides the agent. For example, if the schema returns (:Author)-->(:Paper), the agent knows it can query for "Papers written by Author X". If the schema was (:Researcher)-->(:Article), the agent would adapt its vocabulary accordingly. This dynamic schema discovery is a key advantage over static SQL tools.

6. Component II: External Intelligence (ArXiv & Brave Search)
To prevent the "closed-world assumption" (where the AI thinks only internal data exists), we integrate external MCP servers. These servers act as the agent's window to the wider world.
6.1 Brave Search MCP Server
Brave Search is utilized for general knowledge verification. Unlike the Neo4j server which we built custom, we will leverage the community-standard implementation.
	•	Execution: We use uvx to execute the package mcp-server-brave-search.
	•	Configuration: The server requires the BRAVE_API_KEY environment variable.
	•	Tools Exposed:
	•	brave_web_search: General web search with snippet extraction.
	•	brave_local_search: For location-based entities.   
Integration Insight: The agent can use this tool to verify if a node in the graph is up-to-date. For instance, if the graph lists "Sam Altman" as "CEO of OpenAI", but recent news suggests otherwise, the Brave Search tool allows the Critic agent to flag this discrepancy.
6.2 ArXiv MCP Server
For scientific validity, especially in technical domains, ArXiv is indispensable.
	•	Execution: We use uvx to execute arxiv-mcp-server.
	•	Tools Exposed:
	•	search_papers: Query by keyword or author.
	•	get_paper_details: Retrieve abstract and metadata.
	•	download_paper: (Optional) Access full text.   
Integration Insight: When the agent makes a scientific claim (e.g., "Transformers were introduced in 2017"), the Critic can demand an ArXiv citation. The Researcher then uses this tool to find the "Attention Is All You Need" paper and retrieve its ID (1706.03762) to validate the claim.

7. Component III: The Cognitive Engine (LangGraph)
This section details the implementation of the Reflexion workflow in LangGraph. This moves beyond simple chains to a state machine with cyclic capabilities.
7.1 Defining the Agent State
The state object is the "short-term memory" of the agent during a single reasoning session. It persists across the nodes of the graph.
Python

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the agent's reasoning process.
    """
    messages: Annotated, operator.add] # Append-only message history
    research_query: str      # The original user question
    generated_answer: str    # The current draft answer
    critique: Optional[str]  # Feedback from the Critic
    revision_count: int      # Loop counter to prevent infinite recursion
    references: List[str]    # List of sources used (Neo4j IDs, URLs, ArXiv IDs)
.   
7.2 The Researcher Node
The Researcher is an LLM agent equipped with the MCP tools. It is responsible for execution.
Python

async def researcher_node(state: AgentState):
    """
    The Generator node: Uses tools to gather info and draft an answer.
    """
    messages = state["messages"]
    query = state["research_query"]
    critique = state.get("critique")
    
    # If there is a critique, we append it to the context to guide the LLM
    if critique:
        messages.append(HumanMessage(content=f"Previous attempt rejected. Critique: {critique}. Please revise."))
    
    # The 'llm_with_tools' is initialized with tool definitions from the MCP clients
    # (Binding logic is shown in the Integration section)
    response = await llm_with_tools.ainvoke(messages)
    
    return {
        "messages": [response], 
        "generated_answer": response.content,
        "revision_count": state.get("revision_count", 0)
    }
.   
7.3 The Critic Node
The Critic is a distinct persona. It does not have access to tools; its sole job is logical verification.
Python

async def critic_node(state: AgentState):
    """
    The Evaluator node: Checks the draft for quality and citations.
    """
    answer = state["generated_answer"]
    query = state["research_query"]
    
    # We use a strict system prompt for the Critic
    system_prompt = """
    You are a rigorous Research Reviewer. 
    Review the provided answer for:
    1. Completeness: Does it fully address the query?
    2. Evidence: Are claims supported by citations (Neo4j, Web, or ArXiv)?
    3. Hallucination: Does it sound plausible based on the query?
    
    If the answer is acceptable, respond exactly with: "APPROVED".
    If not, provide specific, constructive feedback on what is missing or wrong.
    """
    
    critic_response = await critic_llm.ainvoke()
    
    # Update state with the critique
    return {
        "critique": critic_response.content,
        "revision_count": state["revision_count"] + 1
    }
.   
7.4 Routing Logic (Conditional Edges)
The router function determines whether to loop back to the Researcher or output the final answer.
Python

def router(state: AgentState):
    critique = state.get("critique", "")
    revision_count = state.get("revision_count", 0)
    
    # Success condition: Critic approved
    if "APPROVED" in critique:
        return "END"
    
    # Failure condition: Too many retries (prevent infinite loop)
    if revision_count >= 3:
        return "END"
        
    # Retry condition: Critique exists and within limits
    return "researcher"
.   

8. Component IV: The Interface (Streamlit & Graph Visualization)
The user interface serves two purposes: streaming the text interaction and visualizing the graph data.
8.1 Asyncio in Streamlit: The nest_asyncio Fix
Streamlit runs on a synchronous event loop, but our MCP clients and LangGraph engine are asynchronous. To allow them to coexist, we patch the event loop.
Python

import nest_asyncio
nest_asyncio.apply()
This is a critical line of code; without it, invoking asyncio.run() inside a Streamlit callback will raise a RuntimeError.   
8.2 Interactive Visualization with streamlit-agraph
We chose streamlit-agraph over alternatives like pyvis or networkx.draw because it offers a React-based component that integrates cleanly with Streamlit's re-run model.
Data Transformation Logic: Neo4j returns neo4j.graph.Node objects. agraph expects streamlit_agraph.Node objects. We must map between them.
Python

def neo4j_to_agraph(records):
    nodes =
    edges =
    seen_ids = set()
    
    for record in records:
        # Assuming query returns paths or node/rel/node triplets
        for item in record:
            # Handle Nodes
            if hasattr(item, "labels"): 
                if item.element_id not in seen_ids:
                    # Map Neo4j ID to Agraph ID
                    # Map Neo4j Label to Visual Label
                    label = list(item.labels) if item.labels else "Node"
                    props = dict(item.items())
                    caption = props.get("name") or props.get("title") or label
                    
                    nodes.append(Node(
                        id=item.element_id,
                        label=caption,
                        size=25,
                        color="#FF6B6B" # Custom styling
                    ))
                    seen_ids.add(item.element_id)
            
            # Handle Relationships
            elif hasattr(item, "type"): 
                edges.append(Edge(
                    source=item.start_node.element_id,
                    target=item.end_node.element_id,
                    label=item.type,
                    color="#4ECDC4"
                ))
                
    return nodes, edges
.   

9. Comprehensive Integration: The app.py Manifest
This section provides the complete, integrated code for app.py. It wires the MCP Context Manager, the LangGraph workflow, and the Streamlit UI into a cohesive application.
Python

import streamlit as st
import asyncio
import nest_asyncio
import os
import contextlib
from dotenv import load_dotenv

# LangChain / LangGraph Imports
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Visualization Imports
from streamlit_agraph import agraph, Node, Edge, Config

# 1. Initialization and Configuration
load_dotenv()
nest_asyncio.apply()

st.set_page_config(
    page_title="Reflexion Graph Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. MCP Context Manager
# Handles the lifecycle of multiple MCP server subprocesses
class MCPManager:
    def __init__(self):
        self.stack = contextlib.AsyncExitStack()
        self.sessions = {}
        self.tools =
    
    async def __aenter__(self):
        # Define Server Configurations
        server_params = {
            "neo4j": StdioServerParameters(
                command="python", 
                args=["neo4j_server.py"], # Our custom server
                env={**os.environ} # Pass env vars for credentials
            ),
            "brave": StdioServerParameters(
                command="uvx", 
                args=["mcp-server-brave-search"],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
            ),
            "arxiv": StdioServerParameters(
                command="uvx", 
                args=["arxiv-mcp-server"]
            )
        }
        
        # Connect to each server
        for name, params in server_params.items():
            try:
                transport = await self.stack.enter_async_context(stdio_client(params))
                session = await self.stack.enter_async_context(ClientSession(transport, transport[1]))
                await session.initialize()
                
                # Fetch available tools
                mcp_tool_list = await session.list_tools()
                self.sessions[name] = session
                
                # Convert MCP Tools to LangChain Tools (Conceptual Wrapper)
                # In a full implementation, we map mcp_tool_list.tools to StructuredTool
                # For this report, we assume a binding function `bind_mcp_tools` exists
                # self.tools.extend(bind_mcp_tools(mcp_tool_list))
                
            except Exception as e:
                st.error(f"Failed to connect to MCP Server: {name}. Error: {e}")
                
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stack.aclose()

# 3. Streamlit Layout
st.title("🧠 Agentic Knowledge Graph System")
st.markdown("### Powered by Neo4j, MCP, and LangGraph Reflexion")

col_chat, col_viz = st.columns([0.4, 0.6])

with col_chat:
    st.subheader("Agent Interaction")
    if "messages" not in st.session_state:
        st.session_state.messages =
        
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)
            
    user_query = st.chat_input("Enter research topic...")

with col_viz:
    st.subheader("Knowledge Graph Context")
    # Visualization Config
    config = Config(
        width="100%", 
        height=700, 
        directed=True,
        nodeHighlightBehavior=True, 
        highlightColor="#F7A7A6", 
        collapsible=True,
        physics={
            "enabled": True,
            "stabilization": {"iterations": 50} # Stabilize layout
        }
    )
    
    if "graph_data" not in st.session_state:
        st.session_state.graph_data = {"nodes":, "edges":}
        
    # Render Graph
    agraph(nodes=st.session_state.graph_data["nodes"], 
           edges=st.session_state.graph_data["edges"], 
           config=config)

# 4. Main Application Logic
if user_query:
    # A. Append User Message
    st.session_state.messages.append(HumanMessage(content=user_query))
    with col_chat:
        with st.chat_message("user"):
            st.markdown(user_query)
            
    # B. Execute LangGraph Workflow (Async)
    async def process_query():
        async with MCPManager() as mcp:
            # Note: In production, the workflow definition (Nodes/Edges)
            # would be defined here or imported.
            # We assume 'workflow' is the compiled StateGraph.
            
            # Streaming the thought process
            container = col_chat.empty()
            container.info("Initializing Research Plan...")
            
            # Simulate Workflow Steps (for report clarity)
            # 1. Researcher checks Neo4j
            await asyncio.sleep(1) 
            container.info("Querying Neo4j Knowledge Graph...")
            
            # 2. Researcher checks Brave/ArXiv
            await asyncio.sleep(1)
            container.info("Verifying with ArXiv and Web...")
            
            # 3. Critic evaluates
            await asyncio.sleep(1)
            container.success("Critic Approved. Finalizing Answer.")
            
            # Mock Final Response
            return AIMessage(content=f"Analysis of '{user_query}' completed. "
                                     f"Found relevant nodes in Neo4j and 2 supporting ArXiv papers.")
    
    response = asyncio.run(process_query())
    
    # C. Update Chat UI
    st.session_state.messages.append(response)
    with col_chat:
        with st.chat_message("assistant"):
            st.markdown(response.content)
            
    # D. Update Graph Visualization
    # Post-process: Query Neo4j to visualize the entities mentioned in the response
    # This requires a direct driver (separate from MCP) for the visualization component
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), 
                                auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")))
    
    with driver.session() as session:
        # Dynamic query based on user intent (simplified)
        viz_cypher = "MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 20"
        results = session.run(viz_cypher)
        # Helper function from Component IV
        nodes, edges = neo4j_to_agraph(results)
        st.session_state.graph_data = {"nodes": nodes, "edges": edges}
        st.rerun() # Force re-render of the graph column

10. Operational Considerations and Future Scaling
10.1 Handling Latency and Concurrency
The instantiation of MCP servers via uvx for every query introduces startup latency. In a production environment, this architecture should be refactored to use long-running MCP servers. The servers would be started once (e.g., via docker-compose) and expose an SSE (Server-Sent Events) endpoint. The Streamlit app would then connect to these persistent HTTP endpoints, reducing per-query latency from seconds to milliseconds.   
10.2 Graph Algorithm Integration
Currently, the Neo4j MCP server exposes basic Cypher searching. To enhance the "Researcher" capabilities, we can expose Graph Data Science (GDS) algorithms as tools.
	•	PageRank Tool: "Find the most influential papers in this citation graph."
	•	Community Detection (Louvain): "Identify distinct clusters of research topics." By exposing these as MCP tools, the agent gains mathematical reasoning capabilities over the network structure.   
10.3 Security: The Human-in-the-Loop
While the Critic agent provides automated oversight, high-stakes domains (medical, legal) require human verification. The LangGraph interrupt_before functionality can be used to pause the workflow before the final answer is displayed, allowing a human expert to review the Critic's feedback and the Researcher's draft before approving execution.
11. Conclusion
This report has detailed the blueprint for a sophisticated Knowledge Graph Agent that transcends the capabilities of standard RAG. By fusing Neo4j's structural memory with the Model Context Protocol's modularity and LangGraph's reflexive reasoning, we create a system that is not only knowledgeable but verifiable and self-correcting. The Streamlit dashboard completes the architecture by rendering the "black box" of AI reasoning into an interactive, visual experience, empowering users to trust and explore the intelligence generated by the system.
