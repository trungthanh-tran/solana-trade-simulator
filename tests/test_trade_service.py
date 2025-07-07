import unittest
from src.services.trade_service import TradeService

class TestTradeService(unittest.TestCase):
    def setUp(self):
        self.trade_service = TradeService()
    
    def test_get_quote_error_handling(self):
        # Test with invalid mint address
        result = self.trade_service.get_quote("INVALID_MINT", "So11111111111111111111111111111111111111112", 1.0)
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()