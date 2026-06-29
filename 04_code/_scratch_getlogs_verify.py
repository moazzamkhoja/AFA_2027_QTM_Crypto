import json,urllib.request,urllib.parse,time
KEY=json.load(open('04_code/.api_keys.json'))['etherscan']
def es(params):
    params={**params,'apikey':KEY}
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for _ in range(4):
        try:
            with urllib.request.urlopen(url,timeout=40) as r: return json.load(r)
        except Exception: time.sleep(1.5)
    return None

# Known event topic0 hashes (keccak256 of signature)
TOP={
 '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':'Transfer(addr,addr,uint256)',
 '0xdec2bacdd2f05b59de34da9b523dff8be42e5e38e818c82fdb0bae774387a724':'DelegateVotesChanged(addr,uint256,uint256)',
 '0x3134e8a2e6d97e929a7e54011ea5485d7d196dd5f0ba4d4ef95803e8e3fc257f':'DelegateChanged(addr,addr,addr)',
}

def block_at(ts):
    d=es({'chainid':1,'module':'block','action':'getblocknobytime','timestamp':ts,'closest':'before'})
    return int(d['result']) if d and d.get('status')=='1' else None

def topic_hist(addr,frm,to,label):
    # address-only getLogs over a window: shows which events fire & are queryable
    d=es({'chainid':1,'module':'logs','action':'getLogs','address':addr,'fromBlock':frm,'toBlock':to})
    if not d or d.get('status')!='1':
        print(f"  {label}: getLogs -> {d.get('message') if d else 'no resp'} (result count 0 or capped)")
        return
    logs=d['result']
    from collections import Counter
    c=Counter(l['topics'][0] for l in logs if l['topics'])
    print(f"  {label}: {len(logs)} logs in window [{frm}..{to}]; distinct event topics:")
    for t,n in c.most_common(8):
        print(f"     {n:5d}  {TOP.get(t, t[:18]+'...')}")

# windows
b_2020_06=block_at(1593561600)  # 2020-07-01-ish HEX active
b_2020_07=block_at(1596240000)
b_2017_07=block_at(1499040000)  # NMR launched mid-2017
b_2017_09=block_at(1504224000)
b_2021_03=block_at(1614556800)  # CORE/SUPER ERC20Votes era
b_2021_04=block_at(1617235200)

print("HEX (built-in staking) — expect StakeStart/StakeEnd topics present:")
topic_hist('0x2b591e99afe9f32eaa6214f7b7629768c40eeb39',b_2020_06,b_2020_07,'HEX 2020-07')

print("\nNMR (NumeraireBackend staking) — expect Staked/StakeReleased topics:")
topic_hist('0x1776e1f26f98b1a5df9cd347953a26dd3cb46671',b_2017_07,b_2017_09,'NMR 2017-Q3')

print("\nCORE (ERC20Votes) — expect DelegateVotesChanged/DelegateChanged + Transfer:")
topic_hist('0x62359ed7505efc61ff1d56fef82158ccaffa23d7',b_2021_03,b_2021_04,'CORE 2021-03')
