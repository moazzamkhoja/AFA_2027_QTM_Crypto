import json,urllib.request,urllib.parse,time,os
KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
def es(params):
    params={**params,'apikey':KEY}
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=60) as r: return json.load(r)
        except Exception: time.sleep(1.5)
    return None

OUT='04_code/_contract_src'
os.makedirs(OUT,exist_ok=True)
TARGETS={
 'HEX':'0x2b591e99afe9f32eaa6214f7b7629768c40eeb39',
 'NMR':'0x1776e1f26f98b1a5df9cd347953a26dd3cb46671',
 'CORE':'0x62359ed7505efc61ff1d56fef82158ccaffa23d7',
 'AST':'0x27054b13b1b798b345b591a4d22e6562d47ea75a',
}
for sym,addr in TARGETS.items():
    d=es({'chainid':1,'module':'contract','action':'getsourcecode','address':addr})
    time.sleep(0.25)
    res=d['result'][0]
    src=res.get('SourceCode','')
    cname=res.get('ContractName','')
    # source may be: plain solidity, OR {{...}} standard-json, OR {...}
    files={}
    s=src.strip()
    if s.startswith('{'):
        if s.startswith('{{'): s=s[1:-1]   # strip doubled braces
        try:
            j=json.loads(s)
            srcs=j.get('sources',j)
            for path,obj in srcs.items():
                files[path]= obj.get('content',obj) if isinstance(obj,dict) else obj
        except Exception as e:
            files[cname+'.sol']=src
    else:
        files[cname+'.sol']=src
    # write concatenated, with separators
    big=[]
    for path,content in files.items():
        big.append("// ============ FILE: %s ============\n%s"%(path,content))
    open(os.path.join(OUT,f'{sym}.sol'),'w',encoding='utf-8').write("\n\n".join(big))
    print(f"{sym}: ContractName={cname}  files={len(files)}  bytes={sum(len(c) for c in files.values())}")
print("written to",OUT)
