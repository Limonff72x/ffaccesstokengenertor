from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, static_folder='.', static_url_path='')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def submit():
    # CORS (প্রয়োজনে)
    if request.method == 'OPTIONS':
        return _cors(jsonify({}))

    try:
        data = request.get_json(force=True)
    except Exception:
        return _cors(jsonify({"success": False, "error": "Invalid JSON"})), 400

    if not data or not isinstance(data, dict):
        return _cors(jsonify({"success": False, "error": "Invalid request"})), 400

    raw_token = (data.get('token') or '').strip()
    if not raw_token:
        return _cors(jsonify({"success": False, "error": "Empty token"})), 400

    # URL থেকে eat= বের করা
    eat_token = raw_token
    if raw_token.startswith("http") or "?" in raw_token:
        try:
            parsed = urllib.parse.urlparse(raw_token)
            params = urllib.parse.parse_qs(parsed.query)
            if 'eat' in params and params['eat']:
                eat_token = params['eat'][0]
        except Exception:
            pass

    if not eat_token:
        return _cors(jsonify({"success": False, "error": "Could not find EAT token"})), 400

    # === main.py এর eat_to_access_token() লজিক ===
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Mobile) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Mobile Safari/537.36"
        )
    }

    try:
        response = requests.get(
            api_url,
            headers=headers,
            allow_redirects=True,
            timeout=20,
            verify=False
        )
        parsed_final = urllib.parse.urlparse(response.url)
        final_params = urllib.parse.parse_qs(parsed_final.query)

        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            account_id = final_params.get('account_id', ['Unknown'])[0]
            nickname = final_params.get('nickname', ['Unknown'])[0]
            region = final_params.get('region', ['Unknown'])[0]

            return _cors(jsonify({
                "success": True,
                "data": {
                    "access_token": access_token,
                    "account_id": account_id,
                    "nickname": urllib.parse.unquote(nickname),
                    "region": region
                }
            }))

        return _cors(jsonify({
            "success": False,
            "error": "Access token not found. EAT token may be expired or invalid."
        })), 400

    except requests.exceptions.Timeout:
        return _cors(jsonify({"success": False, "error": "Request timeout"})), 504
    except Exception as e:
        return _cors(jsonify({"success": False, "error": str(e)})), 500


def _cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n\033[92m[✓] Server running: http://localhost:{port}\033[0m\n")
    app.run(host='0.0.0.0', port=port, debug=False)