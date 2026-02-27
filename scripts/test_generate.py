#!/usr/bin/env python3
import urllib.request
import json
import urllib.error

# Create project
req = urllib.request.Request(
    "http://127.0.0.1:8080/api/projects",
    data=b'{"start_chat": true}',
    method="POST",
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=5) as r:
    d = json.loads(r.read().decode())
    pid = d["project_id"]
    print("Created project:", pid)

# POST generate
url = f"http://127.0.0.1:8080/api/projects/{pid}/generate"
req2 = urllib.request.Request(
    url, data=b"{}", method="POST", headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req2, timeout=5) as r:
        print("Generate OK:", r.read().decode())
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Content-Type:", e.headers.get("Content-Type"))
    print("Body:", e.read().decode()[:400])
