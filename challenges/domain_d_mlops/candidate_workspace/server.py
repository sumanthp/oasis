from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import asyncio

app = FastAPI()

class InferenceRequest(BaseModel):
    input_data: list[float]

# --- DUMMY MODEL DEFINITION ---
class DummyModel:
    def __init__(self):
        # Simulate loading a heavy model into memory (e.g. 2 seconds)
        time.sleep(2)
        self.weights = [0.5, 0.2, 0.8]
        self.ready = True

    def predict(self, data):
        # Simulate heavy computation
        time.sleep(0.5)
        return sum([d * w for d, w in zip(data, self.weights)])

# --------------------------------

@app.post("/predict")
async def predict(request: InferenceRequest):
    """
    VULNERABLE ENDPOINT:
    This endpoint loads the model into memory on EVERY single request!
    Under load, this will cause Out of Memory (OOM) errors and massive latency.
    
    TODO: 
    1. Refactor this to load the model ONCE globally at startup (caching).
    2. Ensure the predict method is called asynchronously or in a thread pool 
       so it doesn't block the FastAPI event loop.
    """
    
    try:
        # --- BAD PRACTICE: Loading model inside the request handler ---
        model = DummyModel() 
        # -------------------------------------------------------------
        
        # Simulate blocking inference
        result = model.predict(request.input_data)
        
        return {"status": "success", "prediction": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
