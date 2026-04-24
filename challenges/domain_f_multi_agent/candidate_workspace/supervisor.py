"""
Oasis Challenge: Multi-Agent Supervisor Routing
================================================
BUG: The supervisor agent is routing queries to the WRONG worker.
Billing questions go to tech_worker and technical questions go to billing_worker.

YOUR TASK:
1. Fix the routing logic in the `route_query` function.
2. Ensure billing-related queries (refunds, invoices, charges) go to `billing_worker`.
3. Ensure technical queries (errors, crashes, API issues) go to `tech_worker`.
4. Handle ambiguous queries by routing to BOTH workers and merging results.

Run `python supervisor.py` to test your fix locally.
"""

from typing import TypedDict, Literal, List

# --- State Definition ---
class AgentState(TypedDict):
    query: str
    route: str
    billing_response: str
    tech_response: str
    final_answer: str

# --- Worker Nodes ---
def billing_worker(state: AgentState) -> AgentState:
    """Handles billing, invoices, refunds, and payment queries."""
    query = state["query"]
    # Simulated billing knowledge base
    responses = {
        "refund": "To process a refund, navigate to Account > Billing > Request Refund. Refunds take 5-7 business days.",
        "invoice": "Your latest invoice is available under Account > Billing > Invoices. Download as PDF.",
        "charge": "Unexpected charges may be from auto-renewal. Check Account > Subscriptions.",
    }
    for keyword, response in responses.items():
        if keyword in query.lower():
            return {**state, "billing_response": response}
    return {**state, "billing_response": f"Billing team response: We are looking into your query: '{query}'"}

def tech_worker(state: AgentState) -> AgentState:
    """Handles technical issues, errors, API problems, and crashes."""
    query = state["query"]
    responses = {
        "error": "Please check the application logs at /var/log/app.log. Common errors are documented in our troubleshooting guide.",
        "crash": "If the app is crashing, try clearing the cache and restarting. If persistent, submit a bug report.",
        "api": "API rate limits are 1000 requests/minute. Check your API key permissions in Developer Settings.",
    }
    for keyword, response in responses.items():
        if keyword in query.lower():
            return {**state, "tech_response": response}
    return {**state, "tech_response": f"Tech support response: Investigating your issue: '{query}'"}

# --- BUG IS HERE: Supervisor Router ---
def route_query(state: AgentState) -> AgentState:
    """
    Routes the incoming query to the correct specialist worker.
    
    BUG: The routing logic below is INVERTED. 
    Billing keywords incorrectly route to 'tech_worker' and vice versa.
    FIX THIS FUNCTION.
    """
    query = state["query"].lower()
    
    billing_keywords = ["refund", "invoice", "charge", "payment", "billing", "subscription"]
    tech_keywords = ["error", "crash", "bug", "api", "timeout", "deploy", "server"]
    
    # INTENTIONAL BUG: Routes are swapped!
    if any(kw in query for kw in billing_keywords):
        return {**state, "route": "tech_worker"}  # <-- WRONG! Should be billing_worker
    elif any(kw in query for kw in tech_keywords):
        return {**state, "route": "billing_worker"}  # <-- WRONG! Should be tech_worker
    else:
        return {**state, "route": "both"}

def merge_responses(state: AgentState) -> AgentState:
    """Merges responses from both workers for ambiguous queries."""
    billing = state.get("billing_response", "No billing response.")
    tech = state.get("tech_response", "No tech response.")
    return {**state, "final_answer": f"Combined Response:\n- Billing: {billing}\n- Technical: {tech}"}

def finalize(state: AgentState) -> AgentState:
    """Produces the final answer from the routed worker."""
    if state["route"] == "billing_worker":
        return {**state, "final_answer": state.get("billing_response", "No response from billing.")}
    elif state["route"] == "tech_worker":
        return {**state, "final_answer": state.get("tech_response", "No response from tech.")}
    else:
        return merge_responses(state)


# --- Execution (simulates LangGraph run) ---
def run_supervisor(query: str) -> dict:
    """Simulates the LangGraph supervisor execution."""
    state: AgentState = {
        "query": query,
        "route": "",
        "billing_response": "",
        "tech_response": "",
        "final_answer": ""
    }
    
    # Step 1: Route
    state = route_query(state)
    
    # Step 2: Execute worker(s)
    if state["route"] == "billing_worker":
        state = billing_worker(state)
    elif state["route"] == "tech_worker":
        state = tech_worker(state)
    else:
        state = billing_worker(state)
        state = tech_worker(state)
    
    # Step 3: Finalize
    state = finalize(state)
    
    return state


if __name__ == "__main__":
    test_queries = [
        "I need a refund for my last payment",
        "The API is returning a 500 error",
        "How do I update my subscription and fix a deploy issue?",
    ]
    
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        result = run_supervisor(q)
        print(f"Route: {result['route']}")
        print(f"Answer: {result['final_answer']}")
