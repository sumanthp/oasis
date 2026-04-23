import time
import threading

class AccountManager:
    """
    AI-Generated Banking Module.
    Candidate has fixed the race condition!
    """
    def __init__(self, initial_balance=1000):
        self.balance = initial_balance
        self._lock = threading.Lock()

    def withdraw(self, amount):
        """Withdraws money if sufficient funds exist."""
        with self._lock:
            if self.balance >= amount:
                # Simulated database latency
                time.sleep(0.01) 
                self.balance -= amount
                return True
            return False
        
    def get_balance(self):
        return self.balance
