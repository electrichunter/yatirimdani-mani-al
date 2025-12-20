import requests
import json

def test_ollama():
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": "Say 'Bağlantı Başarılı' and nothing else.",
        "stream": False
    }
    
    try:
        print(f"🔄 Ollama bağlantısı test ediliyor (model: deepseek-r1:1.5b)...")
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ BAĞLANTI BAŞARILI!")
            print(f"🤖 LLM Yanıtı: {result.get('response')}")
        else:
            print(f"❌ HATA: Durum kodu {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ BAĞLANTI HATASI: {str(e)}")

if __name__ == "__main__":
    test_ollama()
