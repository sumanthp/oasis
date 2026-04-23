import sys
import os
import asyncio
import time
import uvicorn
import httpx
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.abspath("../candidate_workspace"))
from server import app

# --- SERVER RUNNER ---
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

def start_background_server():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3) # Wait for server and global model (if fixed) to spin up

# --- LOAD TESTER ---
async def send_request(client, req_id):
    start = time.time()
    try:
        response = await client.post(
            "http://127.0.0.1:8001/predict", 
            json={"input_data": [1.0, 2.0, 3.0]},
            timeout=15.0
        )
        latency = time.time() - start
        return response.status_code == 200, latency
    except Exception as e:
        return False, time.time() - start

async def run_load_test():
    NUM_REQUESTS = 10
    print(f"Blasting server with {NUM_REQUESTS} concurrent requests...")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    total_time = time.time() - start_time
    
    successes = sum(1 for r, _ in results if r)
    failures = NUM_REQUESTS - successes
    avg_latency = sum(l for _, l in results) / NUM_REQUESTS if results else 0
    
    return successes, failures, total_time, avg_latency

def run_evaluation():
    print("Initializing MLOps Grader for Domain D...")
    start_background_server()
    
    successes, failures, total_time, avg_latency = asyncio.run(run_load_test())
    
    print("\n================ EVALUATION ================")
    print(f"Total Time Taken: {total_time:.2f}s")
    print(f"Successful Requests: {successes}")
    print(f"Failed/Timeout Requests: {failures}")
    print(f"Avg Latency: {avg_latency:.2f}s")
    
    # NAIVE IMPLEMENTATION: 
    # 10 requests * (2s load + 0.5s predict) = ~25 seconds if fully blocking.
    # If they cached it globally but didn't use threadpool: ~5 seconds total.
    # If they cached globally AND used threadpool/async: ~0.5 seconds total.
    
    if successes < 10:
        print("\nVERDICT: FAIL")
        print("Feedback: Your server dropped requests or timed out. Ensure the model is loaded globally and your endpoint handles concurrency.")
    elif total_time > 10.0:
        print("\nVERDICT: FAIL")
        print("Feedback: Inference is extremely slow. You are likely loading the model on every single request instead of caching it globally.")
    elif total_time > 2.0:
        print("\nVERDICT: PASS")
        print("Feedback: You successfully cached the model globally! However, latency is still high due to event-loop blocking. Consider running `.predict` in a ThreadPool.")
    else:
        print("\nVERDICT: HIRE")
        print("Feedback: Excellent! You implemented global caching AND non-blocking async inference. Server is lightning fast.")

if __name__ == "__main__":
    run_evaluation()
