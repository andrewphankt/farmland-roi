import http.server
import socketserver

PORT = 8000

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 1. Allow Streamlit to access the files
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        
        # 2. THE MAGIC FIX: Tell the browser to unzip the Tippecanoe tiles!
        if self.path.endswith('.pbf'):
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', 'application/vnd.mapbox-vector-tile')
            
        return super().end_headers()

if __name__ == '__main__':
    # Using TCPServer with allow_reuse_address so it doesn't crash if you restart it quickly
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Serving tiles with CORS and GZIP support on http://localhost:{PORT}")
        httpd.serve_forever()
