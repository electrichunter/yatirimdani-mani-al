# 🎯 Trading Bot Yeni Özellikler

## ✨ Yapılan İyileştirmeler

### 1. 📊 100+ Farklı Varlık Desteği
Bot artık aşağıdaki varlıkları analiz edebilir:

#### Forex (38 çift)
- **Major Pairs**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, vb.
- **Cross Pairs**: EURGBP, EURJPY, GBPJPY, AUDJPY, vb.
- **Exotic Pairs**: USDTRY, USDZAR, USDMXN, USDBRL, USDRUB, vb.

#### Emtialar (18 varlık)
- **Değerli Madenler**: Altın (GC=F), Gümüş (SI=F), Platin, Paladyum
- **Enerji**: Ham Petrol (CL=F), Brent, Doğal Gaz
- **Tarım**: Mısır, Buğday, Kahve, Şeker, Pamuk, vb.

#### İndeksler (18 indeks)
- **ABD**: S&P 500, Dow Jones, NASDAQ, Russell 2000
- **Avrupa**: FTSE 100, DAX, CAC 40, Euro Stoxx 50
- **Asya**: Nikkei 225, Hang Seng, Shanghai, ASX 200

#### Kripto Paralar (20 coin)
- BTC, ETH, BNB, XRP, ADA, SOL, DOT, vb.

#### Türk Varlıklar (6 hisse)
- BIST 100, Garanti, Ereğli, THY, Akbank, Tüpraş

**TOPLAM: 100+ Varlık**

---

### 2. 📅 Ekonomik Takvim Entegrasyonu (Gelecek Haberler)

#### Nedir?
Bot artık gelecek ekonomik olayları dikkate alarak işlem önerileri sunar.

#### Desteklenen Olay Tipleri:
- ✅ Merkez Bankası Kararları (Fed, ECB, BoE, BoJ)
- ✅ İstihdam Verileri (NFP, İşsizlik Oranı)
- ✅ Enflasyon Verileri (TÜFE, ÜFE)
- ✅ Ekonomik Konuşmalar
- ✅ Düzenleme Açıklamaları (özellikle kripto için)

#### Nasıl Çalışır?
1. Her sembol analiz edilirken, ilgili ülkenin gelecek 7 günlük ekonomik takvimi kontrol edilir
2. Yüksek ve orta etkili olaylar LLM'e iletilir
3. LLM, yaklaşan olayları dikkate alarak risk değerlendirmesi yapar
4. **Örnek**: Yarın Fed faiz kararı varsa ve yüksek etkili ise, LLM daha temkinli davranır

---

### 3. 🇹🇷 Tam Türkçe Destek

#### Sistem Mesajları Türkçe:
```
✅ Sistem başlatıldı
📊 İzlenen Varlıklar: 100 adet
⏱️ Kontrol Aralığı: 300s (5.0 dakika)
✅ Min Güven: %90
```

#### Sinyal Çıktıları Türkçe:
```
🎯 TİCARET SİNYALİ
📊 Varlık: EURUSD=X
📍 Yön: 🟢 ALIM (AL)
💰 Giriş Fiyatı: 1.08500
🛑 Zarar Kes (SL): 1.08200 (30.0 pip uzakta)
🎯 Kar Al (TP): 1.09100 (60.0 pip uzakta)
📦 Pozisyon Büyüklüğü: 0.1 lot
⚖️ Risk/Ödül Oranı: 2.0:1
✅ Güven Seviyesi: %95
💡 NEDEN: H1 ve H4'te güçlü boğa trendi var. RSI 45 seviyesinde ve yükseliş için alan var. ECB'nin yarınki konuşması Euro için pozitif beklentiler yaratıyor.
```

#### LLM Açıklamaları Türkçe:
- LLM'e verilen talimat: "NEDEN alanını MUTLAKA Türkçe ve detaylı yaz!"
- Tüm açıklamalar artık Türkçe döner
- 2-3 cümle ile detaylı analiz

---

### 4. 📈 Gelişmiş TP/SL/Giriş Gösterimi

#### Önceki Format:
```
Entry: 1.08500
Stop Loss: 1.08200
Take Profit: 1.09100
```

#### Yeni Format:
```
💰 Giriş Fiyatı: 1.08500
🛑 Zarar Kes (SL): 1.08200 (30.0 pip uzakta)
🎯 Kar Al (TP): 1.09100 (60.0 pip uzakta)
⚖️ Risk/Ödül Oranı: 2.0:1
```

#### Pip Hesaplama:
- **Forex**: Otomatik pip hesaplama (JPY çiftleri için özel hesaplama)
- **Kripto/Hisse/İndeks**: Fiyat farkı olarak gösterilir

---

## 🚀 Kullanım

### Otomatik Başlatma (100+ Varlık):
```bash
python main.py --auto
```

### Manuel Başlatma:
```bash
python baslat.bat
```

### Sadece Test (İlk 3 Varlık):
`config.py` dosyasında:
```python
SYMBOLS = ["EURUSD=X", "GBPUSD=X", "GC=F"]  # Test için
```

---

## 📋 Ekonomik Takvim Özellikleri

### Otomatik Ülke Tespiti
```python
EURUSD=X  →  USD olayları izlenir
GBPJPY=X  →  JPY olayları izlenir
BTC-USD   →  USD + Kripto düzenleme olayları
XU100.IS  →  TRY olayları izlenir
```

### Cache Sistemi
- İlk çalışmada ekonomik takvim yüklenir
- 6 saat boyunca cache'te tutulur
- Gereksiz API çağrıları önlenir

### API Entegrasyonu (Gelecek Geliştirme)
Şu an örnek veriler kullanılıyor. Gerçek üretimde entegre edilebilir:
- Forex Factory API
- Investing.com Economic Calendar
- TradingView Calendar API

---

## 🎯 Örnek Çıktı

```
============================================================
🔍 Analyzing EURUSD=X
============================================================
💰 EURUSD=X Güncel Fiyat: 1.08523
✅ EURUSD=X - 1. Aşama GEÇİLDİ (Puan: 75/100, Yön: AL)
✅ EURUSD=X - 2. Aşama GEÇİLDİ (Duygu Skoru: 65.0)

📅 GELECEK EKONOMİK TAKVİM OLAYLARI (3 olay):
- 2025-12-18 15:30: ABD İşsizlik Başvuruları [MEDIUM Etki]
- 2025-12-20 21:00: ABD Tarım Dışı İstihdam (NFP) [HIGH Etki]
- 2025-12-22 20:00: Fed Faiz Kararı (FOMC) [HIGH Etki]

============================================================
🎯 TİCARET SİNYALİ / TRADE RECOMMENDATION
============================================================
📊 Varlık: EURUSD=X

📍 Yön: 🟢 ALIM (AL)
💰 Giriş Fiyatı: 1.08520
🛑 Zarar Kes (SL): 1.08220 (30.0 pip uzakta)
🎯 Kar Al (TP): 1.09120 (60.0 pip uzakta)

📦 Pozisyon Büyüklüğü: 0.1 lot
⚖️ Risk/Ödül Oranı: 2.00:1
✅ Güven Seviyesi: %92

💡 NEDEN: H1 ve H4 zaman dilimlerinde güçlü yükseliş trendi gözlemleniyor. RSI 48 seviyesinde ve yükseliş için alan var. Yaklaşan Fed toplantısı öncesi piyasa pozitif beklentilere sahip. Haber duygusu nötr-pozitif aralıkta. Risk/ödül oranı 2:1 olarak mükemmel seviyede.
============================================================
```

---

## ⚙️ Yapılandırma

### config.py'de Ayarlar:
```python
# 100+ varlığın tamamını kullan
SYMBOLS = [...] # Otomatik yüklenmiş

# Veya sadece belirli kategorileri kullan
SYMBOLS = [s for s in SYMBOLS if "=X" in s]  # Sadece Forex
SYMBOLS = [s for s in SYMBOLS if "-USD" in s]  # Sadece Kripto
```

### Ekonomik Takvim Ayarları:
```python
# utils/economic_calendar.py dosyasında:
days_ahead = 7  # Kaç gün ilerisini kontrol et
min_impact = "MEDIUM"  # Minimum etki seviyesi (LOW, MEDIUM, HIGH)
```

---

## 🔄 Güncellemeler

### v2.0 - Aralık 2025
- ✅ 100+ varlık desteği eklendi
- ✅ Ekonomik takvim entegrasyonu
- ✅ Tam Türkçe arayüz
- ✅ Gelişmiş TP/SL gösterimi (pip mesafesi)
- ✅ Emoji'li görsel çıktılar
- ✅ Gelecek haberlerin dikkate alınması

### Gelecek Özellikler:
- 🔜 Canlı ekonomik takvim API entegrasyonu
- 🔜 Telegram/Discord bildirim desteği
- 🔜 Web dashboard (gerçek zamanlı sinyal izleme)
- 🔜 Backtest sistemi (geçmiş performans analizi)

---

## 📚 Teknik Detaylar

### Ekonomik Takvim Modülü
**Dosya**: `utils/economic_calendar.py`

**Özellikler**:
- Sembolden otomatik ülke tespiti
- 6 saatlik cache sistemi
- Etki seviyesine göre filtreleme
- Tarihe göre sıralama

**Kullanım**:
```python
from utils.economic_calendar import EconomicCalendar

calendar = EconomicCalendar()
events = calendar.get_upcoming_events(
    symbol="EURUSD=X",
    days_ahead=7,
    min_impact="MEDIUM"
)
```

### LLM Prompt Güncellemeleri
**Dosya**: `llm/prompts.py`

**Değişiklikler**:
- Sistem promptu Türkçe
- Gelecek olaylar için özel bölüm
- Turkish-to-English field mapping
- Karar değerlerinin çevirisi (AL/SAT/BEKLE ↔ BUY/SELL/PASS)

---

## 🎓 Öğrenme Sistemi

Bot, yaptığı başarılı ve başarısız işlemlerden öğrenmeye devam ediyor:

```
🧠 ÖĞRENİLMİŞ DESENLER (geçmiş başarılı işlemlerden):
- Trend Deseni: H1=YUKARI, H4=YUKARI, D1=YUKARI
  Kazanma Oranı: %78 (23 işlem)
  Ort. Kazanç: 45.2 pip
```

---

## 💡 İpuçları

1. **İlk Çalıştırma**: İlk kez çalıştırırken sembol sayısını azaltın (test için)
2. **API Limitleri**: Yahoo Finance API limitleri var, çok sık tarama yapmayın
3. **Ekonomik Takvim**: Gerçek API entegrasyonu için bir ekonomik takvim servisi kullanın
4. **Güven Seviyesi**: MIN_CONFIDENCE = 90 yüksek bir seviye, test için 70-80 yapabilirsiniz

---

## 🆘 Destek

Sorularınız için:
- GitHub Issues
- Dokümantasyon: README.md, WALKTHROUGH.md
- Log dosyaları: `logs/trading.log`
