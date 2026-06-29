import csv,json,re,urllib.request,urllib.parse,time,os

# Etherscan V2 supported MAINNET chainids (from /v2/chainlist), mapped from CMC/identity chain names
NAME2CHAINID={
 'ethereum':1,'eth':1,
 'bnb smart chain (bep20)':56,'bnb smart chain':56,'binance':56,'bsc':56,'binance-smart-chain':56,'bnb':56,
 'polygon':137,'polygon pos':137,'matic':137,
 'base':8453,
 'arbitrum':42161,'arbitrum one':42161,
 'optimism':10,'op mainnet':10,'op':10,
 'avalanche c-chain':43114,'avalanche':43114,'avax':43114,'avalanche-c-chain':43114,
 'gnosis':100,'gnosis chain':100,'xdai':100,
 'linea':59144,'blast':81457,'mantle':5000,'celo':42220,
 'moonbeam':1284,'moonriver':1285,'opbnb':204,'sonic':146,
 'unichain':130,'berachain':80094,'sei v2':1329,'sei':1329,'apechain':33139,
 'xdc network':50,'xdc':50,'bittorrent-chain':199,'bittorrent':199,'world chain':480,'worldchain':480,'world':480,
}
PRIORITY=[1,56,137,42161,8453,10,43114,100,59144,81457,5000,42220,1284,204,146,130,80094,1329,33139,50,199,480]

def to_chainid(name):
    if not name: return None
    return NAME2CHAINID.get(name.strip().lower())

audit=list(csv.DictReader(open('03_data/phase1/token_bucket1_full_audit.csv',encoding='utf-8')))
idm={r['cmc_id']:r for r in csv.DictReader(open('03_data/phase1/asset_onchain_identity.csv',encoding='utf-8'))}

os.makedirs('03_data/raw/cmc_detail',exist_ok=True)
def cmc_detail(cid):
    cache=f'03_data/raw/cmc_detail/{cid}.json'
    if os.path.exists(cache):
        try: return json.load(open(cache))
        except Exception: pass
    url=f'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?id={cid}'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                d=json.load(r); json.dump(d,open(cache,'w')); return d
        except Exception: time.sleep(1.0)
    return None

def idmap_pair(cid):
    m=idm.get(cid)
    if not m: return []
    raw=(m.get('token_address') or '').strip()
    if not raw: return []
    chain=(m.get('token_chain') or '').strip()
    if ':' in raw:
        pre,a=raw.split(':',1)
        return [(pre,a)]
    if re.fullmatch(r'0x[0-9a-fA-F]{40}',raw):
        # bare 0x: identity-map chain or assume ethereum if Multi-Chain/blank
        return [(chain or 'ethereum', raw)]
    return [(chain,raw)]

rows=[]
for i,a in enumerate(audit):
    cid=a['cmc_id']; sym=a['symbol']; name=a['name']
    cands=[]  # (chainname, address)
    cands+=idmap_pair(cid)
    d=cmc_detail(cid); time.sleep(0.18)
    plats=[]
    if d:
        data=d.get('data') or {}
        pl=data.get('platforms')
        if isinstance(pl,list):
            for p in pl:
                pn=p.get('contractPlatform') or p.get('platform') or ''
                ad=p.get('contractAddress') or p.get('address') or ''
                if ad: cands.append((pn,ad)); plats.append(f'{pn}:{ad}')
    # pick best EVM-reachable
    picked=(None,None,None)
    scored=[]
    for cn,ad in cands:
        # normalize 'ethereum:0x..' style prefixes already split; map name
        chid=to_chainid(cn)
        if chid and re.fullmatch(r'0x[0-9a-fA-F]{40}',ad.strip()):
            scored.append((PRIORITY.index(chid) if chid in PRIORITY else 99, chid, ad.strip()))
    if scored:
        scored.sort()
        _,chid,ad=scored[0]
        picked=(chid,ad,True)
    rows.append({'cmc_id':cid,'symbol':sym,'name':name,
                 'picked_chainid':picked[0] or '','picked_address':picked[1] or '',
                 'reachable':bool(picked[0]),
                 'n_platforms':len(plats),'platforms':' | '.join(plats)[:300]})
    if (i+1)%50==0: print(f'  ...{i+1}/{len(audit)} resolved')

with open('04_code/_etherscan_reach_resolve.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

reach=[r for r in rows if r['reachable']]
from collections import Counter
print(f"\nTOTAL bucket tokens: {len(rows)}")
print(f"Etherscan-V2-reachable (EVM address resolved): {len(reach)}")
print("by chainid:")
for k,v in Counter(r['picked_chainid'] for r in reach).most_common():
    print(f"   chainid {k}: {v}")
print("saved 04_code/_etherscan_reach_resolve.csv")
