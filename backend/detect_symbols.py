"""
MT5 Sembol Tespiti
Broker'daki mevcut sembolleri listeler
"""

import config
import MetaTrader5 as mt5

# MT5'i başlat
if not mt5.initialize():
    print(f"❌ MT5 başlatılamadı: {mt5.last_error()}")
    exit()

# Login from config (which pulls from .env)
authorized = mt5.login(
    login=config.MT5_LOGIN,
    password=config.MT5_PASSWORD,
    server=config.MT5_SERVER
)

if not authorized:
    print(f"⚠️ Login başarısız (Hata: {mt5.last_error()}), varsayılan hesap deneniyor...")

print("=" * 60)
print("📊 MT5 BAĞLANTİ BİLGİLERİ")
print("=" * 60)

account = mt5.account_info()
if account:
    print(f"✅ Hesap: {account.login}")
    print(f"✅ Server: {account.server}")
    print(f"✅ Balance: ${account.balance}")
else:
    print("❌ Hesap bilgisi alınamadı")

print("\n" + "=" * 60)
print("🔍 SEMBOL TARAMASI")
print("=" * 60)

# Tüm sembolleri al
symbols = mt5.symbols_get()
print(f"\nToplam {len(symbols)} sembol bulundu\n")

# Aradığımız sembolleri bul
target_symbols = ["EUR", "GBP", "XAU", "USD", "GOLD"]

print("İstenen Semboller:")
print("-" * 60)

for target in target_symbols:
    matches = [s.name for s in symbols if target in s.name.upper()]
    if matches:
        print(f"\n{target} içeren semboller:")
        for match in matches[:10]:  # İlk 10
            symbol_info = mt5.symbol_info(match)
            if symbol_info:
                status = "✅ Aktif" if symbol_info.visible else "⚠️ Pasif"
                print(f"  {status} {match}")

print("\n" + "=" * 60)
print("💡 ÖNERİLEN CONFIG")
print("=" * 60)

# En yaygın forex sembolleri
common = ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"]
found_symbols = []

for symbol in common:
    # Direkt arama
    if mt5.symbol_info(symbol):
        found_symbols.append(symbol)
        continue
    
    # Ek ile arama (.m, .pro, .b, vb.)
    for ext in [".m", ".pro", ".b", ".raw", ".ecn", ""]:
        test_symbol = symbol + ext
        if mt5.symbol_info(test_symbol):
            found_symbols.append(test_symbol)
            break

if found_symbols:
    print("\nconfig.py'de kullanılacak semboller:")
    print(f'SYMBOLS = {found_symbols}')
else:
    print("\n❌ Hiçbir sembol bulunamadı!")

mt5.shutdown()
