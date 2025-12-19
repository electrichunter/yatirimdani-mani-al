"""
Stage 1: Technical Hard Filter
Fast technical analysis without GPU usage
Goal: Eliminate 90%+ of potential trades immediately
"""

import pandas as pd
import numpy as np
import config
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger("TechnicalFilter")


class TechnicalFilter:
    """
    Technical indicator calculations and signal generation
    No GPU required, pure Python/NumPy calculations
    """
    
    def __init__(self):
        self.logger = logger
    
    def calculate_rsi(self, prices, period=14):
        """
        Calculate Relative Strength Index
        
        Args:
            prices: pandas Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI values as pandas Series
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: pandas Series of closing prices
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)
            
        Returns:
            Dict with macd, signal, and histogram
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def calculate_average_volume(self, volume, period=20):
        """Calculate average volume"""
        return volume.rolling(window=period).mean()
    
    def detect_trend(self, df):
        """
        Detect trend direction using EMAs
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            "BULLISH", "BEARISH", or "NEUTRAL"
        """
        ema_20 = self.calculate_ema(df['close'], 20)
        ema_50 = self.calculate_ema(df['close'], 50)
        ema_200 = self.calculate_ema(df['close'], 200)
        
        current_price = df['close'].iloc[-1]
        ema20_val = ema_20.iloc[-1]
        ema50_val = ema_50.iloc[-1]
        ema200_val = ema_200.iloc[-1]
        
        # Strong bullish: price > EMA20 > EMA50 > EMA200
        if current_price > ema20_val > ema50_val > ema200_val:
            return "BULLISH"
        
        # Strong bearish: price < EMA20 < EMA50 < EMA200
        if current_price < ema20_val < ema50_val < ema200_val:
            return "BEARISH"
        
        return "NEUTRAL"
    
    def check_rsi_signal(self, rsi_value):
        """
        Check RSI for buy/sell signals
        
        Returns:
            Dict with signal and score
        """
        if rsi_value < config.RSI_OVERSOLD:
            return {"signal": "BUY", "score": 30, "reason": f"RSI aşırı satım bölgesinde ({rsi_value:.1f})"}
        elif rsi_value > config.RSI_OVERBOUGHT:
            return {"signal": "SELL", "score": 30, "reason": f"RSI aşırı alım bölgesinde ({rsi_value:.1f})"}
        else:
            return {"signal": "NEUTRAL", "score": 0, "reason": f"RSI nötr ({rsi_value:.1f})"}
    
    def check_macd_signal(self, macd_data):
        """
        Check MACD for crossover signals
        
        Returns:
            Dict with signal and score
        """
        # Get last 2 values to detect crossover
        macd_current = macd_data["macd"].iloc[-1]
        macd_prev = macd_data["macd"].iloc[-2]
        signal_current = macd_data["signal"].iloc[-1]
        signal_prev = macd_data["signal"].iloc[-2]
        histogram_current = macd_data["histogram"].iloc[-1]
        
        # Bullish crossover: MACD crosses above signal
        if macd_prev < signal_prev and macd_current > signal_current:
            return {"signal": "BUY", "score": 25, "reason": "MACD yükseliş kesisi"}
        
        # Bearish crossover: MACD crosses below signal
        if macd_prev > signal_prev and macd_current < signal_current:
            return {"signal": "SELL", "score": 25, "reason": "MACD düşüş kesisi"}
        
        # Check histogram momentum
        if histogram_current > 0:
            return {"signal": "BUY", "score": 10, "reason": "MACD histogram pozitif"}
        elif histogram_current < 0:
            return {"signal": "SELL", "score": 10, "reason": "MACD histogram negatif"}
        
        return {"signal": "NEUTRAL", "score": 0, "reason": "MACD sinyali yok"}
    
    def check_trend_alignment(self, trend_h1, trend_h4, trend_d1):
        """
        Check if multiple timeframes agree on trend
        
        Returns:
            Dict with signal and score
        """
        trends = [trend_h1, trend_h4, trend_d1]
        
        # All timeframes bullish
        if all(t == "BULLISH" for t in trends):
            return {"signal": "BUY", "score": 30, "reason": "Tüm zaman dilimleri yükseliş eğiliminde"}
        
        # All timeframes bearish
        if all(t == "BEARISH" for t in trends):
            return {"signal": "SELL", "score": 30, "reason": "Tüm zaman dilimleri düşüş eğiliminde"}
        
        # Majority bullish
        if trends.count("BULLISH") >= 2:
            return {"signal": "BUY", "score": 15, "reason": "Zaman dilimlerinin çoğu yükseliş eğiliminde"}
        
        # Majority bearish
        if trends.count("BEARISH") >= 2:
            return {"signal": "SELL", "score": 15, "reason": "Zaman dilimlerinin çoğu düşüş eğiliminde"}
        
        return {"signal": "NEUTRAL", "score": 0, "reason": "Trend uyumu yok"}
    
    def check_volume_confirmation(self, df):
        """
        Check if current volume confirms the signal
        
        Returns:
            Dict with score and reason
        """
        current_volume = df['tick_volume'].iloc[-1]
        avg_volume = self.calculate_average_volume(df['tick_volume'], 20).iloc[-1]
        
        if current_volume > avg_volume * config.VOLUME_MULTIPLIER:
            return {"score": 15, "reason": f"Yüksek hacim (ortalamanın {current_volume/avg_volume:.1f}xı)"}
        
        return {"score": 0, "reason": "Hacim önemli değil"}
    
    def analyze(self, market_data):
        """
        Main analysis function - combines all technical indicators
        
        Args:
            market_data: Dict with multi-timeframe data from DataFetcher
            
        Returns:
            Dict with pass/fail, score, direction, and detailed signals
        """
        symbol = market_data.get("symbol", "UNKNOWN")
        
        try:
            # Get data for each timeframe
            df_h1 = market_data.get("H1")
            df_h4 = market_data.get("H4")
            df_d1 = market_data.get("D1")
            
            # H1 is mandatory
            if df_h1 is None:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": "Yetersiz veri (H1 eksik)",
                    "direction": "NONE"
                }
            
            # ========================================
            # CALCULATE INDICATORS
            # ========================================
            
            # RSI (using H1 timeframe)
            rsi = self.calculate_rsi(df_h1['close'])
            rsi_current = rsi.iloc[-1]
            
            # MACD (using H1 timeframe)
            macd = self.calculate_macd(df_h1['close'])
            
            # Trend detection
            trend_h1 = self.detect_trend(df_h1)
            
            # Optional timeframes (handle if missing)
            trend_h4 = self.detect_trend(df_h4) if df_h4 is not None else trend_h1
            trend_d1 = self.detect_trend(df_d1) if df_d1 is not None else trend_h1
            
            # Volume confirmation (H1)
            volume_check = self.check_volume_confirmation(df_h1)
            
            # ========================================
            # GENERATE SIGNALS
            # ========================================
            
            rsi_signal = self.check_rsi_signal(rsi_current)
            macd_signal = self.check_macd_signal(macd)
            trend_signal = self.check_trend_alignment(trend_h1, trend_h4, trend_d1)
            
            # ========================================
            # CALCULATE TOTAL SCORE
            # ========================================
            
            total_score = 0
            buy_score = 0
            sell_score = 0
            
            # Aggregate scores by direction
            if rsi_signal["signal"] == "BUY":
                buy_score += rsi_signal["score"]
            elif rsi_signal["signal"] == "SELL":
                sell_score += rsi_signal["score"]
            
            if macd_signal["signal"] == "BUY":
                buy_score += macd_signal["score"]
            elif macd_signal["signal"] == "SELL":
                sell_score += macd_signal["score"]
            
            if trend_signal["signal"] == "BUY":
                buy_score += trend_signal["score"]
            elif trend_signal["signal"] == "SELL":
                sell_score += trend_signal["score"]
            
            # Add volume bonus to stronger direction
            if buy_score > sell_score:
                buy_score += volume_check["score"]
                total_score = buy_score
                direction = "BUY"
            elif sell_score > buy_score:
                sell_score += volume_check["score"]
                total_score = sell_score
                direction = "SELL"
            else:
                total_score = 0
                direction = "NEUTRAL"
            
            # ========================================
            # DECISION LOGIC
            # ========================================
            
            passed = total_score >= config.TECHNICAL_MIN_SCORE
            
            result = {
                "pass": passed,
                "score": total_score,
                "direction": direction,
                "signals": {
                    "rsi": rsi_current,
                    "rsi_signal": rsi_signal,
                    "macd_signal": macd_signal,
                    "trend_h1": trend_h1,
                    "trend_h4": trend_h4,
                    "trend_d1": trend_d1,
                    "trend_signal": trend_signal,
                    "volume": volume_check,
                    "buy_score": buy_score,
                    "sell_score": sell_score
                },
                "reason": f"{direction} sinyali, {total_score}/100 puan" if passed else f"Puan {total_score}, eşik değerin {config.TECHNICAL_MIN_SCORE} altında"
            }
            
            # Log the decision
            log_trade_decision(logger, symbol, 1, result)
            
            return result
        
        except Exception as e:
            logger.error(f"{symbol} analiz hatası: {str(e)}")
            return {
                "pass": False,
                "score": 0,
                "reason": f"Analiz hatası: {str(e)}",
                "direction": "NONE"
            }
