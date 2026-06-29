import json,urllib.request,urllib.parse,time,csv
from Crypto.Hash import keccak
KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
def es(p):
    p={**p,'apikey':KEY}; url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(p)
    for _ in range(3):
        try:
            with urllib.request.urlopen(url,timeout=45) as r: return json.load(r)
        except Exception: time.sleep(1.0)
    return None
def t0(sig):
    h=keccak.new(digest_bits=256); h.update(sig.encode()); return '0x'+h.hexdigest()
TRANSFER=t0('Transfer(address,address,uint256)')

rows=list(csv.DictReader(open('04_code/_etherscan_lambda_findings.csv',encoding='utf-8')))

# definitive free/blocked probe per chain using a REAL bucket token on each chain
import collections
addr_by_chain=collections.defaultdict(list)
for r in rows: addr_by_chain[r['chainid']].append((r['symbol'],r['address']))
FREE={}
print("Definitive getLogs free-tier probe (real bucket addresses):")
for cid,lst in sorted(addr_by_chain.items(),key=lambda x:int(x[0])):
    sym,addr=lst[0]
    time.sleep(0.7)
    d=es({'chainid':int(cid),'module':'logs','action':'getLogs','address':addr,'fromBlock':0,'toBlock':'latest','topic0':TRANSFER,'page':1,'offset':3})
    free = bool(d and d.get('status')=='1')
    # also accept empty-but-not-error (status 0 w/ 'No records') as FREE if message isn't the paywall
    res=str(d.get('result')) if d else ''
    blocked_msg = 'not supported for this chain' in res
    if not free and not blocked_msg and d and isinstance(d.get('result'),list): free=True
    FREE[cid]= free and not blocked_msg
    print(f"  chain {cid:<6} {sym:<8}: {'FREE' if FREE[cid] else 'BLOCKED(paid)'}")

BLOCKED_CHAINS={c for c,f in FREE.items() if not f}

# --- corrections ---
VARIANT6={'ILV','CORE','SUPER','FLOKI','APEX','BEAM'}
n_relabel=0; n_revert=0
for r in rows:
    # (1) revert the 6 ETH variant tokens (free chain, reliable) to negligible
    if r['symbol'] in VARIANT6:
        r['ch3']='ERC20Votes-negligible(<=2deleg,DVC-never-fired)'
        r['ch3_logs']=''; r['ch3_firstblock']=''; n_revert+=1
    # (2) BLOCKED-chain tokens: log-based verdicts are NOT established on free tier
    if r['chainid'] in BLOCKED_CHAINS:
        if r['ch1'] not in ('-',''):
            r['ch1']=(r['ch1'].split('(')[0]+' [ABI-only; getLogs needs PAID plan on this chain]') if 'admin' not in r['ch1'] else r['ch1']
            r['ch1_logs']=''; r['ch1_firstblock']=''
        if r['ch3'] not in ('-',''):
            base='ERC20Votes' if 'ERC20Votes' in r['ch3'] else r['ch3'].split('(')[0]
            r['ch3']=base+'-ABIonly [getLogs needs PAID plan on this chain]'
            r['ch3_logs']=''; r['ch3_firstblock']=''
        n_relabel+=1

with open('04_code/_etherscan_lambda_findings.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print(f"\ncorrections: reverted {n_revert} ETH variant tokens to negligible; relabeled {n_relabel} blocked-chain tokens")
print("BLOCKED (paid) chains:",sorted(BLOCKED_CHAINS), " FREE chains:",sorted(c for c,f in FREE.items() if f))

# final tally
from collections import Counter
ch1_ok=[r['symbol'] for r in rows if r['ch1']=='GENUINE']
ch3_ok=[r['symbol'] for r in rows if r['ch3']=='ERC20Votes']
ch3_abi_paid=[r['symbol'] for r in rows if 'PAID' in r['ch3']]
ch1_abi_paid=[r['symbol'] for r in rows if 'PAID' in r['ch1']]
print("\n================ FINAL, FREE-TIER-VERIFIED ================")
print(f"CH1 genuine lock/stake, getLogs CONFIRMED (free, ETH): {len(ch1_ok)}  -> {sorted(ch1_ok)}")
print(f"CH3 ACTIVE delegated voting, getLogs CONFIRMED (free): {len(ch3_ok)}  -> {sorted(ch3_ok)}")
print(f"CH3 ERC20Votes infra in ABI but log-confirm needs PAID plan (BSC/Base/Arb/Avax): {len(ch3_abi_paid)} -> {sorted(ch3_abi_paid)}")
print(f"CH1 lock infra in ABI but needs PAID plan: {len(ch1_abi_paid)} -> {sorted(ch1_abi_paid)}")
