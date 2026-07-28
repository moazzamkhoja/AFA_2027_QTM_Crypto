# Session 039 Task A1: probe Subscan /api/scan/daily for transfer-volume history
import json, time, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]
HDR = {"Content-Type": "application/json", "X-API-Key": key}

for chain in ["polkadot", "kusama"]:
    url = f"https://{chain}.api.subscan.io/api/scan/daily"
    for cat in ["transfer", "extrinsic", "transaction", "fee"]:
        body = {"start": "2020-08-01" if chain == "polkadot" else "2019-11-01",
                "end": "2026-06-30", "format": "day", "category": cat}
        try:
            r = requests.post(url, headers=HDR, json=body, timeout=30)
            d = r.json()
        except Exception as e:
            print(f"{chain}/{cat}: EXC {e}")
            continue
        code = d.get("code")
        msg = d.get("message")
        lst = (d.get("data") or {}).get("list") or []
        print(f"{chain}/{cat}: http={r.status_code} code={code} msg={msg} n={len(lst)}")
        if lst:
            print("  first:", json.dumps(lst[0]))
            print("  last: ", json.dumps(lst[-1]))
        time.sleep(1)
