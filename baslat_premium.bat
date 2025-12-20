@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo 🚀 SNIPER TRADING BOT - PREMIUM SUITE BAŞLATILIYOR
echo ============================================================

:: 1. Backend API (FastAPI)
echo [1/3] Backend Veri Servisi Başlatılıyor (Port 8000)...
start "Sniper API" cmd /k "python api.py"

:: 2. Trading Engine (Python Main)
echo [2/3] Ticaret Motoru Başlatılıyor...
start "Sniper Engine" cmd /k "python main.py"

:: 3. Frontend (Next.js)
echo [3/3] Premium Dashboard Hazırlanıyor...
cd frontend_v2
start "Sniper Frontend" cmd /k "npm run dev"

echo.
echo ============================================================
echo ✅ TÜM SİSTEMLER ÇALIŞIYOR
echo 🌐 Premium Dashboard: http://localhost:3000
echo 📊 Eski Dashboard: http://localhost:8000/dashboard.html
echo ============================================================
echo.
pause
