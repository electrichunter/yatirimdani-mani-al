"""
Ollama Client for Local LLM Inference
Optimized for RTX 3050 4GB VRAM
"""

import requests
import json
import config
from utils.logger import setup_logger

logger = setup_logger("OllamaClient")


class OllamaClient:
    """Client for Ollama API"""
    
    def __init__(self, model_name=None, host=None):
        """
        Args:
            model_name: Model to use (default from config)
            host: Ollama host URL (default localhost)
        """
        self.model_name = model_name or config.LLM_MODEL
        self.host = host or "http://localhost:11434"
        self.api_url = f"{self.host}/api/generate"
        
        # Check if Ollama is running
        self.check_connection()
    
    def check_connection(self):
        """Verify Ollama server is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                if self.model_name in model_names:
                    logger.info(f"✅ Ollama connected, model '{self.model_name}' available")
                else:
                    logger.warning(f"⚠️ Model '{self.model_name}' not found. Available: {model_names}")
                    logger.warning(f"   Run: ollama pull {self.model_name}")
            else:
                logger.error("❌ Ollama server not responding")
        
        except requests.RequestException as e:
            logger.error(f"❌ Cannot connect to Ollama at {self.host}")
            logger.error(f"   Make sure Ollama is running: ollama serve")
            logger.error(f"   Error: {str(e)}")
    
    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """
        Generate response from Ollama
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature (default from config)
            max_tokens: Max tokens to generate (default from config)
            
        Returns:
            Generated text response
        """
        if temperature is None:
            temperature = config.LLM_TEMPERATURE
        
        if max_tokens is None:
            max_tokens = config.LLM_MAX_TOKENS
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Force JSON output (Ollama 0.1.0+)
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.debug(f"🤖 Sending request to Ollama ({self.model_name})...")
            
            response = requests.post(self.api_url, json=payload, timeout=120)  # Increased from 60 to 120s
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                logger.debug(f"✅ LLM response received ({len(generated_text)} chars)")
                
                return generated_text
            else:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return None
        
        except requests.Timeout:
            logger.error("❌ Ollama request timed out")
            return None
        
        except Exception as e:
            logger.error(f"❌ Ollama generation failed: {str(e)}")
            return None
    
    def generate_json(self, prompt, system_prompt=None):
        """
        Generate JSON response (with format enforcement)
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            Parsed JSON dict or None if failed
        """
        # Add JSON format instruction to prompt
        json_instruction = "\nRespond ONLY with valid JSON. Do not include any markdown formatting or explanations."
        full_prompt = prompt + json_instruction
        
        response_text = self.generate(full_prompt, system_prompt, temperature=0.1)
        
        if not response_text:
            return None
        
        # Try to parse JSON
        try:
            # Remove markdown code blocks if present
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
            logger.error(f"❌ Failed to parse JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:200]}...")
            return None
