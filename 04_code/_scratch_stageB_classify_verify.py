import csv,json,re,urllib.request,urllib.parse,time,os
from Crypto.Hash import keccak

KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
def es(params):
    params={**params,'apikey':KEY}
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=45) as r: return json.load(r)
        except Exception: time.sleep(1.2)
    return None

def topic0(name,inputs):
    types=[]
    for i in inputs:
        t=i.get('type','')
        types.append(t)
    sig=f"{name}({','.join(types)})"
    h=keccak.new(digest_bits=256); h.update(sig.encode()); return '0x'+h.hexdigest(), sig

os.makedirs('03_data/raw/etherscan_src',exist_ok=True)
def getsource(chainid,addr):
    cache=f'03_data/raw/etherscan_src/{chainid}_{addr.lower()}.json'
    if os.path.exists(cache):
        try: return json.load(open(cache))
        except Exception: pass
    d=es({'chainid':chainid,'module':'contract','action':'getsourcecode','address':addr})
    time.sleep(0.22)
    if d: json.dump(d,open(cache,'w'))
    return d

# mechanism event classification
CH1_GENUINE_EV={'stakestart','staked','stake','locked','balancelocked','lockcreated','depositfor','createlock','lock','newlock','lockedbalance'}
CH1_ADMIN_EV={'addtokenlock','lockuser','freezed','inflationtokensminted','tokenslocked','vestinglock'}
CH3_STRONG_EV={'delegatevoteschanged','votingpowerchanged','delegatedpowerchanged'}
CH3_PARTIAL_EV={'delegatechanged'}
CH1_GENUINE_FN={'stake','stakestart','lock','createlock','create_lock','deposit_for','lockbalance','depositfor'}
CH1_ADMIN_FN={'addtokenlock','lockuser','setvesting','lockfrom'}

reach=[r for r in csv.DictReader(open('04_code/_etherscan_reach_resolve.csv',encoding='utf-8')) if r['reachable']=='True']
print(f"classifying {len(reach)} reachable contracts...")

def verify_event(chainid,addr,t0):
    # confirm event fires & is historically queryable
    d=es({'chainid':chainid,'module':'logs','action':'getLogs','address':addr,
          'fromBlock':0,'toBlock':'latest','topic0':t0,'page':1,'offset':1000})
    time.sleep(0.22)
    if d and d.get('status')=='1' and d['result']:
        logs=d['result']
        first_block=int(logs[0]['blockNumber'],16) if isinstance(logs[0]['blockNumber'],str) and logs[0]['blockNumber'].startswith('0x') else int(logs[0]['blockNumber'])
        return len(logs), first_block
    return 0, None

out=[]
for i,r in enumerate(reach):
    cid=r['cmc_id']; sym=r['symbol']; name=r['name']
    chainid=int(r['picked_chainid']); addr=r['picked_address']
    d=getsource(chainid,addr)
    rec={'cmc_id':cid,'symbol':sym,'name':name,'chainid':chainid,'address':addr,
         'verified':False,'contract':'','is_proxy':'','ch1':'-','ch1_event':'','ch1_logs':'','ch1_firstblock':'',
         'ch3':'-','ch3_event':'','ch3_logs':'','ch3_firstblock':'','ch2':'Transfer(universal)'}
    if not (d and d.get('status')=='1' and d.get('result')):
        out.append(rec); continue
    res=d['result'][0]
    rec['contract']=res.get('ContractName','')
    rec['is_proxy']=res.get('Proxy','0')
    abi_raw=res.get('ABI','')
    impl=res.get('Implementation','')
    # if proxy with implementation, pull implementation ABI for true logic
    if (res.get('Proxy')=='1' or abi_raw=='Contract source code not verified') and impl and re.fullmatch(r'0x[0-9a-fA-F]{40}',impl):
        d2=getsource(chainid,impl)
        if d2 and d2.get('status')=='1' and d2['result'][0].get('ABI') not in ('','Contract source code not verified'):
            abi_raw=d2['result'][0]['ABI']; rec['contract']+=f"->impl:{d2['result'][0].get('ContractName','')}"
    if not abi_raw or abi_raw=='Contract source code not verified':
        out.append(rec); continue
    rec['verified']=True
    try: abi=json.loads(abi_raw)
    except Exception: out.append(rec); continue
    events={e['name'].lower():e for e in abi if e.get('type')=='event' and e.get('name')}
    fns={f['name'].lower() for f in abi if f.get('type')=='function' and f.get('name')}
    # Channel 1
    ch1_ev=None
    for evn in events:
        if evn in CH1_GENUINE_EV and (any(fn in fns for fn in CH1_GENUINE_FN) or evn in ('stakestart','staked','balancelocked','locked')):
            # exclude pure-admin
            if evn in CH1_ADMIN_EV: continue
            ch1_ev=evn; break
    has_admin_lock = any(e in events for e in CH1_ADMIN_EV) or any(f in fns for f in CH1_ADMIN_FN)
    if ch1_ev:
        e=events[ch1_ev]; t0,sig=topic0(e['name'],e.get('inputs',[]))
        n,fb=verify_event(chainid,addr,t0)
        rec['ch1']='GENUINE' if n>0 else 'event-declared(no logs)'
        rec['ch1_event']=sig; rec['ch1_logs']=n; rec['ch1_firstblock']=fb or ''
    elif has_admin_lock:
        rec['ch1']='admin/vesting-lock(not conviction)'
    # Channel 3
    ch3_ev=None; strong=False
    for evn in CH3_STRONG_EV:
        if evn in events: ch3_ev=evn; strong=True; break
    if not ch3_ev:
        for evn in CH3_PARTIAL_EV:
            if evn in events: ch3_ev=evn; break
    if ch3_ev:
        e=events[ch3_ev]; t0,sig=topic0(e['name'],e.get('inputs',[]))
        n,fb=verify_event(chainid,addr,t0)
        rec['ch3']=('ERC20Votes' if strong else 'delegation-only') + ('' if n>0 else '(no logs)')
        rec['ch3_event']=sig; rec['ch3_logs']=n; rec['ch3_firstblock']=fb or ''
    out.append(rec)
    if (i+1)%40==0: print(f'  ...{i+1}/{len(reach)}')

with open('04_code/_etherscan_lambda_findings.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)

from collections import Counter
print("\n=== RESULTS (of %d reachable) ==="%len(out))
print("verified contracts:",sum(1 for r in out if r['verified']))
print("Channel 1:")
for k,v in Counter(r['ch1'] for r in out).most_common(): print(f"   {v:4d}  {k}")
print("Channel 3:")
for k,v in Counter(r['ch3'] for r in out).most_common(): print(f"   {v:4d}  {k}")
print("saved 04_code/_etherscan_lambda_findings.csv")
