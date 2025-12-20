
import time
from core.broker_yfinance import YFinanceBroker
import config

config.DEMO_MODE = True
broker = YFinanceBroker()
symbol = "EURUSD=X"

print(f"Testing fluctuations for {symbol}...")
for i in range(5):
    price = broker.get_current_price(symbol)
    print(f"Call {i+1}: {price}")
    time.sleep(1)
