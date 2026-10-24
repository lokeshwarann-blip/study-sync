import urllib.request
import json

# 1. Login
login_data = json.dumps({"email": "alex@univ.edu", "password": "password123"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    token = res["access_token"]
    print("Login successful! Token:", token[:20], "...")

# 2. Get Me
req2 = urllib.request.Request("http://127.0.0.1:8000/api/users/me", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req2) as resp:
    user = json.loads(resp.read().decode())
    print("GET /api/users/me successful! Logged in as:", user["name"], f"({user['email']})")

# 3. Get Wheel suggestions
req3 = urllib.request.Request("http://127.0.0.1:8000/api/suggestions/wheel", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req3) as resp:
    wheel = json.loads(resp.read().decode())
    print("GET /api/suggestions/wheel successful! Received", len(wheel), "matched cohorts.")
    print("Top Match:", wheel[0]["label"], f"- Score: {wheel[0]['match_score']}%")
