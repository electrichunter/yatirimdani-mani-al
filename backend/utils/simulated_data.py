"""
Simulated Market Data Generator
For testing without MT5 connection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_simulated_data(symbol, timeframe, bars=500):
    """
    Generate realistic fake market data
    
    Args:
        symbol: Trading symbol
        timeframe: H1, H4, D1
        bars: Number of bars to generate
        
    Returns:
        DataFrame with OHLCV data
    """
    # Base prices for different symbols
    base_prices = {
        "EURUSD": 1.0850,
        "GBPUSD": 1.2650,
        "XAUUSD": 2050.00,
        "USDJPY": 148.50
    }
    
    base_price = base_prices.get(symbol, 1.0000)
    
    # Generate timestamps
    if timeframe == "H1":
        delta = timedelta(hours=1)
    elif timeframe == "H4":
        delta = timedelta(hours=4)
    elif timeframe == "D1":
        delta = timedelta(days=1)
    else:
        delta = timedelta(hours=1)
    
    timestamps = [datetime.now() - (delta * i) for i in range(bars, 0, -1)]
    
    # Generate price movements (random walk)
    np.random.seed(42 + hash(symbol) % 1000)  # Deterministic but different per symbol
    
    returns = np.random.normal(0, 0.001, bars)  # Small random returns
    prices = base_price * (1 + returns).cumprod()
    
    # Generate OHLCV
    data = []
    for i, timestamp in enumerate(timestamps):
        open_price = prices[i]
        close_price = prices[i] * (1 + np.random.normal(0, 0.0005))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.001)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.001)))
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'time': timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'tick_volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    
    return df


def get_simulated_price(symbol):
    """Get simulated current price"""
    base_prices = {
        "EURUSD": 1.0850,
        "GBPUSD": 1.2650,
        "XAUUSD": 2050.00,
        "USDJPY": 148.50
    }
    
    base = base_prices.get(symbol, 1.0000)
    # Add small random variation
    variation = np.random.normal(0, 0.0001)
    
    return {
        "bid": base * (1 + variation),
        "ask": base * (1 + variation + 0.0001),
        "mid": base * (1 + variation + 0.00005),
        "time": datetime.now()
    }
