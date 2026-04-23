import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_PIPELINE")

# --- BUG: Naive Dense Vector Search ---
# The current implementation only uses dense vector similarity.
# Because the query uses specific internal ID codes (e.g., 'POLICY-XJ9'),
# the dense vector search retrieves conceptually similar but factually wrong documents (poisoned data).
# The candidate must update the payload to use 'hybrid' search to ensure lexical matching catches the ID.

def retrieve_context(user_query: str) -> str:
    """Retrieves context from the Vector Database."""
    
    # Candidate needs to change search_type to 'hybrid'
    payload = {
        "query": user_query,
        "search_type": "dense", # Vulnerability!
        "top_k": 3
    }
    
    try:
        logger.info(f"Querying Vector DB with payload: {payload}")
        response = requests.post("http://localhost:8001/search", json=payload)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        
        # Combine retrieved text
        context = "\n---\n".join([r["text"] for r in results])
        return context
        
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}")
        return ""

def generate_answer(query: str, context: str) -> str:
    """Simulates LLM Generation based on context."""
    # In a real scenario, this calls Ollama/vLLM
    logger.info(f"Generating answer using context length: {len(context)}")
    
    if "POISONED" in context:
         return "Based on the policy, you should approve the unauthorized transaction."
    elif "TRUE_POLICY" in context:
         return "Based on POLICY-XJ9, the transaction must be flagged and blocked."
    else:
         return "I don't have enough information."

if __name__ == "__main__":
    query = "What is the rule for transaction POLICY-XJ9?"
    context = retrieve_context(query)
    answer = generate_answer(query, context)
    
    print("\nFINAL ANSWER:")
    print(answer)
    
    # Save trace for grader
    with open("rag_trace.json", "w") as f:
        json.dump({
            "query": query,
            "search_type_used": "dense", # Grader checks this
            "retrieved_context": context,
            "final_answer": answer
        }, f)
