# 🔧 MT5 Bağlantı Sorun Giderme

## ✅ MT5 Çalışıyor Durumda

Terminal64.exe process'i tespit edildi (ID: 24040), yani MT5 açık.

---

## ❌ Sorun: Bot MT5'e bağlanamıyor

**Hata:**
```
⚠️ MT5 credentials not configured, using default account
Failed to get price for EURUSD
```

---

## 🔍 Olası Sebepler:

### 1. `.env` Dosyasında Şifre Eksik veya Yanlış

`.env` dosyasını kontrol edin:
```bash
notepad .env
```

**Doğru format:**
```
MT5_LOGIN=12345678
MT5_PASSWORD=gerçek_şifreniz_buraya
MT5_SERVER=Broker-Server-Adı
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

⚠️ "BURAYA_SİFRENİZİ_YAZIN" yazan yerde hala örnek metin varsa değiştirin!

---

### 2. MT5'te Giriş Yapılmamış

MT5 programını açın ve kontrol edin:
- Sağ üst köşede hesap numarası görünüyor mu?
- "Connected" yazıyor mu?

Eğer **bağlı değilse**:
1. File → Login to Trade Account
2. Login: `12345678`
3. Password: (broker şifreniz)
4. Server: `Broker-Server-Adı`
5. Login'e tıklayın

---

### 3. Python-MT5 API Erişimi

MT5'te Python API'nin aktif olması gerekir:
1. MT5'te Tools → Options → Expert Advisors
2. ✅ "Allow automated trading" işaretli olmalı
3. ✅ "Allow DLL imports" işaretli olmalı

---

## 🧪 Geçici Çözüm: Demo Mode

MT5 sorununu çözerken bot işlevselliğini test etmek için:

```powershell
python main.py
# D (Demo/Simüle veri) ← Bunu seçin
# T (Test modu)
```

Bu şekilde MT5 olmadan da çalışır ve sistemi test edebilirsiniz.

---

## 🐛 Detaylı Hata Tespiti

MT5 bağlantısını test edin:

```python
python -c "import MetaTrader5 as mt5; print('MT5 initialized:', mt5.initialize())"
```

**Beklenen çıktı:**
- `MT5 initialized: True` → Bağlantı OK
- `MT5 initialized: False` → Sorun var

---

## 📞 Broker Desteği

Eğer şifre doğru ama hala bağlanamıyorsanız:

**Norexa Finance** desteğine sorun:
- API trading izni aktif mi?
- Hesap kısıtlaması var mı?
- Python API kullanımı için özel ayar gerekiyor mu?

---

## ✅ Başarılı Bağlantı Göstergeleri:

Bot başladığında şunu göreceksiniz:
```
✅ Connected to MT5: NorexaFinance-Server
Account: 12345678
Balance: $XXXX.XX
```

Şu anda bunun yerine görüyorsunuz:
```
⚠️ MT5 credentials not configured
```

---

**Öneri:** Şimdilik **Demo Mode (D)** ile test edin, MT5 bağlantısını daha sonra hallederiz!
