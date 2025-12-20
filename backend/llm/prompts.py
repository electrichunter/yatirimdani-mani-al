"""
LLM Karar Verme için Sistem Komutları (Prompts) - Self-Learning Odaklı
Halüsinasyonu önlemeye ve hatalardan ders çıkarmaya odaklanmış komutlar
"""

import json


def get_system_prompt():
    """
    Ticaret kararları için ana sistem komutunu döndürür.
    AGRESİF, bilinçli ve 'hatalardan ders çıkaran' bir analist profili.
    """
    return """Sen bir finansal analistsin. Verileri analiz et ve SADECE aşağıdaki JSON formatında yanıt ver. 
Markdown bloğu veya ek açıklama kullanma. <think> bloğunda analizini yap, sonra doğrudan JSON'u yaz.

{
  "karar": "AL/SAT/BEKLE",
  "guven": 75,
  "giris_fiyati": 1.1234,
  "zarar_kes": 1.1200,
  "kar_al": 1.1300,
  "risk_skoru": 40,
  "risk_odul_orani": 2.5,
  "analiz_vadesi": "H1",
  "beklenen_sure": "4 saat",
  "neden": "Analiz açıklaması"
}"""
 


def build_decision_prompt(context, strategy_excerpts=None, learned_patterns=None):
    """
    LLM kararı için tam komut metnini oluşturur (RAG çıkarıldı, Öğrenme eklendi).
    
    Argümanlar:
        context: Teknik sinyaller, haberler ve güncel fiyatı içeren sözlük
        strategy_excerpts: (Artık kullanılmıyor, uyumluluk için duruyor)
        learned_patterns: Geçmiş başarılı ve başarısız işlemlerden öğrenilen veriler
        
    Döner:
        Formatlanmış komut (prompt) dizesi
    """
    symbol = context.get("symbol", "BİLİNMİYOR")
    direction = context.get("direction", "BİLİNMİYOR")
    current_price = context.get("current_price", 0)
    
    # Teknik sinyaller
    technical = context.get("technical_signals", {})
    tech_score = context.get("technical_score", 0)
    
    # Haber duygu analizi
    news_sentiment = context.get("news_sentiment", 0)
    news_list = context.get("relevant_news", [])
    
    # Ekonomik takvim (yaklaşan olaylar)
    upcoming_events = context.get("upcoming_events", [])
    
    # Yön çevirisi
    direction_tr = direction.replace("BUY", "AL").replace("SELL", "SAT").replace("NEUTRAL", "NÖTR")
    
    prompt = f"""TİCARET FIRSATI DEĞERLENDİRMESİ

VARLIK: {symbol}
TAVSİYE EDİLEN YÖN: {direction_tr}
GÜNCEL FİYAT: {current_price}

📊 TEKNİK VERİLER (Puan: {tech_score}/100):
- RSI (H1): {technical.get('rsi', 'N/A')}
- MACD Durumu: {technical.get('macd_signal', {}).get('reason', 'N/A')}
- Trend Analizi: H1:{technical.get('trend_h1', 'N/A')}, H4:{technical.get('trend_h4', 'N/A')}, D1:{technical.get('trend_d1', 'N/A')}
- Hacim Onayı: {technical.get('volume', {}).get('reason', 'N/A')}

📰 HABER VE DUYGU ANALİZİ:
- Genel Duygu Skoru: {news_sentiment} (-100 Çok Negatif / +100 Çok Pozitif)
- İlgili Haber Sayısı: {len(news_list)}
"""
    
    if news_list:
        prompt += "\nÖnemli Haberler:\n"
        for news in news_list[:3]:
            prompt += f"- [{news.get('impact', 'N/A')}] {news.get('title', 'Bilinmiyor')} (Sinyal: {news.get('sentiment', 0)})\n"
    
    # Yaklaşan olaylar
    if upcoming_events:
        prompt += f"\n📅 YAKLAŞAN EKONOMİK OLAYLAR ({len(upcoming_events)}):\n"
        for event in upcoming_events[:3]:
            prompt += f"- {event.get('title', 'N/A')} ({event.get('date', 'TBD')}) [Etki: {event.get('impact', 'N/A')}]\n"

    # 🧠 ÖĞRENİLMİŞ DESENLER EKLE (KARAR VERİRKEN EN ÖNEMLİ BÖLÜM)
    if learned_patterns:
        prompt += "\n🧠 SİSTEM HAFIZASI (GEÇMİŞ İŞLEMLERDEN ÖĞRENİLENLER):\n"
        
        # Başarılı desenler
        success_patterns = [p for p in learned_patterns if p['win_rate'] >= 60]
        if success_patterns:
            prompt += "✅ BAŞARILI KURULUMLAR (Tekrarla):\n"
            for p in success_patterns[:3]:
                prompt += f"- {p['data'].get('h1')}/{p['data'].get('h4')} trendi: %{p['win_rate']} başarı\n"
        
        # Hatalı/Başarısız desenler (Kullanıcı talebi: Hatalarını görsün)
        fail_patterns = [p for p in learned_patterns if p['win_rate'] < 50]
        if fail_patterns:
            prompt += "\n❌ HATALI KURULUMLAR (Kaçın!):\n"
            for p in fail_patterns[:3]:
                prompt += f"- {p['data'].get('h1')}/{p['data'].get('h4')} trend kombinasyonu geçmişte %{100 - p['win_rate']} oranında ZARAR ettirdi.\n"
        
        # Güven analizleri
        if learned_patterns:
            prompt += "\n⚠️ TALİMAT: Eğer mevcut teknik kurulum 'HATALI KURULUMLAR' listesindeki bir desene benziyorsa, güven seviyesini düşür ve BEKLE kararı ver.\n"

    prompt += """
GÖREV: Yukarıdaki verileri ve sistem hafızasını birleştirerek nihai kararı ver.

ANALİZ KRİTERLERİ:
1. Risk/Ödül (RR) oranı mutlaka 1.5 üzerinde olmalıdır. Max RR: 10.0.
2. Analiz yaptığın vadeyi (H1/H4/Günlük) ve işlemin ne kadar süre açık kalması gerektiğini belirt.
3. "neden" kısmında hem teknik verileri hem de 'sistem hafızasından' yararak neden AL veya SAT dediğini açıkla.
4. SADECE JSON formatında yanıt ver. JSON HARİCİ HİÇBİR ŞEY YAZMA. Açıklama ekleme."""
    
    return prompt



def validate_llm_response(response_text):
    """
    LLM JSON yanıtını doğrular ve ayrıştırır.
    Sadece JSON kısmını çekip hataları tolere eder.
    """
    import os
    import re
    import json
    # Alanları eşle
    mapping = {
        "karar": "decision",
        "guven": "confidence",
        "giris_fiyati": "entry_price",
        "iris_fiyati": "entry_price", # Model hatası toleransı
        "zarar_kes": "stop_loss",
        "kar_al": "take_profit",
        "risk_skoru": "risk_score",
        "risk_odul_orani": "rr_ratio",
        "analiz_vadesi": "timeframe",
        "beklenen_sure": "expected_duration",
        "neden": "reasoning"
    }
    
    # Gereksiz düşünce (think) bloklarını tamamen temizle
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    
    # Tüm JSON benzeri blokları bul ({...})
    json_blocks = re.findall(r'(\{.*?\})', response_text, re.DOTALL)
    
    data = None
    for block in json_blocks:
        try:
            # Bloğu temizle ve ayrıştır
            candidate = json.loads(block)
            # Eğer anahtarların çoğu mevcutsa doğru bloğu bulduk demektir
            matches = sum(1 for k in mapping.keys() if k in candidate)
            if matches >= 5:
                data = candidate
                break
        except:
            continue
            
    if not data:
        # Son çare: Tüm metni temizle ve en baştan en sona parantezleri ara
        try:
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1:
                data = json.loads(response_text[start:end+1])
        except:
            return None

    if not data: return None

    # Eğer model JSON içine JSON koyarsa (DeepSeek hatası)
    # Bazen key olarak tüm şablonu yazıp value olarak sonucu koyuyor
    # Bu durumda en uzun string değere sahip anahtarı veya iç içe objeyi bulmalıyız
    if len(data) > 0:
        for k, v in data.items():
            if isinstance(v, dict) and sum(1 for subk in mapping.keys() if subk in v) >= 3:
                data = v
                break
            if isinstance(v, str) and v.startswith("{"):
                try:
                    sub_data = json.loads(v)
                    if sum(1 for subk in mapping.keys() if subk in sub_data) >= 3:
                        data = sub_data
                        break
                except: pass
    
    result = {}
    for tr, en in mapping.items():
        val = data.get(tr)
        # Sayısal alanları dönüştür
        if en in ["entry_price", "stop_loss", "take_profit", "risk_reward_ratio"]:
            try: result[en] = float(val) if val is not None else 0.0
            except: result[en] = 0.0
        elif en in ["confidence", "risk_score"]:
            try: result[en] = int(val) if val is not None else 0
            except: result[en] = 0
        else:
            result[en] = val if val is not None else "Belirtilmedi"

    # Kararı standardize et
    d = str(result.get("decision", "")).upper()
    if "AL" in d or "BUY" in d: result["decision"] = "BUY"
    elif "SAT" in d or "SELL" in d: result["decision"] = "SELL"
    else: result["decision"] = "PASS"

    return result
