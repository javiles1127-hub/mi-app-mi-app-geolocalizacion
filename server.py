from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import datetime

data_store = []

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/location':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                location = json.loads(post_data.decode('utf-8'))
                location['ip'] = self.client_address[0]
                location['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_store.append(location)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/api/locations':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(data_store).encode('utf-8'))
        else:
            super().do_GET()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), CustomHandler)
    print("Servidor iniciado en http://localhost:8080")
    print("Catálogo público: http://localhost:8080")
    print("Panel de administración: http://localhost:8080/admin.html")
    server.serve_forever()
