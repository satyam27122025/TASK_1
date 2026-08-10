import json
import sqlite3
import time
import urllib.request
import urllib.error

GATEWAY_URL = "http://127.0.0.1:8000"
USER_DB = r"D:\TASK\TASK\user-service\db.sqlite3"
NOTIFICATION_DB = r"D:\TASK\TASK\notification-service\db.sqlite3"


def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed


def run_tests():
    print("=== STARTING SYSTEM VERIFICATION TESTS ===")
    
    print("\n--- Testing Health Endpoints ---")
    status_code, body = make_request(f"{GATEWAY_URL}/health")
    print(f"Gateway /health -> HTTP {status_code}: {body}")
    assert status_code == 200 and body.get("status") == "ok"
    
    status_code, body = make_request("http://127.0.0.1:8001/health/")
    print(f"User Service /health/ -> HTTP {status_code}: {body}")
    assert status_code == 200 and body.get("status") == "ok"
    
    status_code, body = make_request("http://127.0.0.1:8002/health/")
    print(f"Notification Service /health/ -> HTTP {status_code}: {body}")
    assert status_code == 200 and body.get("status") == "ok"
    
    timestamp = int(time.time())
    username = f"e2etest_{timestamp}"
    email = f"e2etest_{timestamp}@example.com"
    password = "TestPassword123!"
    
    print(f"\n--- Testing Registration via Gateway for username: {username} ---")
    reg_payload = {"username": username, "email": email, "password": password}
    status_code, body = make_request(f"{GATEWAY_URL}/api/users/register/", method="POST", data=reg_payload)
    print(f"Register Response -> HTTP {status_code}: {body}")
    assert status_code == 201, f"Registration failed: {body}"
    user_id = body["user"]["id"]
    print(f"Successfully registered user ID: {user_id}")
    
    print("\n--- Testing Duplicate Registration Handling ---")
    status_code, body = make_request(f"{GATEWAY_URL}/api/users/register/", method="POST", data=reg_payload)
    print(f"Duplicate Register Response -> HTTP {status_code}: {body}")
    assert status_code == 400
    
    print("\n--- Testing Login via Gateway ---")
    login_payload = {"username": username, "password": password}
    status_code, body = make_request(f"{GATEWAY_URL}/api/users/login/", method="POST", data=login_payload)
    print(f"Login Response -> HTTP {status_code}: {body}")
    assert status_code == 200 and "access" in body and "refresh" in body
    access_token = body["access"]
    print("Obtained access token successfully!")
    
    print("\n--- Testing Protected Profile Endpoint via Gateway with JWT ---")
    headers = {"Authorization": f"Bearer {access_token}"}
    status_code, body = make_request(f"{GATEWAY_URL}/api/users/profile/", method="GET", headers=headers)
    print(f"Profile Response -> HTTP {status_code}: {body}")
    assert status_code == 200 and body.get("username") == username
    
    print("\n--- Testing Invalid JWT Authorization ---")
    invalid_headers = {"Authorization": "Bearer invalid.jwt.token"}
    status_code, body = make_request(f"{GATEWAY_URL}/api/users/profile/", method="GET", headers=invalid_headers)
    print(f"Invalid Profile Response -> HTTP {status_code}: {body}")
    assert status_code == 401
    
    print("\n--- Verifying Notification Record in Notification Service SQLite DB ---")
    time.sleep(2)
    conn = sqlite3.connect(NOTIFICATION_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, email, message, status, event_id, created_at FROM notifications_notification WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    print("Notification record found in DB:", row)
    assert row is not None, f"No notification found in DB for user_id {user_id}"
    n_id, n_user_id, n_email, n_message, n_status, n_event_id, n_created_at = row
    assert n_user_id == user_id
    assert n_email == email
    assert n_status == "sent"
    assert n_event_id is not None
    print(f"Confirmed: Event {n_event_id} processed over NATS JetStream and saved to SQLite!")
    
    print("\n==========================================")
    print("ALL SYSTEM INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==========================================")


if __name__ == "__main__":
    run_tests()
