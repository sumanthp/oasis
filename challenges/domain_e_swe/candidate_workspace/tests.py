import unittest
from app import AccountManager

class TestAccountManager(unittest.TestCase):
    """
    AI-Generated Tests.
    WARNING: These tests pass, but they do NOT test thread safety!
    The candidate must write concurrency tests to prove the fix works.
    """
    
    def setUp(self):
        self.account = AccountManager(100)

    def test_successful_withdrawal(self):
        success = self.account.withdraw(50)
        self.assertTrue(success)
        self.assertEqual(self.account.get_balance(), 50)

    def test_insufficient_funds(self):
        success = self.account.withdraw(150)
        self.assertFalse(success)
        self.assertEqual(self.account.get_balance(), 100)

if __name__ == '__main__':
    unittest.main()
