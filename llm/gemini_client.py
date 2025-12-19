"""
Google Gemini API Client (Updated for new google-genai SDK)
Cloud-based LLM inference with guaranteed JSON output
Fast, reliable, and free tier available
"""

import os
import json
import config
from google import genai
from google.genai.types import GenerateContentConfig
from utils.logger import setup_logger

logger = setup_logger("GeminiClient")


class GeminiClient:
    """Client for Google Gemini API (using new google-genai SDK)"""
    
    def __init__(self, model_name=None, api_key=None):
        """
        Args:
            model_name: Model to use (default: gemini-2.0-flash)
            api_key: Gemini API key (default from env)
        """
        # Use model from config or provided name
        self.model_name = (model_name or config.GEMINI_MODEL or "gemini-3-flash-preview")
        
        # GenAI SDK expects model names without 'models/' prefix
        if self.model_name.startswith("models/"):
            self.model_name = self.model_name.replace("models/", "")
            
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment variables")
            logger.error("   Add to .env: GEMINI_API_KEY=your_key_here")
            raise ValueError("Missing GEMINI_API_KEY")
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(f"✅ Gemini API initialized with model '{self.model_name}'")
    
    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """
        Generate response from Gemini
        """
        try:
            # Define strict schema for JSON - CRITICAL FIELDS FIRST
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "karar": {"type": "STRING", "description": "Decision: AL, SAT, or BEKLE"},
                    "guven": {"type": "INTEGER", "description": "Confidence 0-100"},
                    "giris_fiyati": {"type": "NUMBER"},
                    "zarar_kes": {"type": "NUMBER"},
                    "kar_al": {"type": "NUMBER"},
                    "risk_skoru": {"type": "INTEGER", "description": "Risk score 0-100"},
                    "risk_odul_orani": {"type": "NUMBER"},
                    "beklenen_sure": {"type": "STRING", "description": "Expected duration"},
                    "neden": {"type": "STRING", "description": "Detailed reasoning in Turkish"}
                },
                "required": ["karar", "guven", "giris_fiyati", "zarar_kes", "kar_al", "risk_skoru", "risk_odul_orani", "beklenen_sure", "neden"]
            }

            config_gen = GenerateContentConfig(
                temperature=temperature if temperature is not None else 0.1,
                max_output_tokens=max_tokens if max_tokens is not None else 2048,
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction=system_prompt if system_prompt else None
            )
            
            # Generate content with simple retry
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config_gen
                    )
                    
                    if response:
                        # DEBUG: Log metadata
                        if hasattr(response, 'candidates') and response.candidates:
                            reason = response.candidates[0].finish_reason
                            if reason != "STOP":
                                logger.warning(f"⚠️ Gemini Finish Reason: {reason}")
                        
                        if response.text:
                            return response.text
                    
                    logger.error("❌ Gemini returned empty response")
                    return None
                        
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries:
                        logger.warning(f"⚠️ Gemini Rate Limit (429). Retrying in 60s...")
                        import time
                        time.sleep(60)
                        continue
                    else:
                        raise e
        except Exception as e:
            logger.error(f"❌ Gemini Selection Error: {str(e)}")
            return None
    
    def generate_json(self, prompt, system_prompt=None):
        """
        Generate JSON response (already guaranteed by Gemini config)
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            Parsed JSON dict or None if failed
        """
        response_text = self.generate(prompt, system_prompt, temperature=0.1)
        
        if not response_text:
            return None
        
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:200]}...")
            return None
