import csv,json,re,urllib.request,urllib.parse,time,os

KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
audit={r['cmc_id']:r for r in csv.DictReader(open('03_data/phase1/token_bucket1_full_audit.csv',encoding='utf-8'))}
idm={r['cmc_id']:r for r in csv.DictReader(open('03_data/phase1/asset_onchain_identity.csv',encoding='utf-8'))}

def eth_addr(raw):
    raw=raw.strip()
    if not raw: return None
    if raw.startswith('ethereum:'): raw=raw.split(':',1)[1]
    if re.fullmatch(r'0x[0-9a-fA-F]{40}', raw): return raw
    return None

targets=[]
for cid,a in audit.items():
    m=idm.get(cid)
    if not m: continue
    chain=m['token_chain'].strip()
    addr=eth_addr(m['token_address'])
    if addr and chain in ('Ethereum','Multi-Chain',''):
        targets.append((cid,a['symbol'],a['name'],addr))

print("Ethereum-mainnet readable bucket tokens: %d\n"%len(targets))

def es(params):
    params={**params,'apikey':KEY}
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(1.5)
    return None

KW={'stake':'STAKE','unstake':'STAKE','staked':'STAKE','lock':'LOCK','locked':'LOCK',
    'escrow':'ESCROW','deposit':'DEPOSIT','withdraw':'WITHDRAW','vote':'VOTE',
    'delegate':'DELEGATE','checkpoint':'VOTES','getvotes':'VOTES'}

results=[]
for cid,sym,name,addr in targets:
    d=es({'chainid':1,'module':'contract','action':'getsourcecode','address':addr})
    time.sleep(0.22)
    row={'cid':cid,'sym':sym,'name':name,'addr':addr,'verified':False,'cname':'','evts':[],'funcs':[],'tags':[]}
    tags=set()
    if d and d.get('status')=='1' and d['result']:
        res=d['result'][0]
        row['cname']=res.get('ContractName','')
        abi_raw=res.get('ABI','')
        if abi_raw and abi_raw!='Contract source code not verified':
            row['verified']=True
            try:
                abi=json.loads(abi_raw)
                for it in abi:
                    nm=it.get('name','') or ''
                    low=nm.lower()
                    for k,tag in KW.items():
                        if k in low: tags.add(tag)
                    if it.get('type')=='event': row['evts'].append(nm)
                    elif it.get('type')=='function': row['funcs'].append(nm)
            except Exception:
                row['cname']+=' (ABI parse err)'
    row['tags']=sorted(tags)
    results.append(row)
    print("%-9s %-10s %-28s mech:[%s]  evts=%d funcs=%d"%(
        sym,('OK' if row['verified'] else 'UNVERIFIED'),row['cname'][:28],
        ','.join(row['tags']) or '-',len(row['evts']),len(row['funcs'])))

json.dump(results, open('04_code/_scratch_abi_scan.json','w'))
print("\nsaved 04_code/_scratch_abi_scan.json")
