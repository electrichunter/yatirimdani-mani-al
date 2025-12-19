
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

class YFinanceBroker:
    """
    MT5Broker yerine YFinance için birleşik bir broker arayüzü.
    Sadece veri çekme sağlar. İşlem yürütme simüle edilir.
    """
    
    def __init__(self):
        self.name = "YFinance (Sadece Veri)"
        self.initialized = True
        self.logger = logging.getLogger("SniperBot")
        self.logger.info("✅ YFinance Broker Başlatıldı")

    def get_market_data(self, symbol, timeframe, limit=100):
        """
        Yahoo Finance'den piyasa verilerini çek
        
        Argümanlar:
            symbol (str): Sembol adı (örn. 'EURUSD=X', 'AAPL')
            timeframe (str): Zaman dilimi (örn. 'M1', 'H1', 'D1')
            limit (int): Mum sayısı (yfinance tarafından yoksayılır, periyoda göre çekeriz)
            
        Döner:
            pd.DataFrame: OHLCV verileri
        """
        # MT5 zaman dilimlerini YFinance aralıklarına eşle
        tf_map = {
            "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
            "H1": "1h", "H4": "1h", # yfinance'de 4h yoktur, 1h kullanıp gerekirse yeniden örnekleriz
            "D1": "1d", "W1": "1wk", "MN1": "1mo"
        }
        
        interval = tf_map.get(timeframe, "1d")
        
        if interval in ["1m", "2m", "5m", "15m", "30m", "90m"]:
            period = "5d"
        elif "h" in interval:
            period = "1mo" # 1h/4h için 100+ mum için ~1 ay gerekir
        elif "d" in interval:
            period = "1y" # 1d için 100+ mum için 1 yıl gerekir
        else:
            period = "1y" # Varsayılan
            
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df is None or df.empty:
                # Periyot çok uzunsa güvenli varsayılanlarla tekrar dene
                df = ticker.history(period="1y", interval=interval) if period != "1y" else None
                if df is None or df.empty:
                    self.logger.warning(f"{symbol} için {interval} aralığında veri bulunamadı")
                    return None
                
            # Mevcut kodla uyumluluk için özelleştir (MTBroker formatı)
            # YF döner: Open, High, Low, Close, Volume, Dividends, Stock Splits
            # Bize lazım: time, open, high, low, close, tick_volume, spread, real_volume
            
            # Tarih/Saat sütununu sütun olarak almak için indeksi sıfırla
            df.reset_index(inplace=True)
            
            # Sütun isimlerini küçük harfe çevir
            df.columns = [c.lower() for c in df.columns]
            
            # 'date' veya 'datetime' ismini 'time' olarak değiştir
            if 'date' in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            elif 'datetime' in df.columns:
                df.rename(columns={'datetime': 'time'}, inplace=True)
                
            # Zamanın datetime nesnesi olduğundan emin ol
            df['time'] = pd.to_datetime(df['time'])
            
            # Botun beklediği eksik sütunları ekle
            df['tick_volume'] = df['volume']
            df['spread'] = 0
            df['real_volume'] = df['volume']
            
            # Zamana göre sırala
            df.sort_values(by='time', inplace=True)
            
            # İstenen miktarla sınırla
            if limit > 0:
                df = df.tail(limit)
                
            # DataFetcher beklentilerine uyması için zamanı indeks olarak ayarla
            df.set_index('time', inplace=True)
                
            return df
            
        except Exception as e:
            self.logger.error(f"{symbol} için YFinance Hatası: {e}")
            return None

    def get_current_price(self, symbol):
        """En son fiyatı al"""
        try:
            ticker = yf.Ticker(symbol)
            # Döviz çiftleri bazen info kısmında sorunlu olabildiği için önce geçmişe bak
            df = ticker.history(period="1d", interval="1m")
            if not df.empty:
                return float(df['Close'].iloc[-1])
            
            # Yedek olarak fast_info kullan
            info = ticker.fast_info
            if hasattr(info, 'last_price') and info.last_price is not None:
                 return float(info.last_price)
                
            return None
        except Exception as e:
            self.logger.error(f"{symbol} için fiyat alma hatası: {e}")
            return None
            
    def place_order(self, symbol, action, volume, entry=None, sl=None, tp=None, comment=""):
        """
        Simüle edilmiş emir iletimi
        """
        self.logger.info(f"📝 SANAL İŞLEM: {action} {symbol} Hacim:{volume} SL:{sl} TP:{tp}")
        return {
            "success": True,
            "ticket": 123456,
            "price": entry if entry else self.get_current_price(symbol),
            "volume": volume,
            "error": None
        }

    def get_balance(self):
        """Simüle edilmiş bakiye"""
        return 10000.0

    def get_open_positions(self):
        """Simüle edilmiş açık pozisyonlar"""
        return []

    def close(self):
        """Temizlik"""
        pass
