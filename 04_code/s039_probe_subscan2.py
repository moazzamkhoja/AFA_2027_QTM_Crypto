# Session 039 Task A1b: find the free-tier history window for /api/scan/daily transfer
import json, time, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]
HDR = {"Content-Type": "application/json", "X-API-Key": key}
url = "https://polkadot.api.subscan.io/api/scan/daily"

for start, end in [("2026-06-01", "2026-06-30"), ("2026-04-01", "2026-06-30"),
                   ("2026-01-01", "2026-06-30"), ("2025-07-01", "2026-06-30")]:
    r = requests.post(url, headers=HDR, timeout=30,
                      json={"start": start, "end": end, "format": "day", "category": "transfer"})
    d = r.json()
    lst = (d.get("data") or {}).get("list") or []
    print(f"{start}..{end}: code={d.get('code')} msg={d.get('message')} n={len(lst)}")
    if lst:
        print("  sample keys:", list(lst[0].keys()))
        print("  first:", json.dumps(lst[0])[:300])
    time.sleep(1)
