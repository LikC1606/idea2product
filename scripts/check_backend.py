#!/usr/bin/env python3
"""Quick check that the backend is running and returns JSON."""
import urllib.request
import sys

url = "http://127.0.0.1:8080/api/health"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as r:
        ct = r.headers.get("Content-Type", "")
        body = r.read().decode()
        if "application/json" in ct:
            print("OK: Backend is running and returns JSON")
            print(body[:200])
            sys.exit(0)
        else:
            print("ERROR: Backend returned non-JSON")
            print("Content-Type:", ct)
            print("Body:", body[:200])
            sys.exit(1)
except urllib.error.URLError as e:
    print("ERROR: Cannot reach backend at", url)
    print(e)
    print("\nStart the backend with: python -m src.web.app")
    sys.exit(1)
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)
