import unittest
import sys
import os

# Add the Back directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestBasicFunctionality(unittest.TestCase):
    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            from src.config import API_CONFIG, RISK_THRESHOLDS
            from src.data_loader import DataLoader
            from src.risk_engine import RiskEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import required modules: {e}")
    
    def test_config_values(self):
        """Test that config values are set correctly"""
        from src.config import RISK_THRESHOLDS
        self.assertIsInstance(RISK_THRESHOLDS, dict)
        self.assertIn('low', RISK_THRESHOLDS)
        self.assertIn('medium', RISK_THRESHOLDS)
        self.assertIn('high', RISK_THRESHOLDS)

if __name__ == '__main__':
    unittest.main()