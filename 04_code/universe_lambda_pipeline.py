"""Universe-wide Etherscan lambda-channel identification pipeline.
For every token/other asset: resolve EVM address (CMC platforms[] + identity map),
read verified contract (getsourcecode), classify ch1(lock/stake)/ch3(voting) from ABI,
and on free-tier chains confirm via getLogs. Resumable: skips rows already in the output CSV.
"""
import csv,json,re,urllib.request,urllib.parse,time,os,sys
from Crypto.Hash import keccak

KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
OUT='04_code/_universe_lambda_findings.csv'
FREE_CHAINS={1,137,42161,81457}          # getLogs works on free tier (measured live)
NAME2CHAINID={'ethereum':1,'eth':1,'bnb smart chain (bep20)':56,'bnb smart chain':56,'binance':56,'bsc':56,
 'binance-smart-chain':56,'bnb':56,'polygon':137,'polygon pos':137,'matic':137,'base':8453,'arbitrum':42161,
 'arbitrum one':42161,'optimism':10,'op mainnet':10,'op':10,'avalanche c-chain':43114,'avalanche':43114,'avax':43114,
 'avalanche-c-chain':43114,'gnosis':100,'gnosis chain':100,'xdai':100,'linea':59144,'blast':81457,'mantle':5000,
 'celo':42220,'moonbeam':1284,'moonriver':1285,'opbnb':204,'sonic':146,'unichain':130,'berachain':80094,'sei v2':1329,
 'sei':1329,'apechain':33139,'xdc network':50,'xdc':50,'bittorrent-chain':199,'bittorrent':199,'world chain':480,
 'worldchain':480,'world':480}
PRIORITY=[1,56,137,42161,8453,10,43114,100,59144,81457,5000,42220,1284,204,146,130,80094,1329,33139,50,199,480]

def es(p):
    p={**p,'apikey':KEY}; url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(p)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=45) as r: return json.load(r)
        except Exception: time.sleep(1.2)
    return None
def t0(name,inputs):
    sig=f"{name}({','.join(i.get('type','') for i in inputs)})"
    h=keccak.new(digest_bits=256); h.update(sig.encode()); return '0x'+h.hexdigest(),sig

os.makedirs('03_data/raw/cmc_detail',exist_ok=True)
os.makedirs('03_data/raw/etherscan_src',exist_ok=True)
def cmc_detail(cid):
    c=f'03_data/raw/cmc_detail/{cid}.json'
    if os.path.exists(c):
        try: return json.load(open(c))
        except Exception: pass
    url=f'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?id={cid}'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                d=json.load(r); json.dump(d,open(c,'w')); return d
        except Exception: time.sleep(1.0)
    return None
def getsource(chainid,addr):
    c=f'03_data/raw/etherscan_src/{chainid}_{addr.lower()}.json'
    if os.path.exists(c):
        try: return json.load(open(c))
        except Exception: pass
    d=es({'chainid':chainid,'module':'contract','action':'getsourcecode','address':addr})
    time.sleep(0.22)
    if d: json.dump(d,open(c,'w'))
    return d

CH1_GENUINE_EV={'stakestart','staked','stake','locked','balancelocked','lockcreated','createlock','newlock','lockedbalance'}
CH1_ADMIN_EV={'addtokenlock','lockuser','freezed','inflationtokensminted','tokenslocked','vestinglock'}
CH1_GENUINE_FN={'stake','stakestart','lock','createlock','create_lock','deposit_for','lockbalance','depositfor'}
CH1_ADMIN_FN={'addtokenlock','lockuser','setvesting','lockfrom'}
CH3_STRONG={'delegatevoteschanged','votingpowerchanged','delegatedpowerchanged'}
CH3_PARTIAL={'delegatechanged'}

def idmap_pair(m):
    raw=(m.get('token_address') or '').strip()
    if not raw: return []
    chain=(m.get('token_chain') or '').strip()
    if ':' in raw:
        pre,a=raw.split(':',1); return [(pre,a)]
    if re.fullmatch(r'0x[0-9a-fA-F]{40}',raw): return [(chain or 'ethereum',raw)]
    return [(chain,raw)]

def verify(chainid,addr,t0hash):
    d=es({'chainid':chainid,'module':'logs','action':'getLogs','address':addr,'fromBlock':0,'toBlock':'latest','topic0':t0hash,'page':1,'offset':100})
    time.sleep(0.22)
    if d and d.get('status')=='1' and isinstance(d.get('result'),list) and d['result']:
        bn=d['result'][0]['blockNumber']; fb=int(bn,16) if isinstance(bn,str) and bn.startswith('0x') else int(bn)
        return len(d['result']),fb
    return 0,None

# ---- input universe: token + other ----
idm=[r for r in csv.DictReader(open('03_data/phase1/asset_onchain_identity.csv',encoding='utf-8')) if r['asset_class'] in ('token','other')]
done=set()
cols=['cmc_id','symbol','name','asset_class','chainid','address','reachable','getlogs_free','contract',
      'ch1','ch1_event','ch1_logs','ch1_firstblock','ch2','ch3','ch3_event','ch3_logs','ch3_firstblock','n_platforms']
if os.path.exists(OUT):
    done={r['cmc_id'] for r in csv.DictReader(open(OUT,encoding='utf-8'))}
    fh=open(OUT,'a',newline='',encoding='utf-8'); w=csv.DictWriter(fh,fieldnames=cols)
else:
    fh=open(OUT,'w',newline='',encoding='utf-8'); w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()

todo=[m for m in idm if m['cmc_id'] not in done]
print(f"universe token+other={len(idm)}, already done={len(done)}, to process={len(todo)}",flush=True)

for i,m in enumerate(todo):
    cid=m['cmc_id']; sym=m['symbol']; name=m['name']
    rec={k:'' for k in cols}; rec.update({'cmc_id':cid,'symbol':sym,'name':name,'asset_class':m['asset_class'],'ch1':'-','ch3':'-','ch2':'','reachable':'no','getlogs_free':''})
    cands=list(idmap_pair(m))
    d=cmc_detail(cid); time.sleep(0.16)
    nplat=0
    if d:
        pl=(d.get('data') or {}).get('platforms')
        if isinstance(pl,list):
            for p in pl:
                pn=p.get('contractPlatform') or p.get('platform') or ''
                ad=p.get('contractAddress') or p.get('address') or ''
                if ad: cands.append((pn,ad)); nplat+=1
    rec['n_platforms']=nplat
    scored=[]
    for cn,ad in cands:
        chid=NAME2CHAINID.get((cn or '').strip().lower())
        if chid and re.fullmatch(r'0x[0-9a-fA-F]{40}',ad.strip()):
            scored.append((PRIORITY.index(chid) if chid in PRIORITY else 99,chid,ad.strip()))
    if not scored:
        w.writerow(rec);
        if (i+1)%50==0: fh.flush(); print(f'  ...{i+1}/{len(todo)}',flush=True)
        continue
    scored.sort(); chainid=scored[0][1]; addr=scored[0][2]
    rec.update({'reachable':'yes','chainid':chainid,'address':addr,'getlogs_free':'yes' if chainid in FREE_CHAINS else 'no(PAID)'})
    rec['ch2']='Transfer-log' if chainid in FREE_CHAINS else 'Transfer-log(PAID)'
    src=getsource(chainid,addr)
    if not (src and src.get('status')=='1' and src.get('result')):
        w.writerow(rec); continue
    res=src['result'][0]; rec['contract']=res.get('ContractName','')
    abi_raw=res.get('ABI',''); impl=res.get('Implementation','')
    if (res.get('Proxy')=='1' or abi_raw=='Contract source code not verified') and re.fullmatch(r'0x[0-9a-fA-F]{40}',impl or ''):
        d2=getsource(chainid,impl)
        if d2 and d2.get('status')=='1' and d2['result'][0].get('ABI') not in ('','Contract source code not verified'):
            abi_raw=d2['result'][0]['ABI']; rec['contract']+=f"->impl:{d2['result'][0].get('ContractName','')}"
    if not abi_raw or abi_raw=='Contract source code not verified':
        rec['contract']=(rec['contract'] or '')+' [UNVERIFIED]'; w.writerow(rec); continue
    try: abi=json.loads(abi_raw)
    except Exception: w.writerow(rec); continue
    events={e['name'].lower():e for e in abi if e.get('type')=='event' and e.get('name')}
    fns={f['name'].lower() for f in abi if f.get('type')=='function' and f.get('name')}
    free=chainid in FREE_CHAINS
    # Channel 1
    ch1_ev=None
    for evn in events:
        if evn in CH1_GENUINE_EV and evn not in CH1_ADMIN_EV and (any(fn in fns for fn in CH1_GENUINE_FN) or evn in ('stakestart','staked','balancelocked','locked')):
            ch1_ev=evn; break
    if ch1_ev:
        e=events[ch1_ev]; hh,sig=t0(e['name'],e.get('inputs',[])); rec['ch1_event']=sig
        if free:
            n,fb=verify(chainid,addr,hh); rec['ch1']='GENUINE' if n>0 else 'event-declared-no-logs'; rec['ch1_logs']=n; rec['ch1_firstblock']=fb or ''
        else:
            rec['ch1']='lock/stake-ABIonly[PAID-chain]'
    elif any(e in events for e in CH1_ADMIN_EV) or any(f in fns for f in CH1_ADMIN_FN):
        rec['ch1']='admin/vesting-lock(not conviction)'
    # Channel 3
    ch3_ev=None; strong=False
    for evn in CH3_STRONG:
        if evn in events: ch3_ev=evn; strong=True; break
    if not ch3_ev:
        for evn in CH3_PARTIAL:
            if evn in events: ch3_ev=evn; break
    if ch3_ev:
        e=events[ch3_ev]; hh,sig=t0(e['name'],e.get('inputs',[])); rec['ch3_event']=sig
        if not free:
            rec['ch3']=('ERC20Votes' if strong else 'delegation')+'-ABIonly[PAID-chain]'
        else:
            n,fb=verify(chainid,addr,hh)
            if strong:
                if n>0: rec['ch3']='ERC20Votes-ACTIVE'; rec['ch3_logs']=n; rec['ch3_firstblock']=fb or ''
                else:
                    # distinguish dormant vs negligible via DelegateChanged
                    dc=events.get('delegatechanged')
                    dn=0
                    if dc: dh,_=t0(dc['name'],dc.get('inputs',[])); dn,_=verify(chainid,addr,dh)
                    rec['ch3']='ERC20Votes-DORMANT' if dn==0 else 'ERC20Votes-negligible'
            else:
                rec['ch3']='delegation-only' if n>0 else 'delegation-DORMANT'; rec['ch3_logs']=n; rec['ch3_firstblock']=fb or ''
    w.writerow(rec)
    if (i+1)%25==0: fh.flush(); print(f'  ...{i+1}/{len(todo)} (last {sym} ch1={rec["ch1"]} ch3={rec["ch3"]})',flush=True)

fh.flush(); fh.close()
print("DONE_UNIVERSE_PIPELINE",flush=True)
