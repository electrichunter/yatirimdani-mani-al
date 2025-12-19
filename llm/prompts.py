"""
System Prompts for LLM Decision Making
Anti-hallucination focused prompts
"""

import json


def get_system_prompt():
    """
    Get the main system prompt for trading decisions
    Updated for AGGRESSIVE but informed trading
    """
    return """Sen profesyonel bir algoritmik ticaret analistisin. Görevin piyasa fırsatlarını yakalamak ve karlı işlemler açmaktır.

SİSTEM FELSEFESİ:
"Fırsatları kaçırma, riskleri yönet." Her varlık (EURUSD, Altın, Gümüş vb.) kendine has davranışlara sahiptir. Analizini bu sembolün özel karakteristiğine ve mevcut ekonomik takvime göre yap.

KRİTİK KURALLAR:
1. SADECE geçerli JSON formatında yanıt vermelisin (JSON dışında açıklama yok)
2. Kararını teknik sinyaller, haber duygusu ve risk/ödül dengesine dayandır
3. Güven %70 üzerindeyse işlem önerisinde bulunabilirsin
4. Riskli işlemlere (Risk Skoru > 70) izin verilir, ancak nedenini "neden" kısmında açıkla
5. NEDEN alanını MUTLAKA Türkçe yaz

ÇIKTI FORMATI (geçerli JSON) - BU SIRALAMAYA UYUN:
{
  "karar": "AL" | "SAT" | "BEKLE",
  "guven": 0-100,
  "giris_fiyati": float,
  "zarar_kes": float,
  "kar_al": float,
  "risk_skoru": 0-100,
  "risk_odul_orani": float,
  "beklenen_sure": "Örn: 2 saat",
  "neden": "Türkçe detaylı açıklama"
}"""
 


def build_decision_prompt(context, strategy_excerpts, learned_patterns=None):
    """
    Build the complete prompt for LLM decision
    
    Args:
        context: Dict with technical signals, news, current price
        strategy_excerpts: List of relevant strategy text chunks from RAG
        learned_patterns: Dict of learned successful patterns (from previous trades)
        
    Returns:
        Formatted prompt string
    """
    symbol = context.get("symbol", "UNKNOWN")
    direction = context.get("direction", "UNKNOWN")
    current_price = context.get("current_price", 0)
    
    # Technical signals
    technical = context.get("technical_signals", {})
    tech_score = context.get("technical_score", 0)
    
    # News sentiment
    news_sentiment = context.get("news_sentiment", 0)
    news_list = context.get("relevant_news", [])
    
    # Economic calendar (upcoming events)
    upcoming_events = context.get("upcoming_events", [])
    
    # Direction translation
    direction_tr = direction.replace("BUY", "AL").replace("SELL", "SAT").replace("NEUTRAL", "NÖTR")
    
    # Build strategy knowledge section
    strategy_text = "\n\n".join([
        f"Strateji Alıntısı {i+1}:\n{excerpt}"
        for i, excerpt in enumerate(strategy_excerpts[:3])  # Top 3 excerpts
    ])
    
    prompt = f"""TİCARET FIRSATI DEĞERLENDİRMESİ

SİMGE: {symbol}
ÖNERİLEN YÖN: {direction_tr}
GÜNCEL FİYAT: {current_price}

TEKNİK ANALİZ (1. Aşama Puanı: {tech_score}/100):
- RSI: {technical.get('rsi', 'N/A')}
- MACD Sinyali: {technical.get('macd_signal', {}).get('reason', 'N/A')}
- Trend H1: {technical.get('trend_h1', 'N/A')}
- Trend H4: {technical.get('trend_h4', 'N/A')}
- Trend D1: {technical.get('trend_d1', 'N/A')}
- Hacim: {technical.get('volume', {}).get('reason', 'N/A')}

HABER DUYGUSU (2. Aşama):
- Ortalama Duygu: {news_sentiment} (-100 düşüş eğilimli / +100 yükseliş eğilimli)
- Son Haber Sayısı: {len(news_list)}
"""
    
    if news_list:
        prompt += "\nÖnemli Haber Başlıkları:\n"
        for news in news_list[:3]:
            prompt += f"- [{news.get('impact', 'N/A')}] {news.get('title', 'Bilinmiyor')} (Duygu: {news.get('sentiment', 0)})\n"
    
    # Add upcoming economic events
    if upcoming_events:
        prompt += f"\n📅 GELECEK EKONOMİK TAKVİM OLAYLARI ({len(upcoming_events)} olay):\n"
        prompt += "Yaklaşan önemli ekonomik veriler - bu fırsatı değerlendirirken dikkate al:\n\n"
        for event in upcoming_events[:5]:  # Top 5 upcoming events
            prompt += f"- {event.get('date', 'TBD')}: {event.get('title', 'N/A')} [{event.get('impact', 'N/A')} Etki]\n"
            prompt += f"  Ülke: {event.get('country', 'N/A')} | Önceki: {event.get('previous', 'N/A')} | Tahmin: {event.get('forecast', 'N/A')}\n"
        prompt += "\n⚠️ DİKKAT: Yaklaşan yüksek etkili olaylar önceinde pozisyon risk değerlendirmesini etkiler!\n"
    
    prompt += f"\n\nSTRATEJİ BİLGİSİ (ticaret kitaplarından):\n{strategy_text}\n\n"
    
    # Add learned patterns (SELF-LEARNING)
    if learned_patterns and learned_patterns.get("trend_patterns"):
        prompt += "\n🧠 ÖĞRENİLMİŞ DESENLER (geçmiş başarılı işlemlerden):\n"
        prompt += "Aşağıdaki desenler tarihsel olarak yüksek kazanç oranı göstermiştir:\n\n"
        
        for pattern in learned_patterns.get("trend_patterns", [])[:3]:
            prompt += f"- Trend Deseni: H1={pattern['h1']}, H4={pattern['h4']}, D1={pattern['d1']}\n"
            prompt += f"  Kazanma Oranı: %{pattern['win_rate']} ({pattern['sample_size']} işlem)\n"
            prompt += f"  Ort. Kazanç: {pattern['avg_win']} pip\n\n"
        
        if learned_patterns.get("confidence_analysis"):
            prompt += "\nGüven Seviyesi Analizi:\n"
            for conf in learned_patterns.get("confidence_analysis", []):
                prompt += f"- {conf['range']}: %{conf['win_rate']} kazanma oranı ({conf['sample_size']} işlem)\n"
    
    prompt += """
GÖREV: Piyasa verilerini incele ve bir karar ver. 

KRİTİK TALİMATLAR:
1. Risk/Ödül oranı >= 1.5 olmak zorundadır.
2. Giriş fiyatı, Zarar Kes (SL) ve Kar Al (TP) seviyelerini kesin rakamlarla belirt.
3. 'neden' alanını çok detaylı doldur. Özellikle:
   - Neden "AL" veya "SAT" dediğini teknik göstergelerle (RSI, Trend vb.) açıkla.
   - Yaklaşan haberlerin kararındaki etkisini belirt.
   - Risk skoru belirleme mantığını anlat.
   - Bu alan tamamen Türkçe ve profesyonel bir analiz diliyle yazılmalıdır.
4. Sadece JSON yanıt ver. Boş alan bırakma."""
    
    return prompt



def validate_llm_response(response_text):
    """
    Validate and parse LLM JSON response
    Includes auto-closing and regex failsafe for truncated responses
    """
    import os
    import re
    import json
    
    # DEBUG: Save raw response
    try:
        os.makedirs("testllm", exist_ok=True)
        with open("testllm/raw_response.txt", "w", encoding="utf-8") as f:
            f.write(response_text)
    except Exception as e:
        print(f"Error saving debug log: {e}")

    if not response_text:
        return None

    # 1. PRE-CLEANING
    clean_text = response_text.strip()
    
    # 2. MAIN JSON PARSING with AUTO-CLOSING
    data = None
    
    # Try to extract the JSON part
    json_match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
    candidate = json_match.group(1) if json_match else clean_text
    
    # Auto-closing logic for truncated responses
    for suffix in ["", "}", '" }', '"] }', '"] } }', '", "neden": "Analiz yarım kaldı." }']:
        try:
            temp_candidate = candidate + suffix
            data = json.loads(temp_candidate)
            if data: break
        except:
            continue

    # 3. FAILSAFE: REGEX EXTRACTION (If auto-closing failed)
    if not data:
        data = {}
        # Lenovo/Flexible regex for key fields (handle missing/truncated values)
        patterns = {
            "karar": r'"karar":\s*"?([A-ZÇĞİÖŞÜ]*)', 
            "guven": r'"guven":\s*(\d+)?',
            "giris_fiyati": r'"giris_fiyati":\s*([\d\.]*)',
            "zarar_kes": r'"zarar_kes":\s*([\d\.]*)',
            "kar_al": r'"kar_al":\s*([\d\.]*)',
            "risk_skoru": r'"risk_skoru":\s*(\d+)?',
            "risk_odul_orani": r'"risk_odul_orani":\s*([\d\.]*)',
            "beklenen_sure": r'"beklenen_sure":\s*"([^"]*)"?',
            "neden": r'"neden":\s*"([^"]*)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text)
            if match:
                val = match.group(1)
                try:
                    if key in ["guven", "risk_skoru"]: data[key] = int(val)
                    elif key in ["giris_fiyati", "zarar_kes", "kar_al", "risk_odul_orani"]: data[key] = float(val)
                    else: data[key] = val
                except: data[key] = val

    if not data or "karar" not in data:
        return None

    # 4. FIELD MAPPING & NORMALIZATION
    mapping = {
        "karar": "decision",
        "guven": "confidence",
        "giris_fiyati": "entry_price",
        "zarar_kes": "stop_loss",
        "kar_al": "take_profit",
        "risk_skoru": "risk_score",
        "risk_odul_orani": "risk_reward_ratio",
        "beklenen_sure": "expected_duration",
        "neden": "reasoning"
    }
    
    normalized = {}
    for tr, en in mapping.items():
        if tr in data and data[tr] is not None: 
            normalized[en] = data[tr]
        else: 
            if "price" in en or "ratio" in en or "score" in en: normalized[en] = 0.0
            elif en == "confidence": normalized[en] = 0
            else: normalized[en] = "Analiz yarım kaldı (Otomatik kurtarıldı)"
    
    # Ensure decision is present for translation
    if "decision" not in normalized or normalized["decision"] is None:
        normalized["decision"] = "PASS"

    # 5. STRICT NUMERIC CASTING (Safety First)
    numeric_floats = ["entry_price", "stop_loss", "take_profit", "risk_reward_ratio"]
    numeric_ints = ["confidence", "risk_score"]
    
    for field in numeric_floats:
        try:
            if normalized[field] is None: normalized[field] = 0.0
            normalized[field] = float(normalized[field])
        except:
            normalized[field] = 0.0
            
    for field in numeric_ints:
        try:
            if normalized[field] is None: normalized[field] = 0
            normalized[field] = int(float(normalized[field])) # float->int handle 72.0 case
        except:
            normalized[field] = 0
    
    # 6. DECISION TRANSLATION
    d = str(normalized["decision"]).upper()
    if any(x in d for x in ["AL", "ALIM", "BUY"]): normalized["decision"] = "BUY"
    elif any(x in d for x in ["SAT", "SATIM", "SELL"]): normalized["decision"] = "SELL"
    else: normalized["decision"] = "PASS"
    
    return normalized

