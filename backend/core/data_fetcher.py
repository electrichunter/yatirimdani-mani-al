"""
Piyasa Verisi Çekici
MT5 veya diğer kaynaklardan gerçek zamanlı ve geçmiş verileri alır
"""

import pandas as pd
from datetime import datetime, timedelta
import config
from utils.logger import setup_logger

logger = setup_logger("DataFetcher")


class DataFetcher:
    """MT5 veya Broker üzerinden piyasa verilerini çeker"""
    
    def __init__(self, broker):
        """
        Argümanlar:
            broker: Broker örneği (örn. YFinanceBroker veya MT5Broker)
        """
        self.broker = broker
    
    def get_current_price(self, symbol):
        """
        Mevcut alış/satış (bid/ask) fiyatlarını alır
        
        Argümanlar:
            symbol: Ticari varlık
            
        Döner:
            Alış, satış ve orta fiyatı içeren sözlük
        """
        # Mevcutsa Soyut Broker Arayüzünü kullan
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

        # DEMO MODU: Simüle edilmiş verileri kullan
        if config.DEMO_MODE:
            from utils.simulated_data import get_simulated_price
            return get_simulated_price(symbol)
        
        # MT5 direkt kullanımı (Yedek olarak duruyor)
        try:
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"{symbol} için fiyat alınamadı")
                return None
            
            return {
                "bid": tick.bid,
                "ask": tick.ask,
                "mid": (tick.bid + tick.ask) / 2,
                "time": datetime.fromtimestamp(tick.time)
            }
        except ImportError:
            logger.error("MetaTrader5 kütüphanesi yüklü değil")
            return None
    
    def get_bars(self, symbol, timeframe, count=500):
        """
        Geçmiş OHLCV mum verilerini alır
        
        Argümanlar:
            symbol: Ticari varlık
            timeframe: "H1", "H4", "D1" vb. zaman dilimi
            count: Alınacak mum sayısı
            
        Döner:
            OHLCV verilerini içeren pandas DataFrame
        """
        # DEMO MODU: Simüle edilmiş verileri kullan
        if config.DEMO_MODE and not hasattr(self.broker, 'get_market_data'):
            from utils.simulated_data import generate_simulated_data
            return generate_simulated_data(symbol, timeframe, count)
        
        # Soyut Broker Arayüzünü kullan
        if hasattr(self.broker, 'get_market_data'):
            return self.broker.get_market_data(symbol, timeframe, limit=count)
            
        # Doğrudan MT5'e geri dön (Eski destek)
        try:
            import MetaTrader5 as mt5
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
                logger.error(f"{symbol} {timeframe} için mum verisi alınamadı")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
        except ImportError:
            return None
    
    def get_multi_timeframe_data(self, symbol, timeframes=None):
        """
        Aynı anda birden fazla zaman dilimi için veri alır
        
        Argümanlar:
            symbol: Ticari varlık
            timeframes: Zaman dilimleri listesi (varsayılanı config'den alır)
            
        Döner:
            Zaman dilimini anahtar, DataFrame'i değer olarak içeren sözlük
        """
        if timeframes is None:
            timeframes = list(config.TIMEFRAMES.keys())
        
        data = {}
        current_price = self.get_current_price(symbol)
        
        for tf in timeframes:
            df = self.get_bars(symbol, tf)
            if df is not None:
                data[tf] = df
        
        # Güncel fiyat bilgisini ekle
        data["current_price"] = current_price["mid"] if current_price else None
        data["symbol"] = symbol
        
        return data
