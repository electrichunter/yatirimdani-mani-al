# 🚀 Hızlı Başlangıç Rehberi

## 📋 DRY RUN Modu (Önerilen)

Bot şu anda **DRY RUN** modunda çalışacak şekilde ayarlandı. Bu demektir ki:
- ✅ Tüm analizi yapar
- ✅ İşlem önerilerini gösterir
- ❌ Gerçek işlem AÇMAZ

Bu sayede:
1. Botun nasıl çalıştığını görürsünüz
2. Önerilerin kalitesini test edersiniz
3. Hiçbir risk almazsınız

---

## 1️⃣ Adım 1: Gerekli Programları Yükle

### Ollama Kurulumu
1. [ollama.ai](https://ollama.ai) adresinden Ollama'yı indirin
2. Yükledikten sonra PowerShell/Terminal'de:

```bash
# Llama 3.2 3B modelini çek (2.5GB VRAM)
ollama pull llama3.2:3b

# Ollama'yı başlat (her zaman arka planda çalışmalı)
ollama serve
```

### Python Virtual Environment

```bash
# Proje klasörüne git
cd "C:\Users\ouysa\OneDrive\Masaüstü\yatırımdanışmanı-al"

# Virtual environment oluştur
python -m venv venv

# Aktif et (Windows)
venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt
```

---

## 2️⃣ Adım 2: MT5 Ayarları (İsteğe Bağlı)

DRY RUN modunda MT5'e bağlanmadan da çalışabilir, ama bağlanırsa gerçek fiyatları kullanır.

`.env.example` dosyasını `.env` olarak kopyalayın ve doldurun:

```
MT5_LOGIN=12345678
MT5_PASSWORD=şifreniz
MT5_SERVER=broker_server_adı
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

---

## 3️⃣ Adım 3: Botu Çalıştır

```bash
# Ollama'nın çalıştığından emin ol
ollama serve

# Başka bir terminal'de botu başlat
python main.py
```

### Göreceğiniz Çıktı:

```
============================================================
🎯 SNIPER TRADING BOT - INITIALIZATION
============================================================
Start Time: 2025-12-17 14:22:00
Mode: 📋 DRY RUN (Recommendations Only)
LLM Model: llama3.2:3b
Trading Symbols: EURUSD, GBPUSD, XAUUSD
Check Interval: 300s (5.0 minutes)
Min Confidence: 90%
Min Risk/Reward: 2.0:1
============================================================

🔍 Analyzing EURUSD
============================================================
❌ EURUSD - Stage 1 FAILED: Score 45 below threshold 70

🔍 Analyzing GBPUSD
============================================================
✅ GBPUSD - Stage 1 PASSED (Score: 75/100, Direction: BUY)
✅ GBPUSD - Stage 2 PASSED (Sentiment: 60.0)
🤖 Calling LLM for decision...
🎯 SNIPER MODE ACTIVATED - GBPUSD
   Decision: BUY
   Confidence: 92%
   Reasoning: Strong trend alignment with positive sentiment

============================================================
🚀 TRADE RECOMMENDATION
============================================================
   Symbol: GBPUSD
   Direction: BUY
   Entry: 1.2650
   Stop Loss: 1.2600
   Take Profit: 1.2750
   Position Size: 0.1 lots
   Risk/Reward: 2.0:1
   Confidence: 92%
   Reasoning: Strong trend alignment with positive sentiment
============================================================
📋 DRY RUN MODE - Trade NOT executed (recommendation only)
   To enable real trading, set DRY_RUN = False in config.py
============================================================
```

---

## 4️⃣ Ne Zaman Gerçek İşlem Açmalı?

**EN AZ 1 HAFTA** DRY RUN modunda çalıştırın ve:

- [ ] Log'ları inceleyin
- [ ] Önerilerin mantıklı olduğunu doğrulayın
- [ ] Win rate takibi yapın (kağıt üzerinde)
- [ ] VRAM kullanımını kontrol edin
- [ ] Sistem hatalarını düzeltin

### Gerçek İşleme Geçiş:

`config.py` dosyasında:

```python
# Değiştir:
DRY_RUN = True

# Şu şekilde:
DRY_RUN = False
```

⚠️ **UYARI**: İlk gerçek testi **DEMO HESAPTA** yapın!

---

## 📊 Önemli Notlar

### Model Seçimi
Şu anda `llama3.2:3b` kullanıyor (hızlı, 2.5GB VRAM).

Daha iyi performans için:
```python
# config.py'de değiştir:
LLM_MODEL = "llama3.1:8b-instruct-q4_K_M"  # ~3.8GB VRAM
```

### Strateji PDF'leri (İsteğe Bağlı)
Trading stratejisi kitaplarınızı:
```
data/strategies/
```
klasörüne koyun. Bot bu bilgileri kullanarak daha iyi kararlar verecek.

### Haber Veritabanı (İsteğe Bağlı)
Test haberleri eklemek için:

```python
from filters.stage2_news import NewsFilter

nf = NewsFilter()
nf.add_sample_news()
```

---

## 🔧 Sorun Giderme

### "Ollama server not responding"
```bash
# Yeni terminal'de:
ollama serve
```

### "Model not found"
```bash
ollama pull llama3.2:3b
```

### "No module named 'MetaTrader5'"
```bash
pip install MetaTrader5
```

### Hiç sinyal görmüyorum
Bu normal! Sniper modu MÜKEMMEL koşulları bekler. Bazen:
- Günde 0-1 sinyal olabilir
- Test için `TECHNICAL_MIN_SCORE` değerini geçici olarak düşürebilirsiniz (config.py'de)

---

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. `logs/trading.log` dosyasını kontrol edin
2. `logs/errors.log` dosyasına bakın
3. Terminaldeki hata mesajlarını okuyun

---

## ✅ Başarı Kontrolü

Bot doğru çalışıyorsa göreceksiniz:

```
✅ Ollama connected, model 'llama3.2:3b' available
✅ Connected to MT5: YourBroker-Server
✅ System initialization complete
✅ RAG knowledge base ready (XX documents)
🔍 Analyzing symbols...
```

**Başarılar! 🎯**
