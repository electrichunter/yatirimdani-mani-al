
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

class YFinanceBroker:
    """
    A unified broker interface for YFinance to replace MT5Broker.
    Provides data fetching only. Execution is mocked.
    """
    
    def __init__(self):
        self.name = "YFinance (Data Only)"
        self.initialized = True
        self.logger = logging.getLogger("SniperBot")
        self.logger.info("✅ YFinance Broker Initialized")

    def get_market_data(self, symbol, timeframe, limit=100):
        """
        Fetch market data from Yahoo Finance
        
        Args:
            symbol (str): Symbol name (e.g., 'EURUSD=X', 'AAPL')
            timeframe (str): Timeframe (e.g., 'M1', 'H1', 'D1')
            limit (int): Number of candles (ignored by yfinance, we fetch by period)
            
        Returns:
            pd.DataFrame: OHLCV data
        """
        # Map MT5 timeframes to YFinance intervals
        tf_map = {
            "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
            "H1": "1h", "H4": "1h", # yfinance doesn't have 4h, use 1h and resample if needed, or just 1h
            "D1": "1d", "W1": "1wk", "MN1": "1mo"
        }
        
        interval = tf_map.get(timeframe, "1d")
        
        if interval in ["1m", "2m", "5m", "15m", "30m", "90m"]:
            period = "5d"
        elif "h" in interval:
            period = "1mo" # 1h/4h need ~1 month for 100+ candles
        elif "d" in interval:
            period = "1y" # 1d needs 1y for 100+ candles
        else:
            period = "1y" # Default
            
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df is None or df.empty:
                # Retry with safe defaults if period was too long
                df = ticker.history(period="1y", interval=interval) if period != "1y" else None
                if df is None or df.empty:
                    self.logger.warning(f"No data found for {symbol} on {interval}")
                    return None
                
            # Customize for compatibility with existing code (MTBroker format)
            # YF returns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            # We need: time, open, high, low, close, tick_volume, spread, real_volume
            
            # Reset index to get Date/Datetime as a column
            df.reset_index(inplace=True)
            
            # Rename columns to lowercase
            df.columns = [c.lower() for c in df.columns]
            
            # Rename 'date' or 'datetime' to 'time'
            if 'date' in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            elif 'datetime' in df.columns:
                df.rename(columns={'datetime': 'time'}, inplace=True)
                
            # Ensure time is datetime object
            df['time'] = pd.to_datetime(df['time'])
            
            # Add missing columns expected by the bot
            df['tick_volume'] = df['volume']
            df['spread'] = 0
            df['real_volume'] = df['volume']
            
            # Sort by time
            df.sort_values(by='time', inplace=True)
            
            # Limit to requested amount
            if limit > 0:
                df = df.tail(limit)
                
            # Set time as index to match DataFetcher expectations
            df.set_index('time', inplace=True)
                
            return df
            
        except Exception as e:
            self.logger.error(f"YFinance Error for {symbol}: {e}")
            return None

    def get_current_price(self, symbol):
        """Get the latest price"""
        try:
            ticker = yf.Ticker(symbol)
            # Try history first for currency pairs which can be flaky with info
            df = ticker.history(period="1d", interval="1m")
            if not df.empty:
                return float(df['Close'].iloc[-1])
            
            # fast_info as fallback
            info = ticker.fast_info
            if hasattr(info, 'last_price') and info.last_price is not None:
                 return float(info.last_price)
                
            return None
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
            
    def place_order(self, symbol, action, volume, entry=None, sl=None, tp=None, comment=""):
        """
        Mock order placement
        """
        self.logger.info(f"📝 PAPER TRADE: {action} {symbol} Vol:{volume} SL:{sl} TP:{tp}")
        return {
            "success": True,
            "ticket": 123456,
            "price": entry if entry else self.get_current_price(symbol),
            "volume": volume,
            "error": None
        }

    def get_balance(self):
        """Mock balance"""
        return 10000.0

    def get_open_positions(self):
        """Mock open positions"""
        return []

    def close(self):
        """Cleanup"""
        pass
