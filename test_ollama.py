
import requests
import json
import time

MODEL = "tinyllama:latest"
URL = "http://localhost:11434/api/generate"

print(f"Testing Ollama connexion with model: {MODEL}")

payload = {
    "model": MODEL,
    "prompt": "Why is the sky blue?",
    "stream": False
}

try:
    start = time.time()
    response = requests.post(URL, json=payload, timeout=60)
    end = time.time()
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(f"Time taken: {end - start:.2f}s")
        data = response.json()
        print(f"Response: {data.get('response', 'No response field')[:100]}...")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Connection Failed: {e}")
