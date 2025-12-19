"""
3. Aşama: LLM Karar Motoru (Self-Learning Odaklı)
Yapay zeka ile teknik ve temel verilerin harmanlanması
Hatalarından ders çıkaran öğrenme sistemi entegreli
"""

import config
from llm.ollama_client import OllamaClient
from llm.prompts import get_system_prompt, build_decision_prompt, validate_llm_response
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger("LLMDecision")


class LLMDecisionEngine:
    """
    LLM karar verme sistemi - RAG devre dışı, Öğrenme Sistemi aktif.
    Sadece 1. ve 2. aşama geçilirse yüklenir (Gecikmeli Yükleme)
    """
    
    def __init__(self, model_name=None, rag_data_path=None):
        """
        Argümanlar:
            model_name: Kullanılacak LLM modeli (varsayılanı config'den alır)
            rag_data_path: (Devre dışı bırakıldı)
        """
        logger.info("🔧 LLM Karar Motoru Başlatılıyor...")
        
        # Yapılandırmaya göre LLM istemcisini başlat
        if config.USE_GEMINI_API:
            from llm.gemini_client import GeminiClient
            self.llm = GeminiClient(model_name=config.GEMINI_MODEL)
            logger.info("✅ Gemini API kullanılıyor (bulut tabanlı)")
        else:
            from llm.ollama_client import OllamaClient
            self.llm = OllamaClient(model_name=model_name)
            logger.info("✅ Ollama kullanılıyor (yerel)")
        
        # RAG artık bu projenin konusu değil - Tamamen devre dışı
        self.vector_store = None
        self.doc_loader = None
        if config.ENABLE_RAG:
            logger.warning("⚠️ RAG yapılandırmada açık olmasına rağmen bu sürümde devre dışı bırakıldı.")
        
        # Öğrenme sistemini başlat (Hatalardan ders çıkarma merkezi)
        from utils.learning_system import TradePerformanceTracker
        self.learning_system = TradePerformanceTracker()
        
        logger.info("✅ LLM Karar Motoru 'Hatalardan Öğrenme' yeteneğiyle başlatıldı")
    
    def make_decision(self, context):
        """
        Öğrenilmiş desenler ve LLM kullanarak nihai ticaret kararını verir
        
        Argümanlar:
            context: Teknik sinyaller, haberler ve güncel fiyatı içeren sözlük
                
        Döner:
            Karar, güven seviyesi ve giriş/SL/TP fiyatlarını içeren sözlük
        """
        symbol = context.get("symbol", "BİLİNMİYOR")
        
        try:
            # ========================================
            # ÖĞRENME: Geçmiş başarı/hata desenlerini al
            # ========================================
            
            learned_patterns = None
            try:
                # Son 30 gündeki başarılı ve başarısız işlemleri analiz et
                learned_patterns = self.learning_system.get_learned_patterns(days_back=30)
                if learned_patterns:
                    logger.debug(f"🧠 {len(learned_patterns)} öğrenilmiş desen karar sürecine ekleniyor")
            except Exception as e:
                logger.warning(f"Öğrenilmiş desenler yüklenemedi: {str(e)}")
            
            # ========================================
            # LLM: Tek seferlik analiz (ana döngü pass'lerinde kullanılacak)
            # Bu metot her çağrıldığında tek bir LLM çalıştırılır, kaydedilir ve
            # öğrenme sistemi için pattern analizi başlatılır.
            # ========================================

            system_prompt = get_system_prompt()
            user_prompt = build_decision_prompt(context, [], learned_patterns)

            logger.debug(f"🤖 Karar için LLM ({self.llm.model_name}) çağrılıyor...")

            response_text = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=config.LLM_TEMPERATURE
            )

            logger.info("=" * 30 + " HAM LLM YANITI " + "=" * 30)
            logger.info(response_text if response_text else "BOŞ YANIT")
            logger.info("=" * 78)

            if not response_text:
                logger.error("❌ LLM yanıt üretemedi")
                return {
                    "decision": "PASS",
                    "confidence": 0,
                    "reasoning": "LLM çıkarımı başarısız",
                    "entry_price": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_reward_ratio": 0
                }

            decision_data = validate_llm_response(response_text)
            if not decision_data:
                logger.error("❌ LLM yanıt doğrulaması başarısız")
                return {
                    "decision": "PASS",
                    "confidence": 0,
                    "reasoning": "Geçersiz LLM yanıt formatı",
                    "entry_price": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_reward_ratio": 0
                }

            # Eğer güven düşükse, BEKLEMEDE KAL olarak işaretle (gösterim için)
            if decision_data.get("confidence", 0) < config.MIN_CONFIDENCE:
                logger.info(f"⚠️ Güven %{decision_data.get('confidence')}, eşiğin (%{config.MIN_CONFIDENCE}) altında")
                decision_data["decision"] = "BEKLEMEDE KAL"
                current_reason = decision_data.get("reasoning") or ""
                decision_data["reasoning"] = f"Güven seviyesi (%{decision_data.get('confidence',0)}) çok düşük. " + current_reason
                decision_data["entry_price"] = "BEKLEMEDE"
                decision_data["stop_loss"] = "BEKLEMEDE"
                decision_data["take_profit"] = "BEKLEMEDE"

            # Not: log_trade_decision artık main.py'de merkezi olarak yapılıyor.
            # Böylece mükerrer (duplicate) kayıtların önüne geçiliyor.

            # Kısa bekleme yok; ana döngü pass'leri arasında bekleme uygulanacak
            result_for_log = {
                "pass": decision_data.get("decision") != "PASS",
                "confidence": decision_data.get("confidence", 0),
                "reason": decision_data.get("reasoning", "")
            }
            log_trade_decision(logger, symbol, 3, result_for_log)

            return decision_data
        except Exception as e:
            logger.error(f"❌ LLM karar motorunda hata: {str(e)}")
            return {
                "decision": "PASS",
                "confidence": 0,
                "reasoning": f"Karar motoru hatası: {str(e)}",
                "entry_price": 0,
                "stop_loss": 0,
                "take_profit": 0,
                "risk_reward_ratio": 0
            }

    def self_assess(self, context):
        """
        Eğer LLM sürekli 0 güven döndürüyorsa, LLM kendi başına kapsamlı bir analiz yapar.
        Bu metot önce LLM'e daha zengin bir 'self-assess' prompt'u gönderir; eğer LLM
        uygun yanıt vermezse basit bir heuristic fallback ile karar üretir.
        """
        symbol = context.get('symbol', 'BILINMIYOR')
        system_prompt = get_system_prompt()

        # Derinlemesine kendi analizini iste
        user_prompt = """
Lütfen aşağıdaki verilerle kapsamlı bir ticaret analizi yap:
- Teknik sinyaller ve teknik skor: {technical_score}
- Teknik sinyaller ayrıntısı: {technical_signals}
- Haber duygu skoru: {news_sentiment}
- Önemli haberler: {relevant_news}
- Yaklaşan ekonomik olaylar: {upcoming_events}
- Mevcut fiyat: {current_price}
- Önerilen yön (ön analizden): {direction}

Analizi teknik, temel ve psikolojik boyutlarda kısa ve net şekilde yap. Sonuçta JSON formatında
şu alanları ver: decision (BUY/SELL/BEKLE), confidence (0-100), reasoning, entry_price, stop_loss, take_profit, timeframe, expected_duration.
Eğer kesin karar verilemiyorsa BEKLE ver.
""".format(
            technical_score=context.get('technical_score'),
            technical_signals=context.get('technical_signals'),
            news_sentiment=context.get('news_sentiment'),
            relevant_news=context.get('relevant_news'),
            upcoming_events=context.get('upcoming_events'),
            current_price=context.get('current_price'),
            direction=context.get('direction')
        )

        try:
            logger.info(f"🔎 {symbol} için LLM self-assessment başlatılıyor...")
            response_text = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0
            )

            logger.info("LLM self-assess yanıtı alındı")
            decision_data = validate_llm_response(response_text)
            if decision_data:
                decision_data['reasoning'] = f"[LLM Self-Assessment] {decision_data.get('reasoning','') }"
                return decision_data
        except Exception as e:
            logger.warning(f"LLM self-assess hata: {e}")

        # Fallback heuristic
        try:
            tech = context.get('technical_score', 0) or 0
            news = context.get('news_sentiment', 0) or 0
            direction = context.get('direction', 'BUY')

            # Basit puanlama: teknik ağırlıklı
            score = int(max(0, min(100, tech * 0.7 + (news + 50) * 0.3)))

            if tech >= 50 or score >= 50:
                decision = direction
            else:
                # Eğer teknik zayıf ama haber çok pozitif/negatif, o yöne git
                if news >= 40:
                    decision = 'BUY'
                elif news <= -40:
                    decision = 'SELL'
                else:
                    decision = 'BEKLE'

            reasoning = f"Heuristic self-assess => Teknik: {tech}/100, Haber: {news}, hesaplanan puan: {score}."
            # Belirgin giriş/SL/TP hesaplayıcı yoksa None bırak
            return {
                'decision': decision,
                'confidence': score if decision != 'BEKLE' else 10,
                'reasoning': reasoning,
                'entry_price': context.get('current_price') or 0,
                'stop_loss': None,
                'take_profit': None,
                'timeframe': context.get('timeframe', 'H1'),
                'expected_duration': 'Kısa',
            }
        except Exception as e:
            logger.error(f"Self-assess fallback hata: {e}")
            return None
