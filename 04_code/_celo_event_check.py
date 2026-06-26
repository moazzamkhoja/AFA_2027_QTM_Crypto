import json, requests, time
from pathlib import Path
KEY = json.loads(Path("04_code/.api_keys.json").read_text())["etherscan"] if Path("04_code/.api_keys.json").exists() else json.loads(Path(".api_keys.json").read_text())["etherscan"]
BASE = "https://api.etherscan.io/v2/api"; CID = 42220
LG = "0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E"
H = {"User-Agent": "Mozilla/5.0"}
TOP = {'lock': '0x0f0f2fc5b4c987a49e1663ce2c2d65de12f3b701ff02b4d09461421e63e609e7',
       'unlock': '0xb1a3aef2a332070da206ad1868a5e327f5aa5144e00e9a7b40717c153158a588',
       'relock': '0xa823fc38a01c2f76d7057a79bb5c317710f26f7dbdea78634598d5519d0f7cb0'}
def api(p):
    for t in range(5):
        try:
            r = requests.get(BASE, params={'chainid': CID, 'apikey': KEY, **p}, headers=H, timeout=50)
            time.sleep(0.2); return r.json()
        except Exception:
            time.sleep(0.5*(t+1))
    return {'result': None}
bn = int(api({'module': 'proxy', 'action': 'eth_blockNumber'})['result'], 16)
def sumtopic(top, lo, hi, depth=0):
    j = api({'module': 'logs', 'action': 'getLogs', 'address': LG, 'topic0': top, 'fromBlock': lo, 'toBlock': hi})
    res = j.get('result')
    if not isinstance(res, list):
        if lo >= hi: return 0
        mid = (lo+hi)//2; return sumtopic(top, lo, mid, depth+1)+sumtopic(top, mid+1, hi, depth+1)
    if len(res) >= 1000 and lo < hi:
        mid = (lo+hi)//2; return sumtopic(top, lo, mid, depth+1)+sumtopic(top, mid+1, hi, depth+1)
    tot = 0
    for lg in res:
        d = lg.get('data', '0x')
        if d and d != '0x': tot += int(d[2:66], 16)
    return tot
print('current block', bn)
locked = sumtopic(TOP['lock'], 0, bn); relock = sumtopic(TOP['relock'], 0, bn); unlock = sumtopic(TOP['unlock'], 0, bn)
net = (locked+relock-unlock)/1e18
print(f'lock={locked/1e18:,.0f} relock={relock/1e18:,.0f} unlock={unlock/1e18:,.0f}')
print(f'reconstructed total locked = {net:,.2f} CELO  (target getTotalLockedGold=82,425,700.77)')
