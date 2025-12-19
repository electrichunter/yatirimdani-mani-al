"""
Risk Yönetimi Modülü
Pozisyon büyüklüğü, SL/TP ve Risk/Ödül oranlarını hesaplar
"""

import config
from utils.logger import setup_logger

logger = setup_logger("RiskManager")


class RiskManager:
    """Pozisyon büyüklüğü ve risk hesaplamalarını yönetir"""
    
    def __init__(self, broker):
        """
        Argümanlar:
            broker: Broker nesnesi (örneğin YFinanceBroker)
        """
        self.broker = broker
    
    def calculate_position_size(self, symbol, entry_price, stop_loss, risk_percent=None, balance_override=None):
        """
        Risk yüzdesine göre pozisyon büyüklüğünü hesaplar
        
        Formül:
        Pozisyon Büyüklüğü = (Hesap Bakiyesi * Risk%) / (SL Mesafesi (Pip) * Pip Değeri)
        
        Argümanlar:
            symbol: Ticari varlık
            entry_price: Giriş fiyatı
            stop_loss: Zarar kes fiyatı
            risk_percent: Risk yüzdesi (varsayılanı config'den alır)
            
        Döner:
            Lot cinsinden pozisyon büyüklüğü
        """
        if risk_percent is None:
            risk_percent = config.RISK_PERCENT
        
        # Hesap bakiyesini al (öncelik: balance_override > config.VIRTUAL_BALANCE (dry) > broker.get_balance())
        if balance_override is not None:
            balance = float(balance_override)
        else:
            if getattr(config, 'VIRTUAL_BALANCE', None) is not None and getattr(config, 'DRY_RUN', False):
                balance = float(getattr(config, 'VIRTUAL_BALANCE'))
            else:
                balance = self.broker.get_balance()
        if balance == 0:
            logger.error("Hesap bakiyesi 0, pozisyon büyüklüğü hesaplanamıyor")
            return 0.01  # Minimum lot büyüklüğü
        
        # Risk miktarını hesapla
        risk_amount = balance * (risk_percent / 100)
        
        # SL mesafesini hesapla
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            logger.error("Zarar kes mesafesi 0")
            return 0.01
        
        # Pip değerini sembol tipine göre al
        if "JPY" in symbol:
            pip_value = 0.01
        elif "GC=F" in symbol or "XAU" in symbol:
            pip_value = 0.1  # Altın: 1 pip = 0.1 birim
        elif "SI=F" in symbol or "XAG" in symbol:
            pip_value = 0.01 # Gümüş: 1 pip = 0.01 birim
        else:
            pip_value = 0.0001  # Standart Forex
        
        sl_distance_pips = sl_distance / pip_value
        
        # Standart hesap için mini lot (0.1) başına pip başına 1$ varsayalım
        # Bu basitleştirilmiştir - gerçek değer hesap birimine bağlıdır
        value_per_pip = 1.0  # 0.1 lot için pip başına USD
        
        # Pozisyon büyüklüğünü hesapla
        position_size = risk_amount / (sl_distance_pips * value_per_pip) * 0.1
        
        # 2 ondalık basamağa yuvarla
        position_size = round(position_size, 2)
        
        # Minimum lot büyüklüğünü sağla
        if position_size < 0.01:
            position_size = 0.01
        
        # Maksimum lot büyüklüğünü sınırla (opsiyonel güvenlik)
        max_lot_size = 10.0
        if position_size > max_lot_size:
            logger.warning(f"Pozisyon büyüklüğü {position_size} maksimumu aşıyor, {max_lot_size} ile sınırlandırıldı")
            position_size = max_lot_size
        
        logger.info(f"💰 Pozisyon büyüklüğü hesaplandı: {position_size} lot (Risk: ${risk_amount:.2f})")
        
        return position_size
    
    def calculate_risk_reward_ratio(self, entry_price, stop_loss, take_profit):
        """
        Risk/Ödül oranını hesaplar
        
        Argümanlar:
            entry_price: Giriş fiyatı
            stop_loss: Zarar kes fiyatı
            take_profit: Kar al fiyatı
            
        Döner:
            Risk/Ödül oranı (örneğin 3.0, 3:1 ödül:risk anlamına gelir)
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0
        
        rr_ratio = reward / risk
        
        # Kullanıcı talebi: Max RR 10 olsun
        if rr_ratio > 10.0:
            logger.warning(f"⚠️ Uçuk RR tespit edildi ({rr_ratio:.2f}). 10.0 ile sınırlandırılıyor.")
            return 10.0
            
        return round(rr_ratio, 2)
    
    def validate_trade(self, entry_price, stop_loss, take_profit, symbol=None, decision="PASS"):
        """
        İşlemin minimum risk/ödül gereksinimlerini karşılayıp karşılamadığını doğrular
        Eksik (0.0) değerler için otomatik düzeltme içerir
        """
        entry_price = float(entry_price)
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)

        # HATA TELAFİSİ: Fiyatlar 0 ise (AI kesintisi veya hata nedeniyle)
        if decision != "PASS" and entry_price > 0:
            if stop_loss == 0:
                # Varsayılan %1 SL
                stop_loss = entry_price * (0.99 if decision == "BUY" else 1.01)
                logger.warning(f"⚠️ Kritik SL eksik! Otomatik %1 SL atandı: {stop_loss:.5f}")
            
            if take_profit == 0:
                # Varsayılan %1.5 TP (1.5 RR oranını karşılamak için)
                take_profit = entry_price * (1.015 if decision == "BUY" else 0.985)
                logger.warning(f"⚠️ Kritik TP eksik! Otomatik %1.5 TP atandı: {take_profit:.5f}")
        
        elif decision != "PASS" and entry_price <= 0:
            logger.error("❌ Geçersiz Giriş Fiyatı (0.0). İşlem iptal edildi.")
            return {
                "valid": False,
                "reason": "Giriş fiyatı 0.0",
                "rr_ratio": 0,
                "sl": stop_loss,
                "tp": take_profit
            }

        rr_ratio = self.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
        
        # SL ve TP'nin giriş fiyatının doğru tarafında olup olmadığını kontrol et
        if decision == "BUY":
            if stop_loss >= entry_price:
                logger.warning(f"⚠️ BUY için SL fiyattan büyük ({stop_loss} >= {entry_price}). Düzeltiliyor...")
                stop_loss = entry_price * 0.99
            if take_profit <= entry_price:
                logger.warning(f"⚠️ BUY için TP fiyattan küçük ({take_profit} <= {entry_price}). Düzeltiliyor...")
                take_profit = entry_price * 1.015
        elif decision == "SELL":
            if stop_loss <= entry_price:
                logger.warning(f"⚠️ SELL için SL fiyattan küçük ({stop_loss} <= {entry_price}). Düzeltiliyor...")
                stop_loss = entry_price * 1.01
            if take_profit >= entry_price:
                logger.warning(f"⚠️ SELL için TP fiyattan büyük ({take_profit} >= {entry_price}). Düzeltiliyor...")
                take_profit = entry_price * 0.985

        # --- YOĞUN BAKIM (Sanity Check) ---
        # Fiyatların uçuk (hallucination) olup olmadığını kontrol et
        # Forex için %5, Kripto için %30 değişim sınırı
        is_crypto = "-USD" in symbol or "USDT" in symbol # (Basitleştirilmiş kontrol)
        max_change = 0.30 if is_crypto else 0.05
        
        # SL Kontrolü
        sl_change = abs(entry_price - stop_loss) / entry_price
        if sl_change > max_change:
            logger.warning(f"⚠️ UÇUK SL TESPİT EDİLDİ (%{sl_change*100:.1f}). Makul seviyeye çekiliyor.")
            stop_loss = entry_price * (0.98 if decision == "BUY" else 1.02)

        # TP Kontrolü
        tp_change = abs(entry_price - take_profit) / entry_price
        if tp_change > max_change:
            logger.warning(f"⚠️ UÇUK TP TESPİT EDİLDİ (%{tp_change*100:.1f}). Makul seviyeye çekiliyor.")
            # Eğer RR biliniyorsa ona göre, yoksa %3'e sabitle
            stop_dist = abs(entry_price - stop_loss)
            take_profit = entry_price + (stop_dist * 2.0 if decision == "BUY" else -stop_dist * 2.0)

        # Potansiyel düzeltmeden sonra RR'yi tekrar hesapla
        rr_ratio = self.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)

        if rr_ratio < config.MIN_RISK_REWARD_RATIO:
            return {
                "valid": False,
                "reason": f"R:R {rr_ratio} minimum {config.MIN_RISK_REWARD_RATIO} altında",
                "rr_ratio": rr_ratio,
                "sl": stop_loss,
                "tp": take_profit
            }
        
        return {
            "valid": True,
            "reason": "İşlem parametreleri doğrulandı (Sanity Check Geçildi)",
            "rr_ratio": rr_ratio,
            "sl": stop_loss,
            "tp": take_profit
        }
    
    def check_position_limits(self):
        """
        Limitlere göre yeni pozisyon açılıp açılamayacağını kontrol eder
        
        Döner:
            İzin durumunu içeren sözlük
        """
        open_positions = self.broker.get_open_positions()
        
        if len(open_positions) >= config.MAX_OPEN_POSITIONS:
            return {
                "allowed": False,
                "reason": f"Maksimum pozisyon sayısı ({config.MAX_OPEN_POSITIONS}) zaten dolmuş"
            }
        
        return {
            "allowed": True,
            "current_positions": len(open_positions)
        }
