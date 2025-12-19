
import http.server
import socketserver
import os
import logging

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Terminal kirliliğini önlemek için logları sessize alıyoruz
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # 404 hatalarını ve standart GET loglarını terminale basma
        return

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

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
