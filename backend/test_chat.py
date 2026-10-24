import urllib.request
import json

# 1. Login
login_data = json.dumps({"email": "alex@univ.edu", "password": "password123"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    token = res["access_token"]
    print("Login successful! Token:", token[:20], "...")

# 2. Join AlgoRhythms (Group ID: 1) if not joined
try:
    req_join = urllib.request.Request("http://127.0.0.1:8000/api/groups/1/join", data=b"{}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req_join) as resp:
        print("Joined AlgoRhythms!")
except Exception as e:
    print("Already in group or joined:", e)

# 3. Test GET /api/chat/groups
req_chat_groups = urllib.request.Request("http://127.0.0.1:8000/api/chat/groups", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_chat_groups) as resp:
    groups = json.loads(resp.read().decode())
    print(f"Chat groups retrieved: {len(groups)} groups")
    if groups:
        print("First group:", groups[0]["name"])

# 4. Post a test message
post_data = json.dumps({"text": "Hey team! Ready for the Dynamic Programming sprint today?"}).encode('utf-8')
req_send = urllib.request.Request("http://127.0.0.1:8000/api/chat/groups/1/messages", data=post_data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
with urllib.request.urlopen(req_send) as resp:
    msg = json.loads(resp.read().decode())
    print("Sent test message:", msg["text"], "by", msg["user_name"])

# 5. List messages
req_msgs = urllib.request.Request("http://127.0.0.1:8000/api/chat/groups/1/messages", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req_msgs) as resp:
    all_msgs = json.loads(resp.read().decode())
    print(f"Total messages in AlgoRhythms: {len(all_msgs)}")
