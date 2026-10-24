import urllib.request
import json

# 1. Login
login_data = json.dumps({"email": "alex@univ.edu", "password": "password123"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    token = res["access_token"]
    print("Login successful!")

# 2. Test create group
new_group_payload = {
    "name": "Distributed Systems Lab",
    "course": "CS 5412: Cloud Computing",
    "description": "Weekly sprints designing fault-tolerant consensus systems and Raft implementations.",
    "topic_ids": [1, 2],
    "max_members": 4,
    "pace": "Project sprint",
    "mode": "hybrid",
    "venue": "Gates Hall 310 / Zoom",
    "meeting_link": "https://zoom.us/j/123456789",
    "study_days": ["Wed", "Fri"],
    "start_hour": 15,
    "end_hour": 18
}

req_create = urllib.request.Request(
    "http://127.0.0.1:8000/api/groups",
    data=json.dumps(new_group_payload).encode('utf-8'),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req_create) as resp:
        created = json.loads(resp.read().decode())
        print("Created team successfully:", created["name"], "- Pace:", created["pace"], "- Venue:", created["venue"])
except Exception as e:
    print("Create team response:", e)

# 3. Check GET /api/groups for extras
req_groups = urllib.request.Request("http://127.0.0.1:8000/api/groups")
with urllib.request.urlopen(req_groups) as resp:
    groups = json.loads(resp.read().decode())
    print(f"Total groups in list: {len(groups)}")
    found = next((g for g in groups if g["name"] == "Distributed Systems Lab"), None)
    if found:
        print("Verified extras in GET /api/groups:", {
            "pace": found.get("pace"),
            "mode": found.get("mode"),
            "venue": found.get("venue"),
            "study_days": found.get("study_days")
        })
