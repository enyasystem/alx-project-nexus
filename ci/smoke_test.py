import sys
import time
import requests

BASE = 'http://127.0.0.1:8000'


def wait_for_server(timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f'{BASE}/api/docs/')
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def assert_redirect_root():
    r = requests.get(f'{BASE}/', allow_redirects=False)
    if r.status_code not in (301, 302):
        print('Root did not redirect:', r.status_code)
        print(r.text[:200])
        return False
    loc = r.headers.get('Location', '')
    if '/api/docs' not in loc:
        print('Root redirected to unexpected location:', loc)
        return False
    print('Root redirect OK ->', loc)
    return True


def assert_docs_ok():
    r = requests.get(f'{BASE}/api/docs/')
    if r.status_code != 200:
        print('/api/docs/ failed', r.status_code)
        return False
    print('/api/docs/ OK')
    return True


def assert_products_ok():
    r = requests.get(f'{BASE}/api/catalog/products/?limit=1')
    if r.status_code != 200:
        print('/api/catalog/products/ failed', r.status_code)
        return False
    try:
        data = r.json()
    except Exception:
        print('Products response not JSON')
        return False
    print('Products OK, count-ish:', 'results' in data or 'count' in data)
    return True


def run_jwt_flow():
    # Register user
    import uuid
    username = f'ciuser_{uuid.uuid4().hex[:8]}'
    pw = 'Passw0rd!'
    r = requests.post(f'{BASE}/api/auth/register/', json={'username': username, 'password': pw})
    if r.status_code not in (200, 201):
        print('Register failed', r.status_code, r.text[:200])
        return False
    # Obtain token
    r = requests.post(f'{BASE}/api/auth/token/', json={'username': username, 'password': pw})
    if r.status_code != 200:
        print('Token obtain failed', r.status_code, r.text[:200])
        return False
    data = r.json()
    if 'access' not in data:
        print('Token response missing access')
        return False
    print('JWT flow OK')
    return True


def main():
    if not wait_for_server(60):
        print('Server did not come up')
        sys.exit(2)
    ok = True
    ok &= assert_redirect_root()
    ok &= assert_docs_ok()
    ok &= assert_products_ok()
    ok &= run_jwt_flow()
    if not ok:
        print('Smoke tests failed')
        sys.exit(1)
    print('Smoke tests passed')


if __name__ == '__main__':
    main()
