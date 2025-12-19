# 📰 Gerçek Zamanlı Haber Entegrasyonu Rehberi

## 🎯 Sistem Nasıl Çalışıyor?

Bot artık otomatik olarak ekonomik haberleri çekebilir:
- 📊 **Ekonomik göstergeler** (GDP, İşsizlik, Enflasyon)
- 📰 **Forex haberleri** (Reuters, Bloomberg, vb.)
- 📅 **Economic calendar** (Yaklaşan önemli olaylar)

---

## 🔑 API Key'lerini Alın

### 1. NewsAPI (Önerilen - Ücretsiz Başlangıç)

**Ücretsiz Plan:**
- Günde 100 istek
- Son 1 ay haber
- Yeterli kaynak

**Nasıl alınır:**
1. [newsapi.org](https://newsapi.org) → "Get API Key"
2. Ücretsiz hesap oluştur
3. API key'i kopyala

**Ücretli Plan:** $50/ay (sınırsız)

---

### 2. Alpha Vantage (Ücretsiz)

**Ücretsiz Plan:**
- Günde 25 istek
- Ekonomik göstergeler (GDP, CPI, vb.)
- Yeterli temel haber için

**Nasıl alınır:**
1. [alphavantage.co](https://www.alphavantage.co/support/#api-key)
2. Email ile ücretsiz key al

---

## 🔧 Kurulum

### 1. .env Dosyasına Ekle

```bash
# .env dosyasını aç
notepad .env
```

Ekle:
```
NEWSAPI_KEY=your_newsapi_key_here
ALPHAVANTAGE_KEY=your_alphavantage_key_here
```

### 2. Haberleri İlk Kez Çek

```bash
python update_news.py
```

Göreceksiniz:
```
============================================================
📰 News Update Started - 2025-12-17 14:30:00
============================================================
✅ NewsAPI: 45 haber eklendi
✅ Alpha Vantage: 4 gösterge eklendi
✅ News Update Complete - 49 new articles
============================================================
```

---

## 🤖 Ana Botta Kullanım

Artık bot otomatik olarak bu haberleri kullanacak:

```python
# Stage 2: News Filter
# Otomatik olarak veritabanındaki haberleri kontrol eder
stage2_result = news_filter.check_sentiment(
    symbol="EURUSD",
    direction="BUY",
    hours_lookback=24
)

# LLM'e gönderilen context:
# - "Fed faiz kararı beklentisi yükseldi"
# - "ABD tarım verileri beklenenden iyi"
# - "EUR/USD'de yükseliş bekleniyor"
```

---

## ⏰ Otomatik Güncelleme

### Manuel (Her İhtiyacınızda):
```bash
python update_news.py
```

### Otomatik (Her Saat):

`update_news.py` dosyasını düzenle:
```python
if __name__ == "__main__":
    # Bu satırı yoruma al:
    # update_news()
    
    # Bu satırı aktif et:
    run_continuous(interval_minutes=60)  # Her saat
```

Sonra çalıştır:
```bash
python update_news.py
```

### Windows Task Scheduler ile (Önerilen):

1. Task Scheduler'ı aç
2. "Create Basic Task" → "News Updater"
3. Trigger: "Daily" → Her saat tekrarla
4. Action: Program başlat
   - Program: `C:\Users\ouysa\OneDrive\Masaüstü\yatırımdanışmanı-al\venv\Scripts\python.exe`
   - Arguments: `update_news.py`
   - Start in: `C:\Users\ouysa\OneDrive\Masaüstü\yatırımdanışmanı-al`

---

## 📊 Haber Kalitesi

Bot otomatik olarak:
- ✅ **Sentiment analizi** yapar (bullish/bearish)
- ✅ **İlgili sembolleri** bulur
- ✅ **Etki seviyesi** belirler (HIGH/MEDIUM/LOW)
- ✅ **Gereksiz haberleri** filtreler

### Örnek Haber:

```
Title: "Fed Signals Rate Hike May Continue"
Source: Reuters
Sentiment: -60 (Bearish for USD pairs)
Impact: HIGH
Symbols: EURUSD, GBPUSD, USDJPY
```

Bot bunu şöyle kullanır:
```
❌ EURUSD BUY sinyali reddedildi
   Çünkü: Fed'in faiz artışı EUR/USD için bearish
```

---

## 💡 İleri Seviye: Özel Haber Kaynakları

### Kendi Haber Kaynağınızı Ekleyin:

`utils/news_fetcher.py` dosyasını açın ve yeni bir sınıf ekleyin:

```python
class CustomNewsFetcher:
    def fetch_news(self):
        # Kendi mantığınız
        pass
```

### Web Scraping (Dikkatli Kullanın):

```python
# Investing.com, Forex Factory vb. için
# BeautifulSoup kullanarak scrape edebilirsiniz
# Ancak ToS'u kontrol edin!
```

---

## ⚠️ Önemli Notlar

1. **API Limitleri:**
   - NewsAPI: 100/gün (ücretsiz)
   - Alpha Vantage: 25/gün
   - Fazla istek göndermeyin!

2. **Haber Gecikmesi:**
   - Ücretsiz planlar genelde 15-30 dakika gecikir
   - Gerçek zamanlı için ücretli plan gerekli

3. **Sentiment Analizi:**
   - Şu anki sistem basit (keyword-based)
   - Daha iyi için: FinBERT modeli kullanılabilir

4. **Maliyet:**
   - Ücretsiz planlar çoğu trader için yeterli
   - Pro trader: NewsAPI Pro ($50/ay)

---

## 🚀 Test Edin

```bash
# 1. Haberleri çek
python update_news.py

# 2. Botu başlat
python main.py

# 3. Log'larda göreceksiniz:
# "Stage 2: News sentiment aligned with BUY direction"
# "Recent news: [HIGH] Fed signals dovish tone..."
```

---

## 📞 Sorun mu var?

### "No news found"
→ `update_news.py` çalıştırın

### "API key not found"
→ `.env` dosyasını kontrol edin

### "Rate limit exceeded"
→ Daha az sıklıkta güncelleyin

---

**Artık botunuz ekonomik haberleri takip ediyor! 🎉**
