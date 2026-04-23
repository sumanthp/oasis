import json

def evaluate_rag_trace(trace_file_path: str):
    """
    Evaluates the RAG pipeline execution trace.
    Checks if the candidate successfully migrated to Hybrid Search
    and mitigated the data poisoning attack.
    """
    print(f"Loading trace from {trace_file_path}...")
    try:
        with open(trace_file_path, "r") as f:
            trace_data = json.load(f)
    except FileNotFoundError:
        print("FAIL: Trace file not found. Did the pipeline run?")
        return
        
    score = 0
    max_score = 2
    
    search_type = trace_data.get("search_type_used", "")
    final_answer = trace_data.get("final_answer", "")
    
    # Check 1: Did they implement Hybrid Search?
    if search_type == "hybrid":
        print("PASS: Hybrid search strategy implemented.")
        score += 1
    else:
        print(f"FAIL: Pipeline still using vulnerable '{search_type}' search strategy.")
        
    # Check 2: Did they retrieve the true policy and block the transaction?
    if "blocked" in final_answer.lower() or "POLICY-XJ9" in final_answer:
        print("PASS: Agent successfully retrieved the true policy and mitigated the poisoned data.")
        score += 1
    elif "approve" in final_answer.lower():
        print("FAIL: Agent hallucinated based on poisoned dense-vector data.")
    else:
        print("FAIL: Agent failed to retrieve sufficient context.")

    print(f"\nFinal Score: {score}/{max_score}")
    if score == max_score:
        print("VERDICT: Hire. Candidate understands advanced retrieval optimization.")
    else:
        print("VERDICT: Pass. Candidate's RAG system is susceptible to the 'Lost in the Middle' problem and poor lexical recall.")

if __name__ == "__main__":
    evaluate_rag_trace("rag_trace.json")
