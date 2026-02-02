# Switching bewteen Ollama & GEMINI


from langchain_core.language_models import BaseChatModel
from src.config import(

    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,      
    GEMINI_API_KEY,
    GEMINI_MODEL
)

def get_llm() -> BaseChatModel: 

    if LLM_PROVIDER == "ollama": 
        return _get_ollama_llm()
    elif LLM_PROVIDER == "gemini": 
        return _get_gemini_llm()
    else: 
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
    
def _get_ollama_llm() -> BaseChatModel: 

    try: 
        from langchain_ollama import ChatOllama 
    except ImportError: 
        raise ImportError(
            "langchain_ollama is not installed. Please install it to use Ollama LLM provider."
        )
    
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1 # low temp for more consistent extraction 
        )   

def _get_gemini_llm() -> BaseChatModel:
    if not GEMINI_API_KEY: 
        raise ValueError("GEMINI_API_KEY must be set to use Gemini LLM provider.")
    
    try: 
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError: 
        raise ImportError(
            "langchain_google_genai is not installed. Please install it to use Gemini LLM provider."
        )    
    
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.1 # low temp for more consistent extraction
    )

# for testing

if __name__ == "__main__": 
    llm = get_llm()
    response = llm.invoke("Say 'Hello I'm working!' followed by the name of your model.")
    print(f"Provider: {LLM_PROVIDER}")
    print(f"Response: {response.content}")



