# 🎯 Sniper Trading Bot - Hızlı Başlangıç

## 🆕 Yeni Özellikler (v2.0)

### ✨ Bu Güncellemede Neler Var?

1. **📊 100+ Varlık Desteği**
   - 38 Forex çifti (Major + Cross + Exotic)
   - 18 Emtia (Değerli madenler, Enerji, Tarım)
   - 18 Global İndeks
   - 20 Kripto para
   - 6 Türk hisse senedi
   - **TOPLAM: 100+ varlık!**

2. **📅 Ekonomik Takvim Entegrasyonu**
   - Gelecek 7 günlük önemli ekonomik olaylar
   - Fed, ECB, BoE kararları otomatik takip
   - NFP, TÜFE, İşsizlik verileri
   - LLM'in risk analizinde kullanma

3. **🇹🇷 Tam Türkçe Arayüz**
   - Tüm sistem mesajları Türkçe
   - LLM açıklamaları Türkçe
   - Emoji'li görsel çıktılar
   - Kullanıcı dostu format

4. **📈 Gelişmiş Sinyal Formatı**
   - TP, SL, Giriş fiyatları net gösterim
   - Pip mesafesi hesaplama
   - Risk/Ödül oranı vurgulu
   - Türkçe detaylı açıklama (NEDEN alanı)

---

## 🚀 Hızlı Başlatma

### 1. Botu Başlat (Otomatik Mod - 100 Varlık)
```bash
python main.py --auto
```

### 2. Veya Manuel Mod
```bash
python baslat.bat
```
Sonra ekranda:
- Veri kaynağı: **G** (Gerçek piyasa - Yahoo Finance)
- İşlem modu: **S** (Sinyal - sadece öneriler, gerçek işlem yok)

---

## 📊 Örnek Çıktı

```
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

💡 NEDEN: H1 ve H4 zaman dilimlerinde güçlü yükseliş trendi 
gözlemleniyor. RSI 48 seviyesinde ve yükseliş için alan var. 
Yaklaşan Fed toplantısı öncesi piyasa pozitif beklentilere sahip. 
Haber duygusu nötr-pozitif aralıkta. Risk/ödül oranı 2:1 olarak 
mükemmel seviyede.
============================================================
```

---

## ⚙️ Temel Ayarlar

### Varlık Seçimi (config.py)

#### Tüm 100+ Varlık (Varsayılan):
```python
# Hiçbir şey değiştirmeyin, otomatik yüklenmiş
```

#### Sadece Forex:
```python
SYMBOLS = [s for s in SYMBOLS if "=X" in s]
```

#### Sadece Kripto:
```python
SYMBOLS = [s for s in SYMBOLS if "-USD" in s]
```

#### Sadece Türk Varlıklar:
```python
SYMBOLS = [s for s in SYMBOLS if ".IS" in s]
```

#### Manuel Seçim:
```python
SYMBOLS = ["EURUSD=X", "BTC-USD", "GC=F", "^GSPC"]
```

---

## 🎓 3 Aşamalı Filtreleme Sistemi

### 1️⃣ **Teknik Analiz Filtresi** (1-2 saniye)
- RSI, MACD, Trend analizi
- Hacim kontrolü
- %90'ı elenir ❌

### 2️⃣ **Haber Duygu Filtresi** (0.5 saniye)
- Son 24 saat haber analizi
- Sentiment skoru kontrolü
- **YENİ**: Gelecek ekonomik olaylar 📅
- %5-7'si geçer ✅

### 3️⃣ **LLM Karar Motoru** (2-5 saniye)
- RAG ile strateji bilgisi
- Öğrenilmiş desenler 🧠
- **YENİ**: Türkçe detaylı açıklama
- Güven > %90 olanlar işleme alınır 🎯

---

## 📅 Ekonomik Takvim Özellikleri

### Otomatik Ülke Tespiti:
```
EURUSD=X  →  USD ekonomik verileri izlenir
GBPJPY=X  →  JPY ekonomik verileri izlenir  
BTC-USD   →  USD + Kripto düzenleme haberleri
GC=F      →  USD (emtialar USD bazlı)
```

### Takip Edilen Olaylar:
- ✅ Merkez Bankası Faiz Kararları (Fed, ECB, BoE, BoJ)
- ✅ İstihdam Verileri (NFP, İşsizlik)
- ✅ Enflasyon Verileri (TÜFE, ÜFE)
- ✅ Ekonomik Konuşmalar
- ✅ Kripto Düzenleme Açıklamaları

### LLM'e İletim:
```
📅 GELECEK EKONOMİK TAKVİM OLAYLARI (2 olay):
- 2025-12-20 21:00: ABD Tarım Dışı İstihdam (NFP) [HIGH Etki]
- 2025-12-22 20:00: Fed Faiz Kararı (FOMC) [HIGH Etki]

⚠️ DİKKAT: Yaklaşan yüksek etkili olaylar pozisyon risk 
değerlendirmesini etkiler!
```

---

## 🔧 İleri Seviye Ayarlar

### Güven Eşiği (config.py):
```python
MIN_CONFIDENCE = 90  # Çok seçici (önerilen)
# MIN_CONFIDENCE = 80  # Orta seviye
# MIN_CONFIDENCE = 70  # Daha fazla sinyal
```

### Risk/Ödül Oranı:
```python
MIN_RISK_REWARD_RATIO = 2.0  # En az 2:1 (önerilen)
# MIN_RISK_REWARD_RATIO = 1.5  # Daha gevşek
```

### Tarama Sıklığı:
```python
CHECK_INTERVAL = 300  # 5 dakika (önerilen)
# CHECK_INTERVAL = 600  # 10 dakika
# CHECK_INTERVAL = 60   # 1 dakika (API limitlerine dikkat!)
```

---

## 📋 Test Modu

Yeni özellikleri test etmek için:

```bash
python test_new_features.py
```

Bu script test eder:
- ✅ Ekonomik takvim çalışması
- ✅ Türkçe çıktı formatı
- ✅ 100+ varlık listesi
- ✅ Ülke tespiti

---

## 🎯 İlk Kullanım Önerileri

1. **İlk çalıştırma**: 3-5 sembol ile test edin
2. **Güven seviyesi**: MIN_CONFIDENCE = 85 ile başlayın
3. **Kontrol aralığı**: 5-10 dakika yapın (API limitleri)
4. **DRY_RUN**: Kesinlikle True bırakın (sadece öneriler)

### Örnek Test Konfigürasyonu:
```python
# config.py
SYMBOLS = ["EURUSD=X", "BTC-USD", "GC=F"]
MIN_CONFIDENCE = 85
CHECK_INTERVAL = 600  # 10 dakika
DRY_RUN = True  # Sadece öneriler
```

---

## 📁 Dosya Yapısı

```
yatırımdanışmanı-al/
├── config.py                    # ⚙️ Ana yapılandırma (100+ sembol)
├── main.py                      # 🚀 Ana program (Türkçe arayüz)
├── YENİ_ÖZELLİKLER.md          # 📖 Bu dosya
├── test_new_features.py         # 🧪 Test scripti
│
├── filters/
│   ├── stage1_technical.py      # 1️⃣ Teknik analiz
│   ├── stage2_news.py           # 2️⃣ Haber filtresi
│   └── stage3_llm.py            # 3️⃣ LLM karar (Türkçe)
│
├── llm/
│   └── prompts.py               # 🇹🇷 Türkçe promptlar
│
├── utils/
│   ├── economic_calendar.py     # 📅 YENİ: Ekonomik takvim
│   └── ...
│
└── logs/
    └── trading.log              # 📝 Tüm sinyaller burada
```

---

## 🆘 Sorun Giderme

### API Limitleri
Yahoo Finance'te çok fazla istek yapmayın:
```python
CHECK_INTERVAL = 600  # 10 dakika yapın
```

### Ekonomik Takvim Boş
İlk çalıştırmada örnek veriler yüklenir. Gerçek API için:
```python
# utils/economic_calendar.py
# _get_sample_events() yerine gerçek API ekleyin
```

### LLM Türkçe Cevap Vermiyor
Ollama modelini kontrol edin:
```bash
ollama list
ollama pull tinyllama:latest
```

---

## 📚 Detaylı Dokümantasyon

- **Başlangıç Rehberi**: `BAŞLANGIÇ.md`
- **Detaylı Kullanım**: `WALKTHROUGH.md`
- **Yeni Özellikler**: `YENİ_ÖZELLİKLER.md` (bu dosya)
- **MT5 Sorunları**: `MT5_TROUBLESHOOTING.md`

---

## 🎉 Başarılı Kurulum!

Bot şimdi hazır:
- ✅ 100+ varlık desteği
- ✅ Ekonomik takvim entegrasyonu
- ✅ Tam Türkçe arayüz
- ✅ Gelişmiş TP/SL/Giriş gösterimi
- ✅ Gelecek haberleri dikkate alma

**Botu başlatın:**
```bash
python main.py --auto
```

veya

```bash
./baslat.bat
```

İyi işlemler! 🚀📈
