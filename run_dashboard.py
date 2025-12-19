
import http.server
import socketserver
import os
import logging
import json
import sqlite3
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
try:
    from core.broker_yfinance import YFinanceBroker
except Exception:
    YFinanceBroker = None
import config

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Terminal kirliliğini önlemek için logları sessize alıyoruz
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/archive'):
            # return the analysis archive
            archive_path = os.path.join(DIRECTORY, 'data', 'analysis_archive.json')
            if os.path.exists(archive_path):
                try:
                    with open(archive_path, 'r', encoding='utf-8') as f:
                        arr = json.load(f)
                except Exception:
                    arr = []
            else:
                arr = []
            return self._send_json(200, arr)

        if parsed.path.startswith('/api/stats'):
            # compute simple stats from learning DB
            db_path = os.path.join(DIRECTORY, 'database', 'learning.db')
            stats = {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'pending': 0,
                'success_rate': 0.0,
                'virtual_balance': getattr(config, 'VIRTUAL_BALANCE', 100.0)
            }
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM trade_history")
                    stats['total_trades'] = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM trade_history WHERE outcome = 'WIN'")
                    stats['wins'] = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM trade_history WHERE outcome = 'LOSS'")
                    stats['losses'] = cur.fetchone()[0] or 0
                    cur.execute("SELECT COUNT(*) FROM trade_history WHERE outcome = 'PENDING'")
                    stats['pending'] = cur.fetchone()[0] or 0
                    if stats['total_trades'] > 0:
                        stats['success_rate'] = round(100.0 * stats['wins'] / stats['total_trades'], 2)
                    conn.close()
                except Exception:
                    pass
            return self._send_json(200, stats)

        if parsed.path.startswith('/api/archive/meta'):
            meta_path = os.path.join(DIRECTORY, 'data', 'archive_meta.json')
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except Exception:
                    meta = {}
            else:
                meta = {}
            return self._send_json(200, meta)

        if parsed.path.startswith('/api/monitoring') and parsed.path == '/api/monitoring':
            # return monitoring state
            state_path = os.path.join(DIRECTORY, 'data', 'monitoring_state.json')
            if os.path.exists(state_path):
                try:
                    with open(state_path, 'r', encoding='utf-8') as f:
                        st = json.load(f)
                except Exception:
                    st = {'paused': False}
            else:
                st = {'paused': False}
            return self._send_json(200, st)

        if parsed.path.startswith('/api/open_positions'):
            # Return list of pending trades with current price and P/L
            db_path = os.path.join(DIRECTORY, 'database', 'learning.db')
            results = []
            if not os.path.exists(db_path):
                return self._send_json(200, results)

            # lazy broker init
            broker = None
            if YFinanceBroker is not None:
                try:
                    broker = YFinanceBroker()
                except Exception:
                    broker = None

            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM trade_history WHERE outcome = 'PENDING'")
                rows = cur.fetchall()
                for r in rows:
                    rec = dict(r)
                    symbol = rec.get('symbol')
                    entry = rec.get('entry_price')
                    # stored position_size may be NULL/0 for older records
                    pos_size = rec.get('position_size')
                    try:
                        pos_size = float(pos_size) if pos_size is not None else 0.0
                    except Exception:
                        pos_size = 0.0
                    direction = rec.get('direction')

                    current = None
                    if broker is not None and symbol:
                        try:
                            current = broker.get_current_price(symbol)
                        except Exception:
                            current = None

                    # Use a sensible minimum lot for display if DB doesn't have a size
                    display_lot = pos_size if (pos_size and pos_size > 0) else getattr(config, 'MIN_DISPLAY_LOT', 0.01)

                    profit_pips = None
                    profit_amount = None
                    notional_usd = None

                    # Only compute profit/pips when both entry and current are valid numbers
                    try:
                        if entry is not None and current is not None and float(entry) > 0:
                            entry_f = float(entry)
                            current_f = float(current)
                            profit = (current_f - entry_f) if (str(direction).upper().startswith('BUY')) else (entry_f - current_f)
                            pip_mul = 100 if 'JPY' in (symbol or '') else 10000
                            profit_pips = round(abs(profit) * pip_mul, 2)
                            # approximate notional for forex: lot * 100000 * price
                            notional_usd = round(display_lot * 100000 * current_f, 2)
                            profit_amount = round(profit * display_lot * 100000, 2)
                        else:
                            # No valid entry -> leave values None so UI shows placeholders
                            profit_pips = None
                            profit_amount = None
                            notional_usd = round(display_lot * (float(current) if current else 0), 2) if display_lot and current else None
                    except Exception:
                        profit_pips = None
                        profit_amount = None
                        notional_usd = None

                    results.append({
                        'id': rec.get('id'),
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': entry,
                        'current_price': current,
                        'position_size': display_lot,
                        'profit_pips': profit_pips,
                        'profit_amount': profit_amount,
                        'notional_usd': notional_usd,
                        'timestamp': rec.get('timestamp')
                    })
                conn.close()
            except Exception:
                pass

            return self._send_json(200, results)

        # fallback to normal static file serving
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else ''

        if parsed.path == '/api/archive/delete':
            # delete archive file, clear web results, and clear trade history; record deletion meta
            archive_path = os.path.join(DIRECTORY, 'data', 'analysis_archive.json')
            meta_path = os.path.join(DIRECTORY, 'data', 'archive_meta.json')
            web_results_path = os.path.join(DIRECTORY, 'data', 'web_results.json')
            db_path = os.path.join(DIRECTORY, 'database', 'learning.db')
            try:
                # count archived items if present and remove archive file
                archive_count = 0
                if os.path.exists(archive_path):
                    try:
                        with open(archive_path, 'r', encoding='utf-8') as f:
                            arr = json.load(f)
                            archive_count = len(arr)
                    except Exception:
                        archive_count = 0
                    try:
                        os.remove(archive_path)
                    except Exception:
                        pass

                # reset web results
                try:
                    with open(web_results_path, 'w', encoding='utf-8') as wf:
                        json.dump([], wf, ensure_ascii=False, indent=2)
                except Exception:
                    pass

                # clear trade_history in learning DB and count removed rows
                db_deleted = 0
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cur = conn.cursor()
                        cur.execute("SELECT COUNT(*) FROM trade_history")
                        before = cur.fetchone()[0] or 0
                        cur.execute("DELETE FROM trade_history")
                        conn.commit()
                        db_deleted = before
                        conn.close()
                    except Exception:
                        db_deleted = 0

                meta = {
                    'last_deletion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'archive_deleted': archive_count,
                    'db_deleted': db_deleted
                }
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

                return self._send_json(200, {'ok': True, 'meta': meta})
            except Exception as e:
                return self._send_json(500, {'ok': False, 'error': str(e)})

        if parsed.path == '/api/archive/schedule':
            # Schedule analyses: simple heuristic using confidence
            try:
                payload = json.loads(body) if body else {}
            except Exception:
                payload = {}
            archive_path = os.path.join(DIRECTORY, 'data', 'analysis_archive.json')
            if not os.path.exists(archive_path):
                return self._send_json(404, {'error': 'archive not found'})
            try:
                with open(archive_path, 'r', encoding='utf-8') as f:
                    arr = json.load(f)
            except Exception:
                arr = []

            updated = []
            now = datetime.now()
            for item in arr:
                data = item.get('data', {})
                # schedule only if not already scheduled
                if data.get('scheduled_at'):
                    continue
                conf = data.get('confidence', 50) or 50
                # heuristic: lower confidence -> later scheduling (minutes)
                minutes = int((100 - int(conf)) / 10) * 5  # step of 5 minutes
                scheduled = now + timedelta(minutes=minutes)
                data['scheduled_at'] = scheduled.strftime('%Y-%m-%d %H:%M:%S')
                item['data'] = data
                updated.append(item)

            # save updated archive
            try:
                with open(archive_path, 'w', encoding='utf-8') as f:
                    json.dump(arr, f, ensure_ascii=False, indent=2)
            except Exception as e:
                return self._send_json(500, {'error': str(e)})

            return self._send_json(200, {'updated': len(updated)})

        if parsed.path == '/api/monitoring/pause' and self.command == 'POST':
            state_path = os.path.join(DIRECTORY, 'data', 'monitoring_state.json')
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            try:
                st = {'paused': True, 'paused_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(st, f, ensure_ascii=False)
                return self._send_json(200, {'ok': True, 'state': st})
            except Exception as e:
                return self._send_json(500, {'ok': False, 'error': str(e)})

        if parsed.path == '/api/monitoring/resume' and self.command == 'POST':
            state_path = os.path.join(DIRECTORY, 'data', 'monitoring_state.json')
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            try:
                st = {'paused': False, 'resumed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(st, f, ensure_ascii=False)
                return self._send_json(200, {'ok': True, 'state': st})
            except Exception as e:
                return self._send_json(500, {'ok': False, 'error': str(e)})

        return self._send_json(404, {'error': 'unknown endpoint'})

if __name__ == "__main__":
    # socketserver'ın varsayılan loglamasını engellemek için
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        print(f"\n🚀 Dashboard arka planda çalışıyor: http://localhost:{PORT}/dashboard.html")
        print("Bot kapatıldığında dashboard da otomatik kapanacaktır.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()
