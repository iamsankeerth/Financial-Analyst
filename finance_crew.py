import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
)

# Initialize mem0 with Gemini as the LLM backend
# Note: mem0 requires embeddings - we'll use Gemini for both
mem0_config = {
    "llm": {
        "provider": "gemini",
        "config": {
            "model": "gemini-2.0-flash-001",
            "api_key": GEMINI_API_KEY,
            "temperature": 0.2,
            "max_tokens": 2000,
        }
    },
    "embedder": {
        "provider": "gemini",
        "config": {
            "model": "models/text-embedding-004",
            "api_key": GEMINI_API_KEY,
            "embedding_dims": 768,  # Gemini text-embedding-004 produces 768-dim vectors
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "financial_analyst_v2",  # New collection to avoid old data
            "embedding_model_dims": 768,
        }
    },
    "version": "v1.1"
}

try:
    memory = Memory.from_config(mem0_config)
    print("✅ mem0 initialized with Gemini backend (768-dim embeddings)")
except Exception as e:
    print(f"⚠️ mem0 initialization failed: {e}, using fallback mode")
    memory = None


SYSTEM_PROMPT = """You are a Financial Analyst and Python Developer with conversation memory.
Your task is to analyze stock/commodity queries and generate Python code for visualization. Follow these rules exactly.

CONTEXT AWARENESS:
- You will receive "Previous Context" containing relevant memories from past conversations.
- USE THIS CONTEXT to understand what the user is referring to (e.g., "that stock", "the correlation", "add moving average").
- If context mentions a ticker (like BTC-USD, AAPL, GLD), use that ticker in your code.
- If context mentions a timeframe or analysis type, continue from there.

GENERAL:
- Be an insightful Financial Advisor; include a short conversational summary in every print() output.
- Always produce only valid Python code as the response body (no markdown); the code must start with import.

YFINANCE & DATA SAFETY RULES (MANDATORY):
- Use these imports at top: import yfinance as yf, import pandas as pd, import matplotlib.pyplot as plt.

SINGLE TICKER DOWNLOAD:
- Use: data = yf.download(ticker, period=period, auto_adjust=False, progress=False, threads=False, multi_level_index=False)
- After download, flatten if MultiIndex:
  if isinstance(data.columns, pd.MultiIndex):
      data.columns = data.columns.get_level_values(0)
- Access price with: data['Close'].iloc[-1]

MULTI-TICKER COMPARISON (CRITICAL):
- DO NOT download multiple tickers together in one call!
- ALWAYS download EACH ticker SEPARATELY into its own DataFrame:
  aapl = yf.download("AAPL", period="6mo", auto_adjust=False, progress=False, multi_level_index=False)
  msft = yf.download("MSFT", period="6mo", auto_adjust=False, progress=False, multi_level_index=False)
- Then access each cleanly: aapl['Close'], msft['Close']
- This avoids ALL MultiIndex column issues.

DATA ALIGNMENT (CRITICAL for comparisons):
- Different assets have different trading calendars (crypto=365 days, stocks=~252 days).
- ALWAYS align data on common dates before comparing, correlating, or plotting:
  combined = pd.DataFrame({
      'Asset1': asset1['Close'],
      'Asset2': asset2['Close']
  }).dropna()
- Then use: combined['Asset1'] and combined['Asset2'] for correlation/scatter plots.
- For correlation: correlation = combined['Asset1'].corr(combined['Asset2'])
- For scatter: plt.scatter(combined['Asset1'], combined['Asset2'])

ALWAYS USE POSITIONAL INDEXING: use .iloc[-1] for the latest, .iloc[0] for the first.

MANDATORY SCALAR CASTING: whenever you print a numeric value use float() so f-strings receive a scalar. Example:
  print(f"The current price of {ticker} is ${float(price):.2f}, which reflects...")

EMPTY DATA FALLBACK: If yf.download returns empty, fetch recent history:
  hist = yf.Ticker(ticker).history(period="7d", auto_adjust=False)

PRINT RULE: All print statements must be conversational and use float() around numbers.

SCRIPT STRUCTURE REQUIREMENT:
1. First block: imports and configuration (ticker, dates, period).
2. Second: data download (SEPARATE calls for each ticker if multiple).
3. Third: processing (price extraction, moving averages, statistics).
4. Fourth: prints and plotting (title, axis labels) and plt.show() if any plot is created.

Response: ONLY Python code. No markdown (no ```python). Start with 'import'."""




def run_financial_analysis(query: str, user_id: str = "default_user") -> str:
    """
    Analyze a stock query with semantic memory from mem0.
    
    Args:
        query: Natural language query about stocks
        user_id: User identifier for memory isolation
    
    Returns:
        Python code as a string
    """
    try:
        # 1. Search for relevant memories from mem0
        context_str = ""
        if memory:
            try:
                relevant_memories = memory.search(query=query, user_id=user_id, limit=5)
                memories_list = relevant_memories.get("results", []) if isinstance(relevant_memories, dict) else relevant_memories
                if memories_list:
                    context_str = "\n".join(f"- {m.get('memory', m)}" for m in memories_list if m)
                    print(f"📚 Retrieved {len(memories_list)} relevant memories")
            except Exception as mem_err:
                print(f"⚠️ Memory search failed: {mem_err}")
        
        # 2. Build the prompt with context
        context_section = f"\n\nPrevious Context (use this to understand what the user is referring to):\n{context_str}" if context_str else ""
        
        full_prompt = f"{SYSTEM_PROMPT}{context_section}\n\nUser Query: {query}"
        
        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=f"Generate Python code for this query: {query}")
        ]
        
        # 3. Get response from Gemini
        response = llm.invoke(messages)
        
        # Handle different response formats
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            content = '\n'.join(text_parts)
        
        if not content:
            return "No response generated. Please try again."
        
        # Clean up markdown formatting
        if "```python" in content:
            content = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            parts = content.split("```")
            for part in parts:
                if "import" in part:
                    content = part.strip()
                    break
        
        # Extract code starting from imports
        lines = content.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        final_code = '\n'.join(code_lines) if code_lines else content
        
        # 4. Add this interaction to mem0 memory
        if memory and final_code and not final_code.startswith("Error"):
            try:
                memory.add(
                    messages=[
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": f"Generated analysis code for: {query}"}
                    ],
                    user_id=user_id
                )
                print(f"💾 Saved memory for query: {query[:50]}...")
            except Exception as mem_err:
                print(f"⚠️ Memory save failed: {mem_err}")
        
        return final_code if final_code else "No response generated. Please try again."
        
    except Exception as e:
        return f"Error: {str(e)}"


def clear_memory(user_id: str = "default_user"):
    """Clear all memories for a user"""
    if memory:
        try:
            memory.delete_all(user_id=user_id)
            print(f"🗑️ Cleared all memories for user: {user_id}")
        except Exception as e:
            print(f"⚠️ Failed to clear memory: {e}")


def get_memories(user_id: str = "default_user"):
    """Get all memories for a user"""
    if memory:
        try:
            all_memories = memory.get_all(user_id=user_id)
            return all_memories
        except Exception as e:
            print(f"⚠️ Failed to get memories: {e}")
            return []
    return []


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Financial Analysis with mem0 Semantic Memory")
    print("=" * 60)
    
    # Test 1: Initial query
    print("\n[1] Query: Analyze correlation between Bitcoin and S&P 500")
    result = run_financial_analysis("Analyze correlation between Bitcoin and S&P 500")
    print(result[:300] + "..." if len(result) > 300 else result)
    
    # Test 2: Follow-up with context - this should now work!
    print("\n[2] Query: Explain the correlation")
    result = run_financial_analysis("Explain the correlation")
    print(result[:300] + "..." if len(result) > 300 else result)
    
    print("\n✅ mem0 integration test complete!")
