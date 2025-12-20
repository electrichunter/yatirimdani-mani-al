"""
Google Gemini API İstemcisi (Yeni google-genai SDK için güncellendi)
Garantili JSON çıktısı ile bulut tabanlı LLM çıkarımı
Hızlı, güvenilir ve ücretsiz kota mevcuttur
"""

import os
import json
import config
from google import genai
from google.genai.types import GenerateContentConfig
from utils.logger import setup_logger

logger = setup_logger("GeminiClient")


class GeminiClient:
    """Google Gemini API İstemcisi (yeni google-genai SDK kullanılarak)"""
    
    def __init__(self, model_name=None, api_key=None):
        """
        Argümanlar:
            model_name: Kullanılacak model (varsayılan: gemini-2.0-flash)
            api_key: Gemini API anahtarı (varsayılanı env'den alır)
        """
        # Yapılandırmadan gelen veya sağlanan ismi kullan
        self.model_name = (model_name or config.GEMINI_MODEL or "gemini-3-flash-preview")
        
        # GenAI SDK, model isimlerini 'models/' ön eki olmadan bekler
        if self.model_name.startswith("models/"):
            self.model_name = self.model_name.replace("models/", "")
            
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("❌ Ortam değişkenlerinde GEMINI_API_KEY bulunamadı")
            logger.error("   .env dosyasına ekleyin: GEMINI_API_KEY=anahtar_buraya")
            raise ValueError("GEMINI_API_KEY eksik")
        
        # İstemciyi başlat
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(f"✅ Gemini API '{self.model_name}' modeli ile başlatıldı")
    
    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """
        Gemini'den yanıt üret
        """
        try:
            # JSON için katı şema tanımla - ÖNCE KRİTİK ALANLAR
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "karar": {"type": "STRING", "description": "Karar: AL, SAT veya BEKLE"},
                    "guven": {"type": "INTEGER", "description": "Güven 0-100"},
                    "giris_fiyati": {"type": "NUMBER"},
                    "zarar_kes": {"type": "NUMBER"},
                    "kar_al": {"type": "NUMBER"},
                    "risk_skoru": {"type": "INTEGER", "description": "Risk skoru 0-100"},
                    "risk_odul_orani": {"type": "NUMBER"},
                    "analiz_vadesi": {"type": "STRING", "description": "Analiz vadesi (H1, H4 vb.)"},
                    "beklenen_sure": {"type": "STRING", "description": "Beklenen süre"},
                    "neden": {"type": "STRING", "description": "Türkçe detaylı açıklama"}
                },
                "required": ["karar", "guven", "giris_fiyati", "zarar_kes", "kar_al", "risk_skoru", "risk_odul_orani", "analiz_vadesi", "beklenen_sure", "neden"]
            }

            config_gen = GenerateContentConfig(
                temperature=temperature if temperature is not None else config.LLM_TEMPERATURE,
                top_p=getattr(config, "LLM_TOP_P", 0.1),
                max_output_tokens=max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS,
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction=system_prompt if system_prompt else None
            )
            
            # Basit tekrar deneme ile içerik üret
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config_gen
                    )
                    
                    if response:
                        # HATA AYIKLAMA: Meta verileri günlükle
                        if hasattr(response, 'candidates') and response.candidates:
                            reason = response.candidates[0].finish_reason
                            if reason != "STOP":
                                logger.warning(f"⚠️ Gemini Bitiş Nedeni: {reason}")
                        
                        if response.text:
                            return response.text
                    
                    logger.error("❌ Gemini boş yanıt döndürdü")
                    return None
                        
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries:
                        logger.warning(f"⚠️ Gemini İstek Sınırı (429). 60 saniye içinde tekrar deneniyor...")
                        import time
                        time.sleep(60)
                        continue
                    else:
                        raise e
        except Exception as e:
            logger.error(f"❌ Gemini Seçim Hatası: {str(e)}")
            return None
    
    def generate_json(self, prompt, system_prompt=None):
        """
        JSON yanıt üret (zaten Gemini yapılandırmasıyla garanti edilir)
        
        Argümanlar:
            prompt: Kullanıcı komutu
            system_prompt: Sistem komutu
            
        Döner:
            Ayrıştırılmış JSON sözlüğü veya başarısız olursa None
        """
        response_text = self.generate(prompt, system_prompt, temperature=0.1)
        
        if not response_text:
            return None
        
        # JSON ayrıştırmayı dene
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON yanıtı ayrıştırılamadı: {str(e)}")
            logger.debug(f"Ham yanıt: {response_text[:200]}...")
            return None
