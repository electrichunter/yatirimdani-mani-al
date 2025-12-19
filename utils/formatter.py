
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

    def save_result_for_web(self, symbol, signal_data):
        """Sonuçları web dashboard'u için JSON dosyasına kaydeder"""
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
            
        # Yeni sonucu ekle (son 200 kaydı tut - Tarihçe için artırıldı)
        self.all_results.insert(0, result)
        self.all_results = self.all_results[:200]
        
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(self.all_results, f, ensure_ascii=False, indent=2)

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

    def print_loop_status(self, wait_time):
        """Döngü durumunu yazdırır"""
        console.print(f"\n[dim]⏳ Sonraki tarama {wait_time:.0f} saniye sonra... (Durdurmak için Ctrl+C)[/dim]")
