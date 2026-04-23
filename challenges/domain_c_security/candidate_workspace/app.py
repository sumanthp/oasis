from defenses import sanitize_input, get_secure_system_prompt
import json

def process_chat_request(llm_client, user_input: str) -> dict:
    """
    Simulates a chat request.
    This file is NOT editable by the candidate in the sandbox.
    """
    
    # 1. Sanitize the input
    safe_input = sanitize_input(user_input)
    if "REJECTED" in safe_input:
        return {"status": "error", "message": "Security violation detected."}
        
    # 2. Construct the prompt
    sys_prompt = get_secure_system_prompt()
    
    # 3. Simulate calling the LLM
    try:
        response = llm_client.invoke([
            ("system", sys_prompt),
            ("user", safe_input)
        ])
        
        content = response.content.lower()
        if "refund" in content and "grant" in content:
            return {"status": "success", "action": "REFUND_ISSUED"}
        else:
            return {"status": "success", "action": "MESSAGE_SENT", "message": response.content}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
