
import os
import sys
import subprocess

# Backend klasörüne geç ve oradaki main.py'yi çalıştır
if __name__ == "__main__":
    backend_dir = os.path.join(os.getcwd(), "backend")
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        subprocess.run([sys.executable, "main.py"])
    else:
        print("❌ Backend dizini bulunamadı!")
