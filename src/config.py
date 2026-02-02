# from typing import List, Dict
import os
from dotenv import load_dotenv
from enum import Enum
from datetime import datetime, timedelta

# API Keys, option for both local Ollama & Gemini API

load_dotenv()

class LLMProvider(str,Enum): 
    OLLAMA = "ollama"
    GEMINI = "gemini"

LLM_PROVIDER = os.getenv("LLM_PROVIDER","OLLAMA").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL","http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL","qwen2:7b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL","gemini-2.5-flash")

NEO4J_URL = os.getenv("NEO4J_URL","bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME","neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
GITHUB_PAT = os.getenv("GITHUB_PAT")


# Chunking and Overlaps *** 
CHUNK_SIZE_TOKENS = int(os.getenv("CHUNK_SIZE_TOKENS", "2000"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))

MAX_VALIDATION_RETRIES = int(os.getenv("MAX_VALIDATION_RETRIES", "2"))

MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

# Validation heper

def validate_config(): 
    errors = []

    if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY: 
        errors.append("GEMINI_API_KEY must be set when using Gemini LLM provider.")

    if not NEO4J_PASSWORD:
        errors.append("NEO4J_PASSWORD is required")
    
    if not BRAVE_API_KEY:
        errors.append("BRAVE_API_KEY is required for web search")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True

def get_config_summary(): 

    # returns a summary for easy viewing

    return {

        "LLM Provider": LLM_PROVIDER,
        "LLM Model": GEMINI_MODEL if LLM_PROVIDER == "gemini" else OLLAMA_MODEL,
        "Neo4j URL": NEO4J_URL,
        "Chunk Size (tokens)": CHUNK_SIZE_TOKENS,
        "Chunk Overlap (tokens)": CHUNK_OVERLAP_TOKENS,
        "Max Validation Retries": MAX_VALIDATION_RETRIES,
        "Max Search Results": MAX_SEARCH_RESULTS,
    }


# For Chain of Agents
# Check if deprecated later ****

class ChainConfig: 
    MODEL_NAME = 'gemini-2.5-flash'
    TEMPERATURE = 0.3  # lower = more deterministic
    MAX_STEPS = 5  # max reasoning steps for agents

    # HN Search Tool Config
    HN_SEARCH_LIMIT = 10  # default number of stories to fetch per search

    @staticmethod 
    def get_default_time_periods() -> list[dict[str,str]]: 
        """Returns default time periods for analysis."""
        return [
            {"start": "2024-01-01", "end": "2024-03-31", "label": "Q1 2024"},
            {"start": "2024-04-01", "end": "2024-06-30", "label": "Q2 2024"},
            {"start": "2024-07-01", "end": "2024-09-30", "label": "Q3 2024"},
            {"start": "2024-10-01", "end": "2024-12-31", "label": "Q4 2024"},
        ]
    
    @staticmethod 
    def get_monthly_periods(year:int, month_start:int, month_end:int) -> list[dict[str,str]]:
        periods = []    
        for month in range(month_start, month_end + 1):

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            periods.append({
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "label": start_date.strftime("%B %Y")
            })

        return periods
    