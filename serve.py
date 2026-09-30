# Serves the site for the installation monitor:   python serve.py
# (Use this instead of "python -m http.server": on some Windows PCs that serves .js files
#  with the wrong type and the page stays blank.)
import http.server, mimetypes, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
for ext, kind in {'.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
                  '.bin': 'application/octet-stream', '.html': 'text/html', '.css': 'text/css',
                  '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml'}.items():
    mimetypes.add_type(kind, ext)

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json'}
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, fmt, *args):
        if '404' in (fmt % args) and 'favicon' not in (fmt % args):
            super().log_message(fmt, *args)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f'Makers Marks monitor: open http://localhost:{PORT}/   (Ctrl+C to stop)')
http.server.ThreadingHTTPServer(('', PORT), Handler).serve_forever()
