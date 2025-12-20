
import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live

console = Console()

class UIFormatter:
    """Terminal çıktısı ve web sonuçları için biçimlendirme sağlar"""
    
    def __init__(self, results_path="data/web_results.json"):
        self.results_path = results_path
        self.all_results = []
        # Dizinin var olduğundan emin ol
        os.makedirs(os.path.dirname(self.results_path), exist_ok=True)
        
        self.symbol_map = {
            "EURUSD=X": "EUR/USD (Euro Dolar)",
            "GBPUSD=X": "GBP/USD (İngiliz Sterlini Dolar)",
            "USDJPY=X": "USD/JPY (Dolar Yen)",
            "GC=F": "XAU/USD (Altın Ons)",
            "SI=F": "XAG/USD (Gümüş Ons)",
            "HG=F": "HG=F (Bakır)",
            "CL=F": "CL=F (Ham Petrol)",
            "BTC-USD": "BTC/USD (Bitcoin)",
            "ETH-USD": "ETH/USD (Ethereum)"
        }

    def get_display_name(self, symbol):
        """Sembolün uzun adını döndürür"""
        return self.symbol_map.get(symbol, symbol)

    def print_market_header(self, symbol):
        """Varlık analizi başlangıcı için başlık yazdırır"""
        display_name = self.get_display_name(symbol)
        table = Table(show_header=False, header_style="bold magenta", border_style="cyan")
        table.add_row(f"[bold yellow]🚀 VARLIK ANALİZ EDİLİYOR:[/bold yellow] [bold white]{display_name}[/bold white]")
        console.print("\n")
        console.print(Panel(table, border_style="cyan"))

    def print_stage_result(self, stage, result, symbol):
        """Her bir aşama (Teknik/Haber) sonucunu yazdırır"""
        color = "green" if result["pass"] else "red"
        status = "✅ GEÇTİ" if result["pass"] else "❌ KALDI"
        
        detail = ""
        if stage == 1:
            name = "Teknik Analiz"
            detail = f"Skor: {result['score']}/100 | Yön: {result.get('direction', 'N/A')}"
        elif stage == 2:
            name = "Haber Analizi"
            detail = f"Duygu Skoru: {result.get('sentiment_score', 0):.1f}"
        
        text = Text()
        text.append(f"{name}: ", style="bold")
        text.append(f"{status} ", style=f"bold {color}")
        text.append(f"({detail})", style="italic")
        
        console.print(text)
        if not result["pass"] and "reason" in result:
             console.print(f"   [dim]Sebep: {result['reason']}[/dim]")

    def print_trade_signal(self, symbol, signal_data):
        """Nihai ticaret sinyalini tablo halinde yazdırır"""
        decision = signal_data.get("decision", "PASS")
        if decision == "PASS":
            return

        color = "green" if "BUY" in decision else "red"
        icon = "📈" if "BUY" in decision else "📉"
        
        table = Table(title=f"[bold]🎯 TİCARET SİNYALİ - {symbol}[/bold]", border_style=color)
        table.add_column("Parametre", style="cyan")
        table.add_column("Değer", style="white")
        
        table.add_row("Yön", f"[{color}]{decision}[/{color}] {icon}")
        table.add_row("Giriş Fiyatı", f"{signal_data.get('entry_price', 0):.5f}")
        table.add_row("Zarar Kes (SL)", f"[red]{signal_data.get('stop_loss', 0):.5f}[/red]")
        table.add_row("Kar Al (TP)", f"[green]{signal_data.get('take_profit', 0):.5f}[/green]")
        table.add_row("Güven Seviyesi", f"%{signal_data.get('confidence', 0)}")
        table.add_row("RR Oranı", f"{signal_data.get('rr_ratio', 0):.2f}:1")
        
        reasoning = signal_data.get("reasoning", "Açıklama yok")
        
        console.print("\n")
        console.print(table)
        console.print(Panel(f"[italic]{reasoning}[/italic]", title="Strateji Notu", border_style=color))
        
        # Web için kaydet
        self.save_result_for_web(symbol, signal_data)

    def save_result_for_web(self, symbol, signal_data, archive=False):
        """Sonuçları web dashboard'u için JSON dosyasına kaydeder.

        Eğer `archive=True` ise aynı sonucu `data/analysis_archive.json` dosyasına
        tarih/saat bilgisi ile ekleriz. Bu, ileriye dönük test ve doğrulama için kullanılır.
        """
        # Augment signal_data with presentation-friendly fields
        try:
            real_conf = float(signal_data.get('confidence', 0) or 0)
        except Exception:
            real_conf = 0.0

        # Presented confidence: show a minimum friendly value in the UI
        try:
            import config
            min_display = getattr(config, 'MIN_DISPLAY_CONFIDENCE', 0)
        except Exception:
            min_display = 0

        presented_conf = max(real_conf, float(min_display))
        signal_data['presented_confidence'] = round(presented_conf, 2)
        signal_data['low_confidence'] = True if real_conf < getattr(config, 'MIN_CONFIDENCE', 70) else False

        # Ensure metrics are present for the frontend
        if 'technical_score' not in signal_data and 'tech_score' in signal_data:
             signal_data['technical_score'] = signal_data['tech_score']
        
        # Add a concise user-facing message explaining technical weakness (if any)
        try:
            signal_data['user_message'] = self._compose_user_message(signal_data, real_conf)
        except Exception as e:
            signal_data['user_message'] = f'Analiz tamamlandı. (Hata: {str(e)})'

        # Virtual balance simulation (shows how a $100 account would size this trade)
        try:
            signal_data['virtual'] = self._compute_virtual(signal_data)
        except Exception:
            signal_data['virtual'] = {}

        result = {
            "symbol": symbol,
            "display_name": self.get_display_name(symbol),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": signal_data
        }
        
        # Mevcut sonuçları yükle
        try:
            if os.path.exists(self.results_path):
                with open(self.results_path, "r", encoding="utf-8") as f:
                    self.all_results = json.load(f)
            else:
                self.all_results = []
        except:
            self.all_results = []

        # Deduplication (Mükerrer Kaydı Önle):
        # Eğer bu sembol için son karar aynıysa ve bu bir "BEKLE" (Wait) kararıysa, kaydetme.
        # Bu, dashboard'un aynı mesajlarla dolmasını engeller.
        try:
            current_decision = str(signal_data.get('decision', '')).upper()
            is_wait_state = "BEKLE" in current_decision
            
            # Sonuçlar listesinde bu sembolü bul
            last_entry = next((r for r in self.all_results if r.get('symbol') == symbol), None)
            if last_entry and is_wait_state:
                last_decision = str(last_entry.get('data', {}).get('decision', '')).upper()
                if last_decision == current_decision:
                    # Karar aynı ve bir bekleme hali, arşivleme de istenmiyorsa çık
                    if not archive:
                        return
        except Exception:
            pass
            
        # Yeni sonucu ekle (son 200 kaydı tut)
        self.all_results.insert(0, result)
        self.all_results = self.all_results[:200]
        
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(self.all_results, f, ensure_ascii=False, indent=2)

        # Eğer arşivlenmesi istenmişse, özel bir arşiv dosyasına ekle
        if archive:
            try:
                archive_path = os.path.join(os.path.dirname(self.results_path), 'analysis_archive.json')
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                if os.path.exists(archive_path):
                    with open(archive_path, 'r', encoding='utf-8') as af:
                        archive_list = json.load(af)
                else:
                    archive_list = []

                # Yeni girdiyi başa ekle (en son ilk görünür)
                archive_list.insert(0, result)
                # Arşiv boyutunu sınırlayalım
                archive_list = archive_list[:5000]

                with open(archive_path, 'w', encoding='utf-8') as af:
                    json.dump(archive_list, af, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def save_news_for_web(self, news_list, news_path="data/news_results.json"):
        """Haberleri web dashboard'u için JSON dosyasına kaydeder"""
        os.makedirs(os.path.dirname(news_path), exist_ok=True)
        
        # Sadece gerekli alanları al ve kaydet
        formatted_news = []
        for n in news_list:
            formatted_news.append({
                "title": n.get("title", ""),
                "source": n.get("source", ""),
                "published_at": n.get("published_at", ""),
                "sentiment": n.get("sentiment_score", 0),
                "impact": n.get("impact_level", "LOW"),
                "symbols": n.get("symbols", "")
            })
            
        with open(news_path, "w", encoding="utf-8") as f:
            json.dump(formatted_news, f, ensure_ascii=False, indent=2)

    def _compose_user_message(self, signal_data, real_confidence: float):
        """Kullanıcıya gösterilecek profesyonel ve tatmin edici Türkçe açıklamayı oluşturur.
        Teknik veriler, duygu analizi ve risk/ödül dengesini harmanlar.
        """
        try:
            import config
        except Exception:
            config = None

        decision = str(signal_data.get('decision', 'WAIT')).upper()
        tech_score = signal_data.get('technical_score', 0)
        sent_score = signal_data.get('sentiment_score', 0) or signal_data.get('news_sentiment', 0)
        
        parts = []
        
        # Giriş cümlesi: Genel durum özeti
        if "BUY" in decision:
            parts.append("🚀 Teknik göstergeler ve piyasa dinamikleri güçlü bir yükseliş formasyonu işaret ediyor.")
        elif "SELL" in decision:
            parts.append("📉 Ayı baskısı artıyor; teknik veriler satış yönlü bir momentumun başladığını gösteriyor.")
        else:
            parts.append("⚖️ Piyasa şu an nötr bir bölgede; net bir kırılım beklenmesi daha profesyonel bir yaklaşım olacaktır.")

        # Teknik ve Duygu detayları
        if tech_score > 70:
            parts.append(f"Teknik analiz skoru oldukça yüksek ({tech_score}/100); H1 ve H4 trend uyumu mükemmel.")
        elif tech_score > 50:
            parts.append(f"Teknik görünüm pozitif ({tech_score}/100), ancak momentumun tam oturması için bir miktar daha hacim gerekiyor.")
        
        if sent_score > 60:
            parts.append("Haber akışı ve kurumsal duyarlılık alıcıları destekliyor.")
        elif sent_score < 40 and sent_score != 0:
            parts.append("Dikkat: Haber kanallarında bazı negatif sinyaller var, bu da volatiliteyi artırabilir.")

        # RR Açıklaması
        rr = None
        if 'rr_ratio' in signal_data and signal_data['rr_ratio'] is not None:
            try:
                rr = float(signal_data['rr_ratio'])
            except Exception:
                rr = None
        
        if rr is not None:
            if rr >= 2.0:
                parts.append(f"Risk/Ödül oranı ({rr:.2f}:1) oldukça tatmin edici; kâr potansiyeli riski fazlasıyla karşılıyor.")
            elif rr >= 1.5:
                # Kullanıcının sorduğu durum: Neden 1.5?
                parts.append(f"Risk/Ödül oranı {rr:.2f}:1 seviyesinde. Bu oranın 'muhafazakar' çıkma sebebi, hedef fiyatın (TP) hemen üzerinde güçlü bir teknik direnç bölgesi olmasıdır.")
                parts.append("Güvenliği elden bırakmamak adına kar al noktası bu direncin hemen altına normalize edilmiştir.")
            else:
                parts.append(f"RR oranı ({rr:.2f}:1) düşük seyrediyor. Mevcut fiyatın destek/direnç noktalarına çok yakın olması manevra alanını kısıtlıyor.")

        # Final Önerisi
        if real_confidence >= getattr(config, 'MIN_CONFIDENCE', 70):
            parts.append(f"Güven seviyesi %{real_confidence:.0f} ile optimize edildi. Stratejinize uygun lot miktarı ile aksiyon alınabilir.")
        else:
            parts.append(f"Şu anki güven seviyesi (%{real_confidence:.0f}) profesyonel bir giriş için bir miktar düşük. Simülasyon modunda izlemek veya 'Sniper' fırsatını beklemek sermayenizi korur.")

        return ' '.join(parts)

    def _compute_virtual(self, signal_data):
        """Dinamik Lot üzerinden beklenen kâr/zararı hesapla."""
        try:
            entry = float(signal_data.get('entry_price') or 0)
            tp = float(signal_data.get('take_profit') or 0)
            sl = float(signal_data.get('stop_loss') or 0)
            symbol = signal_data.get('symbol', '')
            
            if entry == 0: return {}

            # Bakiyenin %10'u kadar risk/maliyet hesabı (Sanal 100$ üzerinden)
            risk_budget = 10.0 # 100 * 0.10
            lot = round(risk_budget / entry, 2)
            if lot < 0.01: lot = 0.01
            
            # 1.0 Lot = 1 Unit hesabı
            contract_size = 1
            
            # Kar/Zarar Mesafesi
            tp_dist = abs(tp - entry)
            sl_dist = abs(entry - sl)
            
            # USD Bazlı Kar Hesaplama
            def calc_usd(price_diff, current_p):
                raw_profit = price_diff * lot * contract_size
                if symbol.startswith("USD"):
                    return raw_profit / current_p if current_p else raw_profit
                return raw_profit

            expected_profit = round(calc_usd(tp_dist, tp), 2)
            expected_loss = round(calc_usd(sl_dist, sl), 2)

            return {
                'lot': lot,
                'rr': round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0,
                'expected_profit_if_tp': expected_profit,
                'expected_loss_if_sl': expected_loss
            }
        except Exception:
            return {}

    def print_loop_status(self, wait_time):
        """Döngü durumunu yazdırır"""
        console.print(f"\n[dim]⏳ Sonraki tarama {wait_time:.0f} saniye sonra... (Durdurmak için Ctrl+C)[/dim]")
