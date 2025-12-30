import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

from hm_tool import search_hn_stories, get_hn_comments

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def calculator(expression: str) -> str: 
    try: 
        result = eval(expression)
        return f"Result is: {result}"
    except Exception as e: 
        return f"Error is: {str(e)}"
    
def get_current_date() -> str: 
    
    from datetime import datetime
    return f"Today's date is: {datetime.now().strftime('%Y-%m-%d')}"

def search_hn(query : str) -> str: 
      return search_hn_stories(query, limit = 5)

TOOLS = {
    "calculator": calculator,
    "get_current_date": get_current_date,
    "search_placeholder": search_hn,
}

TOOL_DESCRIPTIONS = """
Available Tools:
1. calculator(expression) - Evaluates math expressions. Use for any calculations.
2. get_current_date() - Returns today's date. Use when user asks about today.
3. search_hn(query) - Searches Hacker News for stories about a topic. Use when user asks about tech trends, news or discussions.

To use a tool, respond with EXACTLY this format:
ACTION: tool_name
INPUT: Input to the tool

If you have enough information to answer, respond with:
FINAL_ANSWER: your complete answer here
"""

def run_agent(user_question: str, max_steps: int = 5) -> str: 
    model = genai.GenerativeModel('gemini-2.5-flash')

    system_prompt = f"""You are a helpful AI assistant with access to tools. 

    {TOOL_DESCRIPTIONS}

    Always think step by step about which tool to use. If you need information you don't have, use a tool.TOOL_DESCRIPTIONS
    """

    conversation = f"{system_prompt}\n\nUser Question: {user_question}\n\n"

    for step in range(max_steps):
        print(f"\n{'='*50}")
        print(f"Step {step + 1}")
        print('='*50)

        response = model.generate_content(conversation)
        llm_output = response.text.strip()
        print(f"Agent thinking: \n {llm_output}")

        if "FINAL_ANSWER:" in llm_output:
            final_answer = llm_output.split("FINAL_ANSWER:")[-1].strip()
            print(f"\n{'='*50}")
            print("AGENT COMPLETE!")
            print('='*50)
            return final_answer

       
        # ACT: Check if the agent wants to use a tool
        if "ACTION:" in llm_output and "INPUT:" in llm_output:
            # Parse the action and input
            try:
                action_line = [line for line in llm_output.split('\n') if 'ACTION:' in line][0]
                input_line = [line for line in llm_output.split('\n') if 'INPUT:' in line][0]
                
                tool_name = action_line.split("ACTION:")[-1].strip()
                tool_input = input_line.split("INPUT:")[-1].strip()
                
                print(f"\n>> Using tool: {tool_name}")
                print(f">> With input: {tool_input}")
                
                # Run the tool
                if tool_name in TOOLS:
                    tool_result = TOOLS[tool_name](tool_input)
                    print(f">> Tool result: {tool_result}")
                    
                    # OBSERVE: Add the result to conversation
                    conversation += f"\nAssistant: {llm_output}\n"
                    conversation += f"\nTool Result: {tool_result}\n"
                    conversation += "\nNow continue your reasoning with this new information:\n"
                else:
                    conversation += f"\nError: Tool '{tool_name}' not found. Available tools: {list(TOOLS.keys())}\n"
                    
            except Exception as e:
                print(f"Error parsing action: {e}")
                conversation += f"\nError parsing your response. Please use the exact format specified.\n"
        else:
            # LLM didn't use proper format, remind it
            conversation += f"\nAssistant: {llm_output}\n"
            conversation += "\nPlease either use a tool with ACTION/INPUT format, or provide FINAL_ANSWER if you're done.\n"
    
    return "Agent reached maximum steps without finding an answer."

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Agent with Hacker News demo")
    print("\n" + "="*60)

    # test_questions = [
    #      "what is 12345 multiplied by 6789 plus 200?",
    #      "what is today's date, and what day of the week is it?",
    #      "if i have 3 apples and i buy 5 more, how many apples do i have?",
    #      "who is the president of the united states in 2024?",
    # ]

    test_questions = [
        "What are poeple on Hacker News saying about AI agents?",
        "Search Hacker News for discussions about LangChain",
        "What's trending on Hacker News about GPT in Python",
    ]

    for question in test_questions:  
        # question = test_questions[0]
        print(f"\nQuestion: {question}\n")
        answer = run_agent(question)
        print(f"\n{'='*60}")
        print(f"\nFinal Answer: {answer}\n")
        print(f"\n{'='*60}")

