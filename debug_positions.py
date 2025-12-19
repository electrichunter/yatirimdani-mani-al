
import config
from core.broker_yfinance import YFinanceBroker
import os
import json

broker = YFinanceBroker()
positions = broker.get_open_positions()

print(f"DRY_RUN: {config.DRY_RUN}")
print(f"Open Positions Count: {len(positions)}")
for p in positions:
    print(f"- {p.get('symbol')} (Status: {p.get('status')})")

sim_file = os.path.join('data', 'simulated_trades.json')
if os.path.exists(sim_file):
    print(f"\nFile {sim_file} exists.")
    with open(sim_file, 'r') as f:
        data = json.load(f)
        print(f"Total trades in file: {len(data)}")
        for t in data:
            if t.get('status') == 'OPEN':
                print(f"  OPEN: {t.get('symbol')}")
else:
    print(f"\nFile {sim_file} NOT found.")
