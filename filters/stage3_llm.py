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
            # LLM: Karar üret (Öğrenilmiş desenlerle)
            # ========================================
            
            system_prompt = get_system_prompt()
            # RAG devre dışı olduğu için boş liste gönderiyoruz
            user_prompt = build_decision_prompt(context, [], learned_patterns)
            
            logger.debug(f"🤖 Karar için LLM ({self.llm.model_name}) çağrılıyor...")
            
            # LLM yanıtını al
            response_text = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=config.LLM_TEMPERATURE
            )
            
            # HAM GÜNLÜK AKIŞI
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
            
            # ========================================
            # Yanıtı doğrula ve ayrıştır
            # ========================================
            
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
            
            # ========================================
            # Güven eşiğini uygula
            # ========================================
            
            if decision_data["confidence"] < config.MIN_CONFIDENCE:
                logger.info(f"⚠️ Güven %{decision_data['confidence']}, eşiğin (%{config.MIN_CONFIDENCE}) altında")
                decision_data["decision"] = "BEKLEMEDE KAL"
                current_reason = decision_data.get("reasoning") or ""
                decision_data["reasoning"] = f"Güven seviyesi (%{decision_data['confidence']}) çok düşük. " + current_reason
                # Fiyatları 'BEKLEMEDE' olarak işaretle (Dashboard'da görünmesi için)
                decision_data["entry_price"] = "BEKLEMEDE"
                decision_data["stop_loss"] = "BEKLEMEDE"
                decision_data["take_profit"] = "BEKLEMEDE"
            
            # Sonucu günlükle
            result_for_log = {
                "pass": decision_data["decision"] != "PASS",
                "confidence": decision_data["confidence"],
                "reason": decision_data["reasoning"]
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
