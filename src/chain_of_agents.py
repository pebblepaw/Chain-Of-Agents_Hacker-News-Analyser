import os 
from typing import TypedDict, Annotated, List, TypedDict
from datetime import datetime

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from hn_tool import search_hn_stories, search_hn_by_date_range

from IPython.display import Image, display

load_dotenv() # loads environment

# state: data structure that flows thru the agents
class AgentState(TypedDict):
    query: str 
    time_periods: List[dict]  # start and end 
    current_period_index: int
    search_results: str
    period_summaries: List[str]
    running_summary: str
    final_answer: str

def get_llm(): 
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key = os.getenv("GEMINI_API_KEY"),
        temperature=0.3) #lower = more deterministic, samples less etc.

def manager_nodes(state: AgentState) -> AgentState: 
    
    # defines time periods for worker nodes to examine 
    
    print("/n" + "='"*60)
    print("Manager Agent activated: planning analysis...")
    print("/n" + "='"*60)

    query = state['query']

    #EDIT THIS LATER, MAKE IT DYNAMIC
    time_periods = [
        {"start": "2024-01-01", "end": "2024-03-31", "label": "Q1 2024"},
        {"start": "2024-04-01", "end": "2024-06-30", "label": "Q2 2024"},
        {"start": "2024-07-01", "end": "2024-09-30", "label": "Q3 2024"},
        {"start": "2024-10-01", "end": "2024-12-31", "label": "Q4 2024"},
    ]

    print(f"Query: {query}")
    print(f"Will analyze {len(time_periods)} time periods:")
    for period in time_periods:
        print(f"  - {period['label']}: {period['start']} to {period['end']}")
    
    return {
        **state,
        "time_periods": time_periods,
        "current_period_index": 0,
        "period_summaries": [],
        "running_summary": "",
    }

def worker_node(state: AgentState) -> AgentState:
    # analyze one time period
    # update running summary

    current_index = state['current_period_index']
    time_periods = state['time_periods']

    if current_index >= len(time_periods):
        print("All time periods have been processed.")
        return state  # No more periods to process
    
    period = time_periods[current_index]

    print("\n" + "="*60)
    print(f"🔧 WORKER AGENT: Analyzing {period['label']}...")
    print("="*60)

    print(f"Fetching HN data for '{state['query']}' in {period['label']}...")
    search_results = search_hn_by_date_range(
        query=state['query'],
        start_date=period['start'],
        end_date=period['end'],
        limit = 10)
    print(f"Found data:\n{search_results[:500]}...")  # print first 500 chars

    llm = get_llm()

    analysis_prompt =f"""
You are analyzing Hacker News discusssions about "{state['query']}" 
for the time period {period['label']} ({period['start']} to {period['end']}).

PREVIOUS RUNNING SUMMARY: 
{state['running_summary']}

NEW DATA FROM {period['label']}:
{search_results}

YOUR TASK: 
1. Analyse the new data for this time period
2. Identify key themes, sentiments, and notable discussions
3. Compare with the previous summary, see what changed and what's new?
4. Create an UPDATED RUNNING SUMMARY that incorporates both old and new insights

RESPOND WITH: 
PERIOD ANALYSIS: (2-3 sentences about this specific period)
UPDATED SUMMARY: (comprehensive summary including all periods analysed so far)
"""
    
    response = llm.invoke([HumanMessage(content=analysis_prompt)])
    analysis = response.content

    print(f"\nWorker Analysis: \n{analysis[:500]}...")  # print first 500 chars

    if "UPDATED SUMMARY:" in analysis:
        new_running_summary = analysis.split("UPDATED SUMMARY:")[-1].strip()
    else:
        new_running_summary = analysis
    
    if "PERIOD ANALYSIS:" in analysis and "UPDATED SUMMARY:" in analysis:
        period_analysis = analysis.split("PERIOD ANALYSIS:")[-1].split("UPDATED SUMMARY:")[0].strip()
    else:
        period_analysis = f"Analysis of {period['label']}: {analysis[:200]}"
    
    new_summaries = state["period_summaries"] + [f"{period['label']}: {period_analysis}"]

    return {
    **state,
    "search_results": search_results,
    "period_summaries": new_summaries,
    "running_summary": new_running_summary,
    "current_period_index": current_index + 1}

def synthesizer_node(state: AgentState) -> AgentState:
    # synthesize final answer from period summaries

    print("\n" + "="*60)
    print("🧠 SYNTHESIZER AGENT: Creating final synthesis...")
    print("="*60)

    llm = get_llm()

    all_summaries = "\n".join(state['period_summaries'])

    synthesis_prompt = f"""You are creating a final comprehensive answer about "{state['query']}" based on the analysis of Hacker News discussions across multipe time periods.

    INDIVIDUAL PERIOD ANALYSES: {all_summaries}

    RUNNING SUMMARY: {state['running_summary']}

    YOUR TASK:
    Ceate a well-structured final answer that: 
    1. Summarizes the overall trends across all time periods
    2. highlights key themes and how they evolved over time
    3. Notes any significant shifts in sentiment or focus
    4. Provides actionable insights

    Format your response in a clear, professional manner suitable for someone researching this topic. Use bullet points when appropriate. 
    """

    response = llm.invoke([HumanMessage(content = synthesis_prompt)])
    final_answer = response.content

    print(f"\nFinal Answer Preview:\n{final_answer[:500]}...")  # print first 500 chars     

    return {

        **state,
        "final_answer": final_answer
    }

# The agent routing logic

def should_continue_analysis(state: AgentState) -> str: 

    # decide whether to continue analysing more time periods or -> to synthesis
    # called after each worker node run to determine next step 

    current_index = state['current_period_index']
    total_periods = len(state['time_periods'])

    if current_index < total_periods:
        print(f"\n➡️ Routing: {current_index}/{total_periods} periods done. Continuing...")
        return "continue"  # Go back to worker for next period
    else:
        print(f"\n➡️ Routing: All {total_periods} periods done. Moving to synthesis...")
        return "synthesize"  # Move to synthesizer
    
# the agent graph 

def create_chain_of_agents_graph(): 

    # start -> manager -> worker -> worker (loop) or synthesizer -> end

    graph = StateGraph(AgentState)

    graph.add_node("manager", manager_nodes)
    graph.add_node("worker", worker_node)
    graph.add_node("synthesizer", synthesizer_node)

    # add edges

    graph.add_edge(START, "manager")
    graph.add_edge("manager", "worker")

    graph.add_conditional_edges("worker", should_continue_analysis,
                               {
                                      "continue": "worker",
                                      "synthesize": "synthesizer"
                                 })

    graph.add_edge("synthesizer", END)

    return graph.compile() 

def analyse_hn_trends(query: str) -> str: 
    # main function to run the chain of agents graph 

    print("\n" + "="*60)
    print(f"Starting analysis of Hacker News trends for query: {query}")
    print(f"Started at {datetime.now().isoformat()}")
    print("\n" + "="*60)


    chain = create_chain_of_agents_graph()


    initial_state: AgentState = {
        "query": query,
        "time_periods": [],
        "current_period_index": 0,
        "search_results": "",
        "period_summaries": [],
        "running_summary": "",
        "final_answer": ""
    }

    final_state = chain.invoke(initial_state)

    print("\n" + "="*60)
    print(f"Finished analysis at {datetime.now().isoformat()}")
    print("\n" + "="*60)

    return final_state['final_answer']


# visaulize the agents loop 

def visualize_graph(): 

    try: 
        chain = create_chain_of_agents_graph()

        png_data = chain.get_graph().draw_mermaid_png()

        with open("chain_of_agents_graph.png", "wb") as f:
            f.write(png_data)
        
        print("Graph visualization saved to chain_of_agents_graph.png")

    except Exception as e: 
        print(f"Error generating graph visualization: {str(e)}")

    









if __name__ == "__main__":

    test_queries = [
        "AI Agents",
        "LLM applications",
        "RAG retrieval augmented generation",
    ]

    query = test_queries[0]
    result = analyse_hn_trends(query)

    print("\n" + "="*60)
    print(f"FINAL RESULT FOR QUERY: {query}")
    print("="*60)
    print(result)
