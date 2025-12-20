
from core.broker_yfinance import YFinanceBroker
import pandas as pd

def test_yfinance():
    print("🚀 YFinance Bağlantı Testi Başlatılıyor...")
    
    broker = YFinanceBroker()
    
    symbols = ["EURUSD=X", "GBPUSD=X", "GC=F"]
    
    for symbol in symbols:
        print(f"\n🔍 {symbol} verisi alınıyor...")
        df = broker.get_market_data(symbol, "H1", limit=10)
        
        if df is not None and not df.empty:
            print(f"✅ {symbol} verisi başarıyla alındı:")
            # 'time' is index, so just print index and columns
            print(df.tail(3)[['open', 'high', 'low', 'close', 'tick_volume']])
            
            price = broker.get_current_price(symbol)
            print(f"💰 Güncel Fiyat: {price}")
        else:
            print(f"❌ {symbol} verisi ALINAMADI!")

    print("\n✅ Test Tamamlandı.")

if __name__ == "__main__":
    test_yfinance()
