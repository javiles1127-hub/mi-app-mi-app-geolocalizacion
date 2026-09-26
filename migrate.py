import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

firebase_helpers = """
import urllib.request
FIREBASE_URL = "https://tienda-gps-62152-default-rtdb.firebaseio.com"

def firebase_get(path):
    try:
        req = urllib.request.Request(f"{FIREBASE_URL}/{path}.json")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode('utf-8'))
            if isinstance(data, dict):
                return [v for k,v in data.items() if v is not None]
            return data if data is not None else []
    except Exception as e:
        print(f"Firebase GET error ({path}): {e}")
        return []

def firebase_put(path, data):
    try:
        req = urllib.request.Request(f"{FIREBASE_URL}/{path}.json", data=json.dumps(data).encode('utf-8'), method='PUT')
        with urllib.request.urlopen(req, timeout=5) as res:
            return True
    except Exception as e:
        print(f"Firebase PUT error ({path}): {e}")
        return False
"""

content = re.sub(r'data_store = \[\]', firebase_helpers, content)

content = re.sub(
    r"""                locations = \[\]\s+if os\.path\.exists\('locations\.json'\):.*?json\.dump\(locations, f\)""",
    """                locations = firebase_get('locations')\n                locations.append(location)\n                firebase_put('locations', locations)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                        prods = \[\]\s+if os\.path\.exists\('products\.json'\):.*?json\.dump\(prods, f\)""",
    """                        prods = firebase_get('products')\n                        for p in prods:\n                            if str(p.get('id')) == str(product_id):\n                                p['likes'] = p.get('likes', 0) + 1\n                                break\n                        firebase_put('products', prods)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""        elif self\.path == '/api/locations/clear':.*?self\.send_response\(200\)""",
    """        elif self.path == '/api/locations/clear':\n            firebase_put('locations', [])\n            self.send_response(200)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                import os\s+if os\.path\.exists\('locations\.json'\):.*?json\.dump\(locs, f\)""",
    """                locs = firebase_get('locations')\n                locs = [loc for loc in locs if loc and loc.get('id') not in ids_to_delete]\n                firebase_put('locations', locs)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                products = \[\]\s+if os\.path\.exists\('products\.json'\):.*?json\.dump\(products, f\)""",
    """                products = firebase_get('products')\n                if 'id' in payload and 'name' in payload:\n                    for p in products:\n                        if p and str(p.get('id')) == str(payload['id']):\n                            p['name'] = payload['name']\n                            break\n                firebase_put('products', products)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                contacts = \[\]\s+if os\.path\.exists\('contacts\.json'\):.*?json\.dump\(contacts, f\)""",
    """                contacts = firebase_get('contacts')\n                contacts.append(payload)\n                firebase_put('contacts', contacts)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                if not os\.path\.exists\('uploads'\):.*?print\("Error actualizando products\.json:", ex\)""",
    """                import mimetypes\n                mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'\n                data_uri = f"data:{mime_type};base64,{filedata_b64}"\n                try:\n                    products = firebase_get('products')\n                    new_product = {\n                        "id": str(int(time.time())),\n                        "image": data_uri,\n                        "name": "Look Añadido",\n                        "likes": 0\n                    }\n                    products.append(new_product)\n                    firebase_put('products', products)\n                    filepath = data_uri\n                except Exception as ex:\n                    print("Error actualizando Firebase products:", ex)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                import os\s+if os\.path\.exists\('contacts\.json'\):.*?json\.dump\(conts, f\)""",
    """                conts = firebase_get('contacts')\n                conts = [c for c in conts if c and c.get('id') not in ids_to_delete]\n                firebase_put('contacts', conts)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""                import os\s+if os\.path\.exists\('products\.json'\):.*?json\.dump\(products, f\)""",
    """                products = firebase_get('products')\n                products = [p for p in products if p and str(p.get('id')) != str(prod_id)]\n                firebase_put('products', products)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""        elif self\.path == '/api/products':\s+products = \[\]\s+if os\.path\.exists\('products\.json'\):.*?self\.send_response\(200\)""",
    """        elif self.path == '/api/products':\n            products = firebase_get('products')\n            self.send_response(200)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""        elif self\.path == '/api/locations':\s+locations = \[\]\s+if os\.path\.exists\('locations\.json'\):.*?self\.send_response\(200\)""",
    """        elif self.path == '/api/locations':\n            locations = firebase_get('locations')\n            self.send_response(200)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""        elif self\.path == '/api/contacts':\s+contacts = \[\]\s+if os\.path\.exists\('contacts\.json'\):.*?self\.send_response\(200\)""",
    """        elif self.path == '/api/contacts':\n            contacts = firebase_get('contacts')\n            self.send_response(200)""",
    content, flags=re.DOTALL
)

content = re.sub(
    r"""        elif self\.path == '/api/contacts/clear':.*?self\.send_response\(200\)""",
    """        elif self.path == '/api/contacts/clear':\n            firebase_put('contacts', [])\n            self.send_response(200)""",
    content, flags=re.DOTALL
)

with open('server_new.py', 'w', encoding='utf-8') as f:
    f.write(content)
