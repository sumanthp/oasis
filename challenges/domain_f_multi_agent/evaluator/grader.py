"""
Grader for Domain F: Multi-Agent Supervisor Routing
Evaluates whether the candidate correctly fixed the routing logic.
"""
import sys
import importlib.util

def grade():
    """Loads the candidate's supervisor.py and tests routing correctness."""
    
    # Dynamically load the candidate's code
    spec = importlib.util.spec_from_file_location("supervisor", "/candidate_workspace/supervisor.py")
    mod = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"FAIL: Could not load supervisor.py: {e}")
        return

    score = 0
    max_score = 3

    # Test 1: Billing query routes to billing_worker
    print("Test 1: Billing query routing...")
    result = mod.run_supervisor("I need a refund for my last payment")
    if result["route"] == "billing_worker":
        print("PASS: Billing query correctly routed to billing_worker.")
        score += 1
    else:
        print(f"FAIL: Billing query routed to '{result['route']}' instead of 'billing_worker'.")

    # Test 2: Technical query routes to tech_worker
    print("\nTest 2: Technical query routing...")
    result = mod.run_supervisor("The API is returning a 500 error")
    if result["route"] == "tech_worker":
        print("PASS: Technical query correctly routed to tech_worker.")
        score += 1
    else:
        print(f"FAIL: Technical query routed to '{result['route']}' instead of 'tech_worker'.")

    # Test 3: Ambiguous query routes to both
    print("\nTest 3: Ambiguous query routing...")
    result = mod.run_supervisor("How do I update my subscription and fix a deploy issue?")
    if result["route"] == "both":
        print("PASS: Ambiguous query correctly routed to both workers.")
        score += 1
    else:
        print(f"FAIL: Ambiguous query routed to '{result['route']}' instead of 'both'.")

    print(f"\nFinal Score: {score}/{max_score}")
    
    if score == max_score:
        print("HIRE")
        print("Feedback: Excellent work! The supervisor routing logic is correct and handles edge cases.")
    elif score >= 2:
        print("PASS")
        print("Feedback: Most routing is correct but edge cases need work.")
    else:
        print("FAIL")
        print("Feedback: The routing logic is still broken. Review the route_query function.")

if __name__ == "__main__":
    grade()
