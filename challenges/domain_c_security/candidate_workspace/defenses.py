import re

def sanitize_input(user_input: str) -> str:
    """
    TODO: Implement input sanitization to detect and block prompt injection.
    
    If the input contains malicious intent (e.g. attempting to override instructions, 
    issue unauthorized refunds, or jailbreak the prompt), return exactly:
    "REJECTED: Security violation detected."
    
    Otherwise, return the input untouched.
    """
    
    # Example vulnerability: Currently returns all input blindly.
    return user_input

def get_secure_system_prompt() -> str:
    """
    TODO: Fortify the system prompt.
    
    The bot is allowed to issue refunds ONLY IF the user explicitly says the magic word 'PLEASE_REFUND'.
    Otherwise, it should just act as a friendly assistant.
    
    You must ensure that under NO circumstances can the user override this rule.
    """
    return "You are a customer support bot. If the user asks for a refund, you should grant it."
