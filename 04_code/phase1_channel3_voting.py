"""
phase1_channel3_voting.py  --  Phase 1, Channel 3 (voting engagement)

Canonical source: Snapshot's GraphQL API (hub.snapshot.org/graphql) -- the actual
store of off-chain DAO votes (gasless signed messages), not an aggregator. Verified
free/keyless (Entry 21). On-chain-only DAOs (Compound Governor, Maker) that don't use
Snapshot are a documented gap.

Space map (Entry 25): cmc_id -> Snapshot space, built as the union of
  (a) DeFiLlama `governanceID` snapshot spaces carried in the identity map (35), and
  (b) a curated, name-verified set of major governance DAOs with EXPLICIT cmc_ids
      (27) -- explicit ids avoid the symbol-collision trap (e.g. UNI is cmc_id 7083,
      not the symbol-matched 4113).
Written to 03_data/phase1/snapshot_space_map.csv for audit.

Metric (spec 3.3): monthly token-weighted turnout = mean(scores_total) / eligible
supply, where eligible supply = circulating supply from the Phase 0 panel (joined on
cmc_id + month_end). A proposal is attributed to the month its voting period ENDS.
We also record mean unique voter addresses per proposal as a diagnostic. CAVEAT: a few
spaces use non-token-balance strategies (quadratic / 1-person-1-vote) so scores_total
is not in token units there; flagged with `strategy_note`, kept for the z-scored
cross-section, audited via the raw per-space cache.

Output: 03_data/phase1/snapshot_space_map.csv
        03_data/phase1/channel3_voting.csv
        03_data/raw/phase1_onchain/snapshot/<space>.json  (cached raw proposals)
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IDENT = REPO / "03_data" / "phase1" / "asset_onchain_identity.csv"
PANEL = REPO / "03_data" / "universe_panel.csv"
MAP_OUT = REPO / "03_data" / "phase1" / "snapshot_space_map.csv"
OUT = REPO / "03_data" / "phase1" / "channel3_voting.csv"
CACHE = REPO / "03_data" / "raw" / "phase1_onchain" / "snapshot"
GQL = "https://hub.snapshot.org/graphql"
H = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

CURATED = {
    7083: "uniswapgovernance.eth", 7278: "aavedao.eth", 5692: "comp-vote.eth",
    6538: "curve.eth", 6758: "sushigov.eth", 5728: "balancer.eth", 5864: "veyfi.eth",
    2586: "snxgov.eth", 9903: "cvx.eth", 6953: "frax.eth", 28324: "dydxgov.eth",
    11857: "gmx.eth", 2943: "rocketpool-dao.eth", 12999: "mainnet.ssvnetwork.eth",
    8613: "alchemixstakers.eth", 1727: "bancornetwork.eth", 9067: "olympusdao.eth",
    11841: "arbitrumfoundation.eth", 11840: "opcollective.eth", 6719: "graphprotocol.eth",
    18934: "stgdao.eth", 11396: "joegovernance.eth", 13855: "ens.eth",
    8000: "lido-snapshot.eth", 10052: "gitcoindao.eth", 18876: "apecoin.eth",
    8104: "1inch.eth",
}


def build_space_map():
    ident = pd.read_csv(IDENT)
    rows = {}
    # (a) DeFiLlama-sourced spaces
    for _, r in ident[ident["has_snapshot"] == True].iterrows():  # noqa: E712
        rows[int(r["cmc_id"])] = {
            "cmc_id": int(r["cmc_id"]), "symbol": r["symbol"], "name": r["name"],
            "asset_class": r["asset_class"], "snapshot_space": r["snapshot_space"],
            "map_source": "defillama_governanceID",
        }
    # (b) curated (overrides/extends; explicit cmc_id)
    meta = ident.set_index("cmc_id")
    for cid, space in CURATED.items():
        sym = meta.loc[cid, "symbol"] if cid in meta.index else ""
        nm = meta.loc[cid, "name"] if cid in meta.index else ""
        cl = meta.loc[cid, "asset_class"] if cid in meta.index else ""
        if cid in rows and rows[cid]["snapshot_space"] == space:
            rows[cid]["map_source"] = "both"
        else:
            rows[cid] = {"cmc_id": cid, "symbol": sym, "name": nm, "asset_class": cl,
                         "snapshot_space": space, "map_source": "curated"}
    m = pd.DataFrame(list(rows.values())).sort_values("cmc_id")
    MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(MAP_OUT, index=False)
    print(f"space map: {len(m)} (cmc_id -> space); wrote {MAP_OUT}")
    return m


def fetch_proposals(space):
    """Page ALL closed proposals for a space (created asc cursor). Cache raw."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / f"{space}.json"
    if cf.exists():
        return json.loads(cf.read_text())
    out, cursor = [], 0
    while True:
        q = {"query": (
            'query($s:String!,$c:Int!){proposals(first:500,'
            'where:{space:$s,created_gt:$c},orderBy:"created",orderDirection:asc){'
            'id created start end state votes scores_total scores_state type}}'),
            "variables": {"s": space, "c": cursor}}
        try:
            r = requests.post(GQL, headers=H, data=json.dumps(q), timeout=45)
            data = r.json().get("data", {})
            props = data.get("proposals") if data else None
        except Exception as e:
            print(f"    {space} error: {e}; retrying")
            time.sleep(2)
            continue
        if not props:
            break
        out.extend(props)
        cursor = props[-1]["created"]
        time.sleep(0.4)
        if len(props) < 500:
            break
    cf.write_text(json.dumps(out))
    return out


def main():
    smap = build_space_map()
    panel = pd.read_csv(PANEL)
    # circulating supply by (cmc_id, YYYY-MM)
    panel["ym"] = panel["month_end"].str[:7]
    circ = panel[panel.status == "observed"].set_index(["cmc_id", "ym"])["circulating_supply"].to_dict()
    monthend = panel.groupby(panel["month_end"].str[:7])["month_end"].first().to_dict()

    rows = []
    for _, sp in smap.iterrows():
        cid, space = int(sp["cmc_id"]), sp["snapshot_space"]
        props = fetch_proposals(space)
        closed = [p for p in props if p.get("end") and p["end"] > 0]
        # Token-weight validity guard: in a real token-balance space, average voting
        # power per voter (scores_total/votes) is large (thousands+ of tokens). A
        # 1-person-1-vote space (e.g. snxgov.eth) has scores_total == vote count, so
        # the ratio ~1. Flag spaces whose median power-per-voter < 10 as NOT
        # token-weighted and null their vw_turnout (it is not a real token turnout).
        ratios = [(p["scores_total"] / p["votes"]) for p in closed
                  if (p.get("votes") or 0) > 0 and (p.get("scores_total") or 0) > 0]
        token_weighted = True
        if ratios:
            ratios.sort()
            med = ratios[len(ratios) // 2]
            token_weighted = med >= 10
        # bucket by month of voting-period END
        by_month = {}
        for p in closed:
            ym = time.strftime("%Y-%m", time.gmtime(p["end"]))
            by_month.setdefault(ym, []).append(p)
        for ym, ps in by_month.items():
            votes = [p.get("votes") or 0 for p in ps]
            scores = [p.get("scores_total") or 0 for p in ps]
            c = circ.get((cid, ym))
            vw_mean = sum(scores) / len(scores) if scores else 0
            rows.append({
                "cmc_id": cid, "symbol": sp["symbol"], "month_end": monthend.get(ym, ym + "-28"),
                "ym": ym, "snapshot_space": space, "n_proposals": len(ps),
                "voters_mean": sum(votes) / len(votes) if votes else 0,
                "voters_total": sum(votes), "vw_mean": vw_mean,
                "circulating_supply": c,
                "vw_turnout": (vw_mean / c) if (c and token_weighted) else None,
                "token_weighted": token_weighted,
                "strategy_note": "" if token_weighted else "non-token-weighted space (1p1v/ticket); vw_turnout nulled",
            })
        print(f"  {space:30} props={len(closed):>5}  months={len(by_month)}  "
              f"token_weighted={token_weighted}")

    out = pd.DataFrame(rows).sort_values(["cmc_id", "ym"])
    out.to_csv(OUT, index=False)
    n_assets = out.cmc_id.nunique()
    n_withturn = out[out.vw_turnout.notna()].cmc_id.nunique()
    print(f"\nwrote {OUT}")
    print(f"  asset-months: {len(out)} | distinct assets: {n_assets} | with vw_turnout: {n_withturn}")
    print(f"  month range: {out.ym.min()} -> {out.ym.max()}")


if __name__ == "__main__":
    main()
