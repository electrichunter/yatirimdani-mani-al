import subprocess
import threading
import os
import sys
import time
import webbrowser
import signal

def kill_port_processes(ports):
    """Belirtilen portlari kullanan Windows sureclerini temizler."""
    for port in ports:
        try:
            # Netstat ile PID bul
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode()
            for line in output.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if pid != "0":
                        subprocess.run(['taskkill', '/F', '/T', '/PID', pid], capture_output=True)
                        print(f"🧹 Port {port} temizlendi (PID: {pid})")
        except:
            pass

def run_api():
    print("📡 API Sunucusu başlatılıyor (Port: 8000)...")
    backend_dir = os.path.abspath("backend")
    # API'yi doğrudan uvicorn ile başlatarak daha hızlı yanıt alalım
    subprocess.run([sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"], cwd=backend_dir)

def run_engine():
    print("⚙️ Sniper Bot Motoru başlatılıyor (Komut Bekleme Modu)...")
    backend_dir = os.path.abspath("backend")
    subprocess.run([sys.executable, "main.py"], cwd=backend_dir)

def run_frontend(command):
    print(f"🖥️ Frontend başlatılıyor ({command})...")
    frontend_dir = os.path.abspath("frontend_v2")
    subprocess.run(command.split(), cwd=frontend_dir, shell=True)

if __name__ == "__main__":
    # Portlari temizle (8000: API, 3000: Frontend)
    print("🧹 Eski oturumlar temizleniyor...")
    kill_port_processes([8000, 3000, 3001])

    print("\n" + "="*50)
    print("      SNIPER TRADING BOT - MODERN STARTUP")
    print("="*50 + "\n")
    
    # Eskimiş config ve signal dosyalarını temizle ki temiz başlasın
    config_path = os.path.join("backend", "data", "bot_config.json")
    stop_signal = os.path.join("backend", "data", "system_stop.signal")
    
    for f in [config_path, stop_signal]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    print("Frontend Seçimi:")
    print("1) Gelistirme (npm run dev)")
    print("2) Uretim (npm run start)")
    choice = input("\nSeciminizi yapin (1/2): ").strip()
    fe_cmd = "npm run dev" if choice == '1' else "npm run start"

    # Thread'leri başlat
    api_t = threading.Thread(target=run_api, daemon=True)
    eng_t = threading.Thread(target=run_engine, daemon=True)
    fe_t = threading.Thread(target=run_frontend, args=(fe_cmd,), daemon=True)

    api_t.start()
    time.sleep(2) # API önce kalksın
    eng_t.start()
    fe_t.start()

    print("\n🌍 Kontrol Paneli Hazir: http://localhost:3000")
    webbrowser.open("http://localhost:3000")

    # Ana thread'i canlı tut ve STOP sinyalini izle
    try:
        while True:
            if os.path.exists(stop_signal):
                print("\n🛑 WEB ÜZERİNDEN KAPATMA SİNYALİ ALINDI. Sistem kapatiliyor...")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Sistem kapatiliyor...")
    
    # Temizlik yap ve çık
    if os.path.exists(stop_signal):
        try: os.remove(stop_signal)
        except: pass
    sys.exit(0)
