
import os
import json
import config
from main import process_symbol

def test_single_trade_restriction():
    print("Testing Single Trade Restriction...")
    
    # Mock components
    class MockBroker:
        def get_open_positions(self):
            return [{"symbol": "EURUSD=X", "status": "OPEN"}]
    
    class MockLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    
    components = {
        "broker": MockBroker(),
        # Other components not needed for the first check
    }
    
    # This should return False because EURUSD=X is "open"
    # We patch the logger in main for this test
    import main
    main.logger = MockLogger()
    
    result = process_symbol("EURUSD=X", components)
    assert result == False, "Analysis should have been skipped for EURUSD=X"
    print("✅ Single trade restriction verified!")

if __name__ == "__main__":
    try:
        test_single_trade_restriction()
    except Exception as e:
        print(f"❌ Test failed: {e}")
