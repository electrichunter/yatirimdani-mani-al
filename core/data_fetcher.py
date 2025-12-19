"""
Market Data Fetcher
Retrieves real-time and historical data from MT5
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import config
from utils.logger import setup_logger

logger = setup_logger("DataFetcher")


class DataFetcher:
    """Fetch market data from MT5"""
    
    def __init__(self, broker):
        """
        Args:
            broker: MT5Broker instance
        """
        self.broker = broker
    
    def get_current_price(self, symbol):
        """
        Get current bid/ask prices
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with bid, ask, and mid prices
        """
        # Use Abstract Broker Interface if available
        if hasattr(self.broker, 'get_current_price'):
            price = self.broker.get_current_price(symbol)
            if price:
                return {
                    "bid": price,
                    "ask": price,
                    "mid": price,
                    "time": datetime.now()
                }
            return None

        # DEMO MODE: Use simulated data
        if config.DEMO_MODE:
            from utils.simulated_data import get_simulated_price
            return get_simulated_price(symbol)
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get price for {symbol}")
            return None
        
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "mid": (tick.bid + tick.ask) / 2,
            "time": datetime.fromtimestamp(tick.time)
        }
    
    def get_bars(self, symbol, timeframe, count=500):
        """
        Get historical OHLCV bars
        
        Args:
            symbol: Trading symbol
            timeframe: "H1", "H4", "D1", etc.
            count: Number of bars to retrieve
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        # DEMO MODE: Use simulated data
        if config.DEMO_MODE and not hasattr(self.broker, 'get_market_data'):
            from utils.simulated_data import generate_simulated_data
            return generate_simulated_data(symbol, timeframe, count)
        
        # Use Abstract Broker Interface
        if hasattr(self.broker, 'get_market_data'):
            return self.broker.get_market_data(symbol, timeframe, limit=count)
            
        # Fallback to direct MT5 (Legacy support)
        # Map timeframe strings to MT5 constants
        if not mt5.initialize():
             return None

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1,
            "MN1": mt5.TIMEFRAME_MN1
        }
        
        mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to get bars for {symbol} {timeframe}")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    
    def get_multi_timeframe_data(self, symbol, timeframes=None):
        """
        Get data for multiple timeframes at once
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes (default from config)
            
        Returns:
            Dict with timeframe as key and DataFrame as value
        """
        if timeframes is None:
            timeframes = list(config.TIMEFRAMES.keys())
        
        data = {}
        current_price = self.get_current_price(symbol)
        
        for tf in timeframes:
            df = self.get_bars(symbol, tf)
            if df is not None:
                data[tf] = df
        
        # Add current price info
        data["current_price"] = current_price["mid"] if current_price else None
        data["symbol"] = symbol
        
        return data
