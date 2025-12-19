"""
Yerel LLM Çıkarımı için Ollama İstemcisi
RTX 3050 4GB VRAM için optimize edilmiştir
"""

import requests
import json
import config
from utils.logger import setup_logger

logger = setup_logger("OllamaClient")


class OllamaClient:
    """Ollama API İstemcisi"""
    
    def __init__(self, model_name=None, host=None):
        """
        Argümanlar:
            model_name: Kullanılacak model (varsayılanı config'den alır)
            host: Ollama ana bilgisayar URL'si (varsayılan localhost)
        """
        self.model_name = model_name or config.LLM_MODEL
        self.host = host or "http://127.0.0.1:11434"
        self.api_url = f"{self.host}/api/generate"
        
        # Ollama'nın çalışıp çalışmadığını kontrol et
        self.check_connection()
    
    def check_connection(self):
        """Ollama sunucusunun çalıştığını doğrula"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                if self.model_name in model_names:
                    logger.info(f"✅ Ollama bağlandı, '{self.model_name}' modeli mevcut")
                else:
                    logger.warning(f"⚠️ '{self.model_name}' modeli bulunamadı. Mevcut modeller: {model_names}")
                    logger.warning(f"   Çalıştırın: ollama pull {self.model_name}")
            else:
                logger.error("❌ Ollama sunucusu yanıt vermiyor")
        
        except requests.RequestException as e:
            logger.error(f"❌ {self.host} adresindeki Ollama'ya bağlanılamıyor")
            logger.error(f"   Ollama'nın çalıştığından emin olun: ollama serve")
            logger.error(f"   Hata: {str(e)}")
    
    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """
        Ollama'dan yanıt üret
        
        Argümanlar:
            prompt: Kullanıcı komutu
            system_prompt: Sistem komutu
            temperature: Örnekleme sıcaklığı (varsayılanı config'den alır)
            max_tokens: Üretilecek maksimum token sayısı (varsayılanı config'den alır)
            
        Döner:
            Üretilen metin yanıtı
        """
        if temperature is None:
            temperature = config.LLM_TEMPERATURE
        
        if max_tokens is None:
            max_tokens = config.LLM_MAX_TOKENS
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": getattr(config, "LLM_TOP_P", 0.1),
                "num_ctx": getattr(config, "LLM_CONTEXT_WINDOW", 2048)
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.debug(f"🤖 Ollama'ya ({self.model_name}) istek gönderiliyor...")
            
            response = requests.post(self.api_url, json=payload, timeout=180)  # 4GB GPU'lar için 180s yapıldı
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                logger.debug(f"✅ LLM yanıtı alındı ({len(generated_text)} karakter)")
                
                return generated_text
            else:
                logger.error(f"❌ Ollama API hatası: {response.status_code}")
                return None
        
        except requests.Timeout:
            logger.error("❌ Ollama isteği zaman aşımına uğradı")
            return None
        
        except Exception as e:
            logger.error(f"❌ Ollama üretimi başarısız oldu: {str(e)}")
            return None
    
    def generate_json(self, prompt, system_prompt=None):
        """
        JSON yanıtı üret (format zorlaması ile)
        
        Argümanlar:
            prompt: Kullanıcı komutu
            system_prompt: Sistem komutu
            
        Döner:
            Ayrıştırılmış JSON sözlüğü veya başarısız olursa None
        """
        # Komuta JSON formatı talimatını ekle
        json_instruction = "\nSADECE geçerli JSON ile yanıt ver. Markdown formatı veya açıklama ekleme."
        full_prompt = prompt + json_instruction
        
        response_text = self.generate(full_prompt, system_prompt, temperature=0.1)
        
        if not response_text:
            return None
        
        # JSON ayrıştırmayı dene
        try:
            # Varsa markdown kod bloklarını kaldır
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON yanıtı ayrıştırılamadı: {str(e)}")
            logger.debug(f"Ham yanıt: {response_text[:200]}...")
            return None
