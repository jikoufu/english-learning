from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


HOST = "127.0.0.1"
PORT = 60001
ROOT = Path(__file__).resolve().parent


class LearningHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        parsed = urlparse(path)
        clean_path = unquote(parsed.path)
        if clean_path in ("", "/"):
            clean_path = "/index.html"
        return str(ROOT / clean_path.lstrip("/"))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    server = ThreadingHTTPServer((HOST, PORT), LearningHandler)
    print(f"English learning server running at http://{HOST}:{PORT}/index.html")
    print(f"Root: {ROOT}")
    print("Keep this window open. Use server.ps1 stop to close the service.")
    server.serve_forever()


if __name__ == "__main__":
    main()
