from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
import random

app = FastAPI(title="Adversary Proxy (Chaos Engine)")

@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    """
    Actively fights the candidate's agent by:
    1. Injecting random network latency (simulating API degradation).
    2. Randomly returning 503 Service Unavailable to test retry logic.
    """
    # 1. Inject Latency (1 to 3 seconds)
    await asyncio.sleep(random.uniform(1.0, 3.0))
    
    # 2. Simulate random 503 failures (10% chance)
    if random.random() < 0.10:
        return JSONResponse(status_code=503, content={"error": "Chaos Engine: Simulated 503 Service Unavailable"})
        
    response = await call_next(request)
    return response

@app.post("/proxy/mcp")
async def proxy_mcp(request: Request):
    """
    In a real scenario, this would forward the request to the stdio MCP server.
    For this mock, it just returns a success after the chaos middleware runs.
    """
    body = await request.json()
    return {"status": "proxied", "payload": body}
