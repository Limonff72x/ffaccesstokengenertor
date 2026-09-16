from http.server import BaseHTTPRequestHandler
import json, urllib.parse, requests, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def process_token(raw_token):
    eat_token = raw_token
    if raw_token.startswith("http") or "?" in raw_token:
        try:
            parsed = urllib.parse.urlparse(raw_token)
            params = urllib.parse.parse_qs(parsed.query)
            if 'eat' in params and params['eat']:
                eat_token = params['eat'][0]
        except Exception:
            pass

    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Linux; Android 13; Mobile) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Mobile Safari/537.36")
    }
    resp = requests.get(api_url, headers=headers, allow_redirects=True,
                        timeout=20, verify=False)
    parsed = urllib.parse.urlparse(resp.url)
    final = urllib.parse.parse_qs(parsed.query)

    if 'access_token' in final:
        return {
            "success": True,
            "data": {
                "access_token": final['access_token'][0],
                "account_id":   final.get('account_id', ['Unknown'])[0],
                "nickname":     urllib.parse.unquote(final.get('nickname', ['Unknown'])[0]),
                "region":       final.get('region', ['Unknown'])[0]
            }
        }
    return {"success": False, "error": "Access token not found"}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            token = (data.get('token') or '').strip()
            if not token:
                result = {"success": False, "error": "Empty token"}
            else:
                result = process_token(token)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        self.send_response(200 if result.get("success") else 400)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
