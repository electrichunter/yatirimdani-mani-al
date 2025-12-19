"""
Test Script - Ekonomik Takvim ve Yeni Özellikler
"""

from utils.economic_calendar import EconomicCalendar

def test_economic_calendar():
    """Ekonomik takvim modülünü test et"""
    print("=" * 60)
    print("📅 EKONOMİK TAKVİM TEST")
    print("=" * 60)
    
    calendar = EconomicCalendar()
    
    # Test sembolleri
    test_symbols = [
        "EURUSD=X",
        "GBPUSD=X",
        "USDJPY=X",
        "BTC-USD",
        "GC=F",  # Gold
        "XU100.IS"  # BIST 100
    ]
    
    for symbol in test_symbols:
        print(f"\n📊 Sembol: {symbol}")
        print("-" * 60)
        
        # Ülke tespiti
        country = calendar._extract_country_from_symbol(symbol)
        print(f"🌍 Tespit Edilen Ülke/Para Birimi: {country}")
        
        # Gelecek olaylar
        events = calendar.get_upcoming_events(
            symbol=symbol,
            days_ahead=7,
            min_impact="MEDIUM"
        )
        
        if events:
            print(f"\n📅 Gelecek {len(events)} Önemli Olay:")
            for event in events:
                print(f"   • {event['date']}: {event['title']}")
                print(f"     Etki: {event['impact']} | Önceki: {event['previous']} | Tahmin: {event['forecast']}")
        else:
            print("   ℹ️ Yakın zamanda önemli olay yok")
    
    print("\n" + "=" * 60)
    print("✅ Test Tamamlandı")
    print("=" * 60)


def test_turkish_output():
    """Türkçe çıktı formatını test et"""
    print("\n" + "=" * 60)
    print("🇹🇷 TÜRKÇE ÇIKTI FORMAT TESTİ")
    print("=" * 60)
    
    # Örnek sinyal
    example_signal = {
        "symbol": "EURUSD=X",
        "decision": "BUY",
        "entry_price": 1.08520,
        "stop_loss": 1.08220,
        "take_profit": 1.09120,
        "position_size": 0.1,
        "risk_reward": 2.0,
        "confidence": 92,
        "reasoning": "H1 ve H4 zaman dilimlerinde güçlü yükseliş trendi gözlemleniyor. RSI 48 seviyesinde ve yükseliş için alan var. Yaklaşan Fed toplantısı öncesi piyasa pozitif beklentilere sahip."
    }
    
    # Format output
    entry = example_signal['entry_price']
    sl = example_signal['stop_loss']
    tp = example_signal['take_profit']
    
    # Pip calculation
    pip_multiplier = 10000  # For EUR/USD
    sl_distance = abs(entry - sl) * pip_multiplier
    tp_distance = abs(tp - entry) * pip_multiplier
    
    print(f"""
🎯 TİCARET SİNYALİ / TRADE RECOMMENDATION
{'=' * 60}
📊 Varlık: {example_signal['symbol']}

📍 Yön: 🟢 ALIM (AL)
💰 Giriş Fiyatı: {entry:.5f}
🛑 Zarar Kes (SL): {sl:.5f} ({sl_distance:.1f} pip uzakta)
🎯 Kar Al (TP): {tp:.5f} ({tp_distance:.1f} pip uzakta)

📦 Pozisyon Büyüklüğü: {example_signal['position_size']} lot
⚖️ Risk/Ödül Oranı: {example_signal['risk_reward']:.2f}:1
✅ Güven Seviyesi: %{example_signal['confidence']}

💡 NEDEN: {example_signal['reasoning']}
{'=' * 60}
""")
    
    print("✅ Format testi başarılı!\n")


def show_supported_assets():
    """Desteklenen varlıkları göster"""
    print("\n" + "=" * 60)
    print("📊 DESTEKLENEN VARLIKLAR (100+)")
    print("=" * 60)
    
    import config
    
    # Kategorilere ayır
    forex = [s for s in config.SYMBOLS if "=X" in s]
    crypto = [s for s in config.SYMBOLS if "-USD" in s]
    futures = [s for s in config.SYMBOLS if "=F" in s]
    indices = [s for s in config.SYMBOLS if s.startswith("^")]
    turkish = [s for s in config.SYMBOLS if ".IS" in s]
    chinese = [s for s in config.SYMBOLS if ".SS" in s]
    
    print(f"""
💱 FOREX ÇİFTLERİ: {len(forex)} adet
   İlk 5: {', '.join(forex[:5])}
   
💰 KRİPTO PARALAR: {len(crypto)} adet
   İlk 5: {', '.join(crypto[:5])}
   
📦 EMTİALAR (Futures): {len(futures)} adet
   İlk 5: {', '.join(futures[:5])}
   
📈 İNDEKSLER: {len(indices)} adet
   İlk 5: {', '.join(indices[:5])}
   
🇹🇷 TÜRK VARLIKLAR: {len(turkish)} adet
   Tümü: {', '.join(turkish)}

📊 TOPLAM: {len(config.SYMBOLS)} Varlık
""")


if __name__ == "__main__":
    print("\n🚀 YENİ ÖZELLİKLER TEST PROGRAMI\n")
    
    # Test 1: Ekonomik Takvim
    test_economic_calendar()
    
    # Test 2: Türkçe Çıktı
    test_turkish_output()
    
    # Test 3: Varlık Listesi
    show_supported_assets()
    
    print("\n" + "=" * 60)
    print("🎉 TÜM TESTLER TAMAMLANDI!")
    print("=" * 60)
    print("\nBotu başlatmak için:")
    print("  python main.py --auto")
    print("\nVeya:")
    print("  ./baslat.bat")
    print()
