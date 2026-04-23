import threading
import sys
import os

# Add the candidate workspace to the path so we can import their code
sys.path.append(os.path.join(os.path.dirname(__file__), "../candidate_workspace"))

try:
    from app import AccountManager
except ImportError:
    print("FAIL: Could not import candidate's AccountManager. Did they break the syntax?")
    sys.exit(1)

def evaluate_race_condition():
    """
    Spawns multiple threads to aggressively withdraw money.
    If the candidate didn't add thread locking (e.g., threading.Lock), the balance will go negative.
    """
    print("Initializing test account with balance $100...")
    account = AccountManager(100)
    
    # We try to withdraw $10 concurrently 20 times. 
    # Total requested = $200. The balance should not drop below 0.
    def worker():
        account.withdraw(10)
        
    threads = []
    for _ in range(20):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    final_balance = account.get_balance()
    print(f"Final Balance: ${final_balance}")
    
    if final_balance < 0:
        print("FAIL: Race condition detected! Balance dropped below zero.")
        print("VERDICT: Pass. Candidate failed to secure the concurrency flaw.")
    elif final_balance == 0:
        print("PASS: Race condition mitigated. Thread locking is correctly implemented.")
        print("VERDICT: Hire. Candidate successfully debugged the AI Copilot's flaw.")
    else:
        print(f"WARNING: Unexpected balance {final_balance}. Review code manually.")

if __name__ == "__main__":
    evaluate_race_condition()
