
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def test_connection():
    login = int(os.getenv("MT5_LOGIN", 0))
    password = os.getenv("MT5_PASSWORD", "")
    server = os.getenv("MT5_SERVER", "")
    path = os.getenv("MT5_PATH", "")

    print(f"Testing Login: {login}")
    print(f"Server: {server}")
    print(f"Path: {path}")

    if not path or not os.path.exists(path):
        print(f"ERROR: MT5 path not found at: {path}")
        return

    # Initialize MT5
    print("Initializing MT5...")
    if not mt5.initialize(path=path):
        print("initialize() failed, error code =", mt5.last_error())
        return

    # Login
    print("Attempting login...")
    authorized = mt5.login(login, password=password, server=server)
    
    if authorized:
        print(f"Connected to account #{login} on server {server}")
        print("Terminal Info:", mt5.terminal_info())
        print("Account Info:", mt5.account_info())
    else:
        print("failed to connect at account #{}, error code: {}".format(login, mt5.last_error()))
        error_code = mt5.last_error()
        if error_code == (10004, 'Invalid login/password'):
            print("Suggest checking login/password.")
        elif error_code == -2:
             print("Common error -2: usually 'Common error' or server name mismatch.")
    
    # Check symbols
    print("\nChecking symbols...")
    symbols = mt5.symbols_total()
    print(f"Total symbols found: {symbols}")
    
    if symbols > 0:
        # Try to get info for XAUUSD as a test
        tik = "XAUUSD"
        info = mt5.symbol_info(tik)
        if info:
            print(f"Found {tik}: Bid={info.bid}, Ask={info.ask}")
        else:
            print(f"Could not find {tik}. Trying EURUSD...")
            tik = "EURUSD"
            info = mt5.symbol_info(tik)
            if info:
                print(f"Found {tik}: Bid={info.bid}, Ask={info.ask}")
            else:
                 print("Could not find common symbols. You might need to add them in Market Watch.")

    mt5.shutdown()

if __name__ == "__main__":
    test_connection()
