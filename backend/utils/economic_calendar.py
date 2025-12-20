"""
Ekonomik Takvim Entegrasyonu
Gelecek önemli ekonomik olayları alır ve işlem kararlarında kullanır
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("EconomicCalendar")


class EconomicCalendar:
    """
    Ekonomik takvim verilerini yönetir
    Gelecek önemli olayları izler ve işlem kararlarını etkiler
    """
    
    def __init__(self):
        self.events_cache = []
        self.last_update = None
        self.cache_duration = timedelta(hours=6)  # 6 saatte bir güncelle
    
    def get_upcoming_events(self, 
                           symbol: str, 
                           days_ahead: int = 7,
                           min_impact: str = "MEDIUM") -> List[Dict]:
        """
        Belirli bir sembol için gelecek ekonomik olayları al
        """
        if self._should_update_cache():
            self._update_events_cache()
        
        # ALL veya None durumunda tüm ülkeleri getir
        if symbol is None or symbol.upper() == "ALL":
            countries = ["USD", "EUR", "GBP", "JPY", "TRY", "CRYPTO"]
        else:
            countries = self._extract_countries_from_symbol(symbol)
            
        if not countries:
            return []
        
        # İlgili olayları filtrele
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        # Etki seviyeleri: "HIGH" seçilse bile "MEDIUM" da gelsin (kullanıcı isteği)
        # Eğer min_impact LOW ise hepsi gelsin.
        if min_impact == "LOW":
            impact_levels = ["HIGH", "MEDIUM", "LOW"]
        else:
            impact_levels = ["HIGH", "MEDIUM"]
        
        all_relevant_events = []
        seen_titles = set()
        
        for country in countries:
            country_events = [
                event for event in self.events_cache
                if event.get("country") == country
                and event.get("impact") in impact_levels
                and self._parse_event_date(event.get("date")) <= cutoff_date
            ]
            for event in country_events:
                # Başlığa ve tarihe göre tekilleştir
                unique_key = f"{event.get('title')}_{event.get('date')}"
                if unique_key not in seen_titles:
                    all_relevant_events.append(event)
                    seen_titles.add(unique_key)
        
        # Tarihe göre sırala (en yakın önce)
        all_relevant_events.sort(key=lambda x: self._parse_event_date(x.get("date")))
        
        return all_relevant_events[:10]  # Maksimum 10 önemli haber
    
    def _should_update_cache(self) -> bool:
        """Cache'in güncellenip güncellenmeyeceğini kontrol et"""
        if not self.last_update:
            return True
        
        time_since_update = datetime.now() - self.last_update
        return time_since_update > self.cache_duration
    
    def _update_events_cache(self):
        """
        Ekonomik takvim verilerini güncelle
        Not: Gerçek üretimde bir API'den çekilir (örn: Forex Factory, Investing.com)
        Şu an için örnek veri kullanıyoruz
        """
        logger.info("📅 Updating economic calendar cache...")
        
        # Şimdilik statik örnek veriler (Gerçek uygulamada API çağrısı yapılır)
        self.events_cache = self._get_sample_events()
        self.last_update = datetime.now()
        
        logger.info(f"✅ Loaded {len(self.events_cache)} upcoming economic events")
    
    def _get_sample_events(self) -> List[Dict]:
        """
        Örnek ekonomik olaylar (Test için)
        Gerçek uygulamada burası bir API'den veri çeker
        """
        base_date = datetime.now()
        
        events = [
            # US Events
            {
                "date": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "title": "ABD İşsizlik Başvuruları",
                "country": "USD",
                "impact": "MEDIUM",
                "previous": "210K",
                "forecast": "215K",
                "category": "Employment"
            },
            {
                "date": (base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                "title": "ABD Tarım Dışı İstihdam (NFP)",
                "country": "USD",
                "impact": "HIGH",
                "previous": "200K",
                "forecast": "180K",
                "category": "Employment"
            },
            {
                "date": (base_date + timedelta(days=5)).strftime("%Y-%m-%d"),
                "title": "Fed Faiz Kararı (FOMC)",
                "country": "USD",
                "impact": "HIGH",
                "previous": "5.50%",
                "forecast": "5.50%",
                "category": "Central Bank"
            },
            
            # EUR Events
            {
                "date": (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "ECB Başkanı Lagarde Konuşması",
                "country": "EUR",
                "impact": "HIGH",
                "previous": "-",
                "forecast": "-",
                "category": "Central Bank"
            },
            {
                "date": (base_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                "title": "Eurozone TÜFE",
                "country": "EUR",
                "impact": "HIGH",
                "previous": "2.4%",
                "forecast": "2.3%",
                "category": "Inflation"
            },
            
            # GBP Events
            {
                "date": (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "title": "İngiltere İşsizlik Oranı",
                "country": "GBP",
                "impact": "MEDIUM",
                "previous": "4.2%",
                "forecast": "4.3%",
                "category": "Employment"
            },
            {
                "date": (base_date + timedelta(days=6)).strftime("%Y-%m-%d"),
                "title": "BoE Faiz Kararı",
                "country": "GBP",
                "impact": "HIGH",
                "previous": "5.25%",
                "forecast": "5.25%",
                "category": "Central Bank"
            },
            
            # JPY Events
            {
                "date": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "title": "Japonya TÜFE",
                "country": "JPY",
                "impact": "HIGH",
                "previous": "3.2%",
                "forecast": "3.0%",
                "category": "Inflation"
            },
            
            # Crypto-related (US focused)
            {
                "date": (base_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                "title": "ABD Kripto Düzenleme Açıklaması (SEC)",
                "country": "CRYPTO",
                "impact": "HIGH",
                "previous": "-",
                "forecast": "-",
                "category": "Regulatory"
            },
        ]
        
        return events
    
    def _extract_countries_from_symbol(self, symbol: str) -> List[str]:
        """
        Sembolden ilgili tüm ülkeleri çıkar
        """
        symbol = symbol.upper()
        countries = []
        
        # Forex pairs
        if "=X" in symbol:
            pair = symbol.replace("=X", "")
            if len(pair) >= 6:
                countries.append(pair[:3])
                countries.append(pair[3:6])
        
        # Commodity codes (Gold, Silver)
        if any(x in symbol for x in ["GC=F", "XAU", "GOLD"]):
            countries.append("USD")
            # Altın için bazen özel haberler olabilir
        elif any(x in symbol for x in ["SI=F", "XAG", "SILVER"]):
            countries.append("USD")
            
        # Default USD for most things if empty
        if not countries and any(x in symbol for x in ["-USD", "^GSPC", "^DJI"]):
            countries.append("USD")
            
        # Remove duplicates and filter common currencies
        valid_countries = ["USD", "EUR", "GBP", "JPY", "TRY", "CRYPTO"]
        return list(set([c for c in countries if c in valid_countries]))
    
    def _parse_event_date(self, date_str: str) -> datetime:
        """Parse event date string to datetime object"""
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # Fallback: Uzak bir tarih
        return datetime.now() + timedelta(days=30)
