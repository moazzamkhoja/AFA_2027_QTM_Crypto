import json,urllib.request,urllib.parse,time,csv,re
from Crypto.Hash import keccak
KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
def es(p):
    p={**p,'apikey':KEY}; url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(p)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=45) as r: return json.load(r)
        except Exception: time.sleep(1.2)
    return None
def t0(sig):
    h=keccak.new(digest_bits=256); h.update(sig.encode()); return '0x'+h.hexdigest()
TRANSFER=t0('Transfer(address,address,uint256)')

print("===== (b) CONFIRM getLogs WORKS ON BSC (chainid 56) =====")
# BAKE on BSC; Transfer must return logs if multichain logs work
for sym,addr,cid in [('BAKE','0xe02df9e3e622debdd69fb838bb799e3f168902c5',56),
                     ('MDX','0x9c65ab58d8d978db963e63f2bfb7121627e3a739',56),
                     ('VVV','0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf',8453)]:
    d=es({'chainid':cid,'module':'logs','action':'getLogs','address':addr,'fromBlock':0,'toBlock':'latest','topic0':TRANSFER,'page':1,'offset':10})
    time.sleep(0.25)
    n=len(d['result']) if d and d.get('status')=='1' else 0
    print(f"  chain {cid} {sym}: Transfer logs returned = {n}  ({d.get('message') if d else 'noresp'})  -> getLogs {'WORKS' if n>0 else 'FAILED/empty'}")

print("\n===== (a) RESOLVE VARIANT VOTING EVENTS (read source, find real signature) =====")
rows={r['symbol']:r for r in csv.DictReader(open('04_code/_etherscan_lambda_findings.csv',encoding='utf-8'))}
VARIANTS=['ILV','CORE','SUPER','FLOKI','APEX','BEAM']
updated={}
for sym in VARIANTS:
    r=rows[sym]; cid=int(r['chainid']); addr=r['address']
    js=json.load(open(f'03_data/raw/etherscan_src/{cid}_{addr.lower()}.json'))
    res=js['result'][0]; abi=json.loads(res['ABI'])
    # every event whose name hints voting/power/delegation
    cands=[e for e in abi if e.get('type')=='event' and any(w in e.get('name','').lower() for w in ('vot','power','deleg','checkpoint'))]
    best=None
    print(f"\n  {sym}: candidate vote-events in ABI = {[e['name'] for e in cands]}")
    for e in cands:
        sig=f"{e['name']}({','.join(i['type'] for i in e['inputs'])})"
        hh=t0(sig)
        d=es({'chainid':cid,'module':'logs','action':'getLogs','address':addr,'fromBlock':0,'toBlock':'latest','topic0':hh,'page':1,'offset':100})
        time.sleep(0.25)
        n=len(d['result']) if d and d.get('status')=='1' else 0
        fb=''
        if n>0:
            bn=d['result'][0]['blockNumber']; fb=int(bn,16) if isinstance(bn,str) and bn.startswith('0x') else int(bn)
        print(f"      {sig:<52} logs={n} firstblk={fb}")
        if n>0 and (best is None or n>best[2]): best=(e['name'],sig,n,fb)
    if best:
        updated[sym]=('ERC20Votes-ACTIVE(variant)',best[1],best[2],best[3])
        print(f"    -> RESOLVED ACTIVE via {best[0]} ({best[2]} logs)")
    else:
        updated[sym]=('ERC20Votes-negligible(<=2deleg)',r['ch3_event'],0,'')
        print(f"    -> confirmed NEGLIGIBLE (no votes-weight event fires)")

# apply updates
for sym,(verd,ev,n,fb) in updated.items():
    rows[sym]['ch3']=verd; rows[sym]['ch3_event']=ev; rows[sym]['ch3_logs']=n; rows[sym]['ch3_firstblock']=fb
allrows=list(csv.DictReader(open('04_code/_etherscan_lambda_findings.csv',encoding='utf-8')))
for ar in allrows:
    if ar['symbol'] in updated: ar.update({'ch3':rows[ar['symbol']]['ch3'],'ch3_event':rows[ar['symbol']]['ch3_event'],'ch3_logs':rows[ar['symbol']]['ch3_logs'],'ch3_firstblock':rows[ar['symbol']]['ch3_firstblock']})
with open('04_code/_etherscan_lambda_findings.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=allrows[0].keys()); w.writeheader(); w.writerows(allrows)
print("\nfindings CSV updated.")
