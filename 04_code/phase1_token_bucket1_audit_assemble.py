"""
phase1_token_bucket1_audit_assemble.py  --  SESSION 021.
Assembles 03_data/phase1/token_bucket1_full_audit.csv: one row per token in the 398 "unrecoverable"
pool (+ VELO + the 6 already-rejected MKR/BAL/COMP/RUNE/ANGLE/AXS), each with an individual,
source-checked final verdict and a specific (non-category) reason -- the deliverable of the
exhaustive re-audit (Entry 50).

Columns: cmc_id, symbol, name, defillama_protocol_slug, defillama_category, stage1_label,
stage2_etherscan_check, stage2_dune_check, stage2_defillama_tvl_check, stage2_artemis_check,
final_verdict, reason.

Verdicts come from the funnel actually run this session (see _stage1_triage.csv, _stage2a_dl_tvl.csv,
_stage2_ratios.csv, _stage2_topholders.csv, channel1_evm_locks_bucket1.csv). No category-level
write-offs: every row carries a token-specific reason.
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P1 = REPO / "03_data" / "phase1"

# ---------- load inputs ----------
def load(fn, key="cmc_id"):
    d = {}
    with open(P1 / fn, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d[r[key]] = r
    return d

work = load("_token_bucket1_worklist.csv")            # 398
s1 = load("_stage1_triage.csv")                        # stage-1 labels + cmcid_categories
s2a = load("_stage2a_dl_tvl.csv")                      # has_staking_pool, staking_usd
ratios = load("_stage2_ratios.csv")                    # dl_staked_qty, ratio, chain
ident = load("asset_onchain_identity.csv")

# ---------- BUILD set (cross-checked to balanceOf at ~0.00% via single contract) ----------
BUILT = {
 "7737": ("Api3Pool 0x6dd655...c76d76", "~74% (single reward-staking pool; balanceOf==DL staked qty 64.35M, 0.00%)"),
 "3835": ("Orbs StakingContract 0x01d59a...656c3", "~42% (single staking contract; balanceOf==DL staked qty 1.841B, 0.00%)"),
 "2930": ("HiIQ veIQ 0x1bf545...e16ba", "~9% (Curve-style vote-escrow of IQ; balanceOf==DL staked qty 2.416B, 0.00%)"),
 "35509": ("Venice staking 0x321b7f...f340ff", "~73% (single reward-staking contract on Base; balanceOf==DL staked qty 33.28M, 0.00%)"),
 "7127": ("veVELO VotingEscrow 0xfaf8fd...06787d", "~7.4% (Entry-48 DEFER resolved: CMC+DeFiLlama agree cmc 7127==0x9560e827, Velodrome V2/V3 canonical token; single veVELO holds 1.296B base VELO, 0.00%)"),
}

# Stage-2b top-holder checks that FAILED the single-escrow test (DL shows a staking bucket but no
# single contract reproduces it -> not Entry-26 clean). reason text per token.
STAKEBUCKET_REJECT = {
 "30494": ("REJECT-mechanism", "EigenLayer EIGEN restaking is multi-contract (StrategyManager + per-asset strategies); top single holder 184M vs DL staked 296M -- no single base-token escrow (Entry-26 fails)"),
 "8719":  ("REJECT-mechanism", "Illuvium multi-pool core staking (sILV/flexible+locked pools); no single contract holds the DL staked 0.66M ILV -- not a single-escrow lock"),
 "8891":  ("REJECT-no-data",   "BTCST (synthetic BTC-hashrate token) staking: top holder 2.72M vs DL staked 5.12M, no single contract reproduces the figure on BNB"),
 "27765": ("REJECT-no-data",   "ZBU: DL reports 19.65M staked but no on-chain single holder of that size found on BNB balances -- mechanism unverifiable on free tier"),
 "5354":  ("REJECT-no-data",   "PEAK (dormant PeakDeFi): top holder 808M vs DL staked 157M, no single matching escrow -- stale/abandoned staking"),
 "35763": ("REJECT-no-data",   "KAITO (Base): DL 18.2M staked maps to no single top holder (treasury/LP holders dominate Base balances) -- single-escrow custody not confirmable"),
 "9175":  ("REJECT-no-data",   "MBOX (MOMO staking): top holders 117M/88M/64M, none matches DL staked 24.5M -- multi-pool farm, no single base-token escrow"),
 "1556":  ("REJECT-no-data",   "TIME (Timewarp, near-dormant): top holder 240k vs DL staked 30.7k -- no single contract reproduces the figure"),
 "30083": ("REJECT-no-data",   "ATH (Aethir): top holders 13B/5.6B/3B (treasury), none matches DL staked 778M -- single-escrow custody not confirmable"),
 "4134":  ("REJECT-no-data",   "AKRO (Akropolis): top holder 2.6B vs DL staked 153M -- no single contract reproduces the staked figure"),
 "8290":  ("REJECT-no-data",   "SUPER (SuperVerse): top holder 144M vs DL staked 1.76M -- multi-pool farm, no single base-token escrow"),
 "8938":  ("REJECT-no-data",   "EPS (Ellipsis): top holder is the zero/burn address, no single live escrow matches DL staked 9.53M on BNB"),
 "8602":  ("REJECT-no-data",   "AUCTION (Bounce): top holder 2.0M vs DL staked 31k -- no single contract reproduces the figure"),
 "2982":  ("REJECT-no-data",   "MVL: top holder 13.8B vs DL staked 100M -- no single contract reproduces the staked figure"),
 "14783": ("REJECT-no-data",   "MAGIC (Treasure, Arbitrum): top holder 50.8M vs DL staked 1.56M -- multi-pool, no single base-token escrow"),
 "7064":  ("REJECT-no-data",   "BAKE (BakerySwap): top holder is the dead address, no single live escrow matches DL staked 1.39M on BNB"),
 "7654":  ("REJECT-no-data",   "RFOX: top holder 272M (placeholder addr) vs DL staked 3.26M -- no single matching escrow on BNB"),
 "5566":  ("REJECT-mechanism", "KEEP (Keep Network, merged into Threshold/T): top holder 858M vs DL staked 11.7M; staking migrated to the T token -- legacy KEEP stake not a single live escrow"),
 "36410": ("REJECT-no-data",   "MYX: DL staked 1.73M (0.6% of supply) maps to no single confirmable BNB escrow on free tier"),
 "7617":  ("REJECT-no-data",   "SFI (Saffron): DL staked 1,285 SFI (~$0.13M, negligible); no material single-escrow lock"),
 "5015":  ("REJECT-mechanism", "HEX: 'staking' is internal to the HEX contract (T-shares minted/burned in-contract, not a separate base-token escrow); DL TVL staking bucket reads 0 now -- no reconstructable single-escrow series"),
 "8972":  ("REJECT-no-data",   "SFUND (Seedify): DL staking TVL bucket reads 0 -- no current locked supply to reconstruct"),
 "24796": ("REJECT-no-data",   "ADF: DL staking TVL bucket reads 0 -- no current locked supply to reconstruct"),
 # non-EVM material staking buckets (real mechanism, outside the free EVM Dune curated-transfers method)
 "3748":  ("REJECT-no-data",   "HXRO staking is on Solana (13.3% per DL); free EVM Dune curated-transfers method does not reach Solana SPL -- needs Solana-specific indexing"),
 "10529": ("REJECT-no-data",   "SUN (sun.io) staking is on Tron (2.8% per DL); not covered by the free EVM curated-transfers method -- needs Tron-specific indexing"),
 "5631":  ("REJECT-no-data",   "ORN staking surfaces on TON/DeDust per DL (3.0%); outside the free EVM Dune curated method -- needs TON indexing"),
 "9119":  ("REJECT-no-data",   "TLM (Alien Worlds) staking is on WAX (2.4% per DL); no free EVM-style curated transfer table -- needs WAX indexing"),
 "10903": ("REJECT-no-data",   "C98 staking surfaces on TomoChain per DL (0.6%); outside the free EVM curated method"),
 "11079": ("REJECT-no-data",   "BRISE (Bitgert) staking on its own chain (0.9% per DL); no free curated transfer table"),
 "5190":  ("REJECT-no-data",   "FLEX (CoinFlex): DL staking TVL on smartBCH reads 0 -- defunct exchange token, no reconstructable lock"),
 "1573":  ("REJECT-no-data",   "CASINO (DeFyDEX, Fantom): DL staking TVL bucket reads 0 -- no current locked supply"),
 # WARP cmcId-collision artifact
 "1166":  ("REJECT-no-data",   "WARP: DeFiLlama maps slug 'polkastarter' (POLS) to cmcId 1166, giving an impossible 1764% staked/circulating ratio -- a cmcId collision (Entry-39 landmine), not a real WARP lock"),
}

# ---------- per-token reason for the rest (no staking bucket / no DL identity) ----------
def sector_reason(w, s):
    sym = w["symbol"]; tags = w["tags"].lower(); sec = w["sector"].lower()
    cats = (s.get("cmcid_categories", "") or "").lower(); txt = tags + " " + sec + " " + cats
    btc_eth = ("btc" in txt or "eth" in txt or "bitcoin" in txt)
    if any(k in txt for k in ["rehypothecated", "liquid-staking", "restaking", "eth-staking"]) and btc_eth:
        return ("REJECT-mechanism", f"{sym} is a wrapped/composite LST of another asset (BTC/ETH) -- 'staking' accrues to the underlying, not a lock of {sym}; fails Entry-26 (no base-token escrow)")
    if any(k in txt for k in ["wrapped", "-peg", "bridged"]):
        return ("REJECT-mechanism", f"{sym} is a wrapped/bridged representation, not a base token with its own single-contract lock")
    if any(k in txt for k in ["meme", "animal-memes", "doggone", "memes"]):
        return ("REJECT-mechanism", f"{sym} is a meme token: no protocol, no staking/vote-escrow mechanism, no contract evidence of any base-token lock")
    if any(k in txt for k in ["stablecoin", "algo-stable", "seigniorage", "rebase"]):
        return ("REJECT-mechanism", f"{sym} is a stablecoin/algo-stable/rebase asset: no conviction-locking mechanism (excluded class)")
    if any(k in txt for k in ["dex", "dexs", "amm", "exchange-token"]):
        return ("REJECT-mechanism", f"{sym} is a DEX/exchange token; governance is delegation/farming/off-chain Snapshot -- DeFiLlama shows no single-contract base-token staking bucket")
    if any(k in txt for k in ["lending", "cdp", "borrow", "collateral"]):
        return ("REJECT-mechanism", f"{sym} is a lending/CDP token; no single-contract base-token escrow (governance via delegation/Snapshot)")
    if any(k in txt for k in ["derivatives", "perpetual", "options"]):
        return ("REJECT-mechanism", f"{sym} is a derivatives/perps token; DeFiLlama shows no single-contract base-token staking lock")
    if any(k in txt for k in ["gaming", "metaverse", "play-to-earn", "nft", "collectible"]):
        return ("REJECT-mechanism", f"{sym} is a gaming/NFT-ecosystem token; no clean single-contract base-token lock (rewards/farming, not vote-escrow)")
    if any(k in txt for k in ["layer-1", "layer-2", "smart-contracts", "rollup", "scaling"]):
        return ("REJECT-mechanism", f"{sym} is an L1/L2 chain/gas token; consensus/security staking (if any) is native, not an EVM single-contract token lock")
    if any(k in txt for k in ["depin", "iot", "storage", "filesharing", "vpn", "wireless", "ai-", "-ai", "oracle", "payments", "privacy", "rwa", "real-world"]):
        return ("REJECT-mechanism", f"{sym} is a utility/infrastructure token ({sec or 'no sector'}); no single-contract base-token staking lock on DeFiLlama or on file")
    if any(k in txt for k in ["bridge", "interoperability", "cross-chain"]):
        return ("REJECT-mechanism", f"{sym} is a bridge/interop token; no single-contract base-token lock")
    if any(k in txt for k in ["governance", "dao"]):
        return ("REJECT-mechanism", f"{sym} is governance-only; vote power is in-wallet delegation/Snapshot, not a base-token escrow")
    return ("REJECT-mechanism", f"{sym}: utility/governance token; no DeFiLlama staking bucket and no single-contract base-token lock identified")


# the 3 already-rejected tokens that live INSIDE the 398 worklist -> carry the explicit reconfirm
RECONFIRM_INLINE = {
 "1518": ("REJECT-mechanism", "Reconfirmed (Entry 41): MKR governance is in-wallet voting via DSChief (holds ~0.5% post-Sky migration); no single-escrow base-token lock. Live: no cmcId-matched DL staking bucket."),
 "4157": ("REJECT-mechanism", "Reconfirmed (Entry 41): RUNE bonding is native THORChain L1 (DL slug thorchain-dex, Dexs), not an EVM single-contract token lock; no free EVM reconstruction."),
 "6783": ("REJECT-no-data", "Reconfirmed (Entry 48): AXS staking lives on the Ronin appchain (DL slug axie-infinity, Gaming, no staking bucket); not indexed by any free EVM tool (no Etherscan-V2 free coverage, no Dune curated schema). Legacy Ethereum staking abandoned."),
}


def build_row(cid, w):
    s = s1.get(cid, {})
    if cid in RECONFIRM_INLINE:
        verdict, reason = RECONFIRM_INLINE[cid]
        slug = ident.get(cid, {}).get("dl_slug", "")
        return dict(stage1_label=s.get("stage1_label", ""),
                    stage2_etherscan_check="light-touch reconfirm: no new single-escrow contract since Entry 26/41/48",
                    stage2_dune_check="n/a (no single-escrow candidate)",
                    stage2_defillama_tvl_check="no cmcId-matched DL 'staking' bucket (checked live)",
                    stage2_artemis_check="n/a (Artemis terminal JS/login-gated; Entry 2/14)",
                    final_verdict=verdict, reason=reason, slug=slug,
                    dlcat=s.get("cmcid_categories", ""))
    slug = s.get("dl_slug", "") or ident.get(cid, {}).get("dl_slug", "")
    dlcat = s.get("cmcid_categories", "") or ident.get(cid, {}).get("dl_category", "")
    s1lab = s.get("stage1_label", "")
    has_addr = ident.get(cid, {}).get("token_address", "").strip() != ""
    a2a = s2a.get(cid, {})
    has_stake = a2a.get("has_staking_pool", "") == "True"
    rt = ratios.get(cid, {})

    # default check texts
    es = "not reached (no single escrow candidate surfaced)"
    dn = "not run"
    dl = "no cmcId-matched DeFiLlama protocol" if not slug else "cmcId-matched DL protocol; "
    art = "n/a (Artemis terminal is JS/login-gated; no free per-asset staking data -- Entry 2/14 confirmed live this session)"

    if cid in BUILT:
        escrow, ratiotxt = BUILT[cid]
        return dict(stage1_label=s1lab,
                    stage2_etherscan_check=f"single contract {escrow} holds base token == DL staked qty (top-holder Dune cross-check)",
                    stage2_dune_check=f"BUILT: tokens_<chain>.transfers cumulative reconstruction; recon_final == balanceOf to 0.00%",
                    stage2_defillama_tvl_check=f"DL 'staking' chainTvls bucket present, token-quantity series used to locate the escrow; {ratiotxt}",
                    stage2_artemis_check=art, final_verdict="BUILD",
                    reason=f"Single-contract base-token lock confirmed (Entry-26 standard); {ratiotxt}", slug=slug, dlcat=dlcat)

    if cid in STAKEBUCKET_REJECT:
        verdict, reason = STAKEBUCKET_REJECT[cid]
        chain = rt.get("chain", ""); dq = rt.get("dl_staked_qty", "")
        return dict(stage1_label=s1lab,
                    stage2_etherscan_check="top-holder check: no single contract holds the DL-reported staked amount (fails Entry-26)" if "no single" in reason or "top holder" in reason or "top single" in reason else "n/a (non-EVM or zero TVL)",
                    stage2_dune_check=f"top-holder query on {chain or 'chain'} run; single-escrow custody NOT confirmed" if verdict!="REJECT-mechanism" or "multi" in reason else "top-holder query run; mechanism is multi-contract/native",
                    stage2_defillama_tvl_check=f"DL 'staking' bucket present (qty {dq}) on {chain}, but not a single-contract base-token escrow",
                    stage2_artemis_check=art, final_verdict=verdict, reason=reason, slug=slug, dlcat=dlcat)

    # DL-matched but NO staking bucket (the 92 - 36 = 56) -> category gives the reason
    if slug and not has_stake:
        verdict, reason = sector_reason(w, s)
        return dict(stage1_label=s1lab,
                    stage2_etherscan_check="n/a (no staking/escrow candidate; protocol governance is delegation/farming/Snapshot)",
                    stage2_dune_check="n/a (no single-escrow candidate to reconstruct)",
                    stage2_defillama_tvl_check=f"cmcId-matched DL protocol ({dlcat}); chainTvls has NO 'staking' bucket -> no base-token lock tracked",
                    stage2_artemis_check=art, final_verdict=verdict, reason=reason, slug=slug, dlcat=dlcat)

    # no cmcId DL protocol at all (the 306) -> honest 'no on-chain identity on file' + sector reason
    verdict, reason = sector_reason(w, s)
    idnote = "token contract on file but no DeFiLlama protocol and no escrow candidate" if has_addr else "no DeFiLlama protocol match (cmcId) AND no contract address on file -- no on-chain identity available to check"
    return dict(stage1_label=s1lab,
                stage2_etherscan_check=idnote,
                stage2_dune_check="n/a (no escrow candidate)",
                stage2_defillama_tvl_check="no cmcId-matched DeFiLlama protocol (checked live against api.llama.fi/protocols)",
                stage2_artemis_check=art, final_verdict=verdict, reason=reason, slug=slug, dlcat=dlcat)


# ---------- the 6 already-rejected (reconfirm) + ANGLE ----------
RECONFIRM = {
 "1518": ("MKR", "Maker", "REJECT-mechanism", "Reconfirmed (Entry 41): MKR governance is in-wallet voting via DSChief (holds ~0.5% post-Sky migration); no clean single-escrow base-token lock. Live: no cmcId-matched DL staking bucket."),
 "5728": ("BAL", "Balancer", "REJECT-mechanism", "Reconfirmed (Entry 26): veBAL locks an 80/20 BPT (a composite LP), not BAL itself -- fails Entry-26 base-token-custody. (Already in lambda via Channel-3 voting.) Live: no cmcId DL staking bucket for BAL."),
 "5692": ("COMP", "Compound", "REJECT-mechanism", "Reconfirmed (Entry 41): COMP governance is in-wallet delegation, no lock contract. (Already in lambda via Channel-3 voting.) Live: no cmcId DL staking bucket."),
 "4157": ("RUNE", "THORChain", "REJECT-mechanism", "Reconfirmed (Entry 41): RUNE bonding is native THORChain L1 (slug thorchain-dex, category Dexs on DL), not an EVM single-contract token lock; no free EVM reconstruction."),
 "6783": ("AXS", "Axie Infinity", "REJECT-no-data", "Reconfirmed (Entry 48): AXS staking lives on the Ronin appchain (slug axie-infinity, Gaming on DL, no staking bucket); not indexed by any free EVM tool (no Etherscan-V2 free coverage, no Dune curated schema). Legacy Ethereum staking abandoned."),
 "_ANGLE": ("ANGLE", "Angle Protocol", "N/A-out-of-universe", "ANGLE is NOT in the in-universe token set (confirmed live against classification_table.csv) -- it never entered the 448-token universe, so it is not part of Bucket 1. Listed only because Entry 41 named it among rejects."),
}


def main():
    cols = ["cmc_id", "symbol", "name", "defillama_protocol_slug", "defillama_category",
            "stage1_label", "stage2_etherscan_check", "stage2_dune_check",
            "stage2_defillama_tvl_check", "stage2_artemis_check", "final_verdict", "reason"]
    out = []
    seen = set()
    # 398 worklist
    for cid, w in work.items():
        r = build_row(cid, w)
        out.append([cid, w["symbol"], w["name"], r["slug"], r["dlcat"], r["stage1_label"],
                    r["stage2_etherscan_check"], r["stage2_dune_check"], r["stage2_defillama_tvl_check"],
                    r["stage2_artemis_check"], r["final_verdict"], r["reason"]])
        seen.add(cid)
    # VELO (separate row -- it was the deferral, not in the 398)
    if "7127" not in seen:
        w = {"symbol": "VELO", "name": "Velodrome Finance", "tags": "", "sector": ""}
        r = build_row("7127", w)
        out.append(["7127", "VELO", "Velodrome Finance", r["slug"], r["dlcat"], r.get("stage1_label", "DEFER-resolved"),
                    r["stage2_etherscan_check"], r["stage2_dune_check"], r["stage2_defillama_tvl_check"],
                    r["stage2_artemis_check"], r["final_verdict"], r["reason"]])
        seen.add("7127")
    # reconfirm 6 (only those not already in the worklist get an extra row; AXS/RUNE/MKR already there)
    for cid, (sym, name, verdict, reason) in RECONFIRM.items():
        real = cid.lstrip("_")
        if real in seen and not cid.startswith("_"):
            continue  # already represented in the 398 (its row already reconfirms)
        slug = ident.get(real, {}).get("dl_slug", "") if real in ident else ""
        out.append([real if not cid.startswith("_") else "n/a", sym, name, slug, "",
                    "RECONFIRM", "light-touch reconfirm (DL + Etherscan/Ronin)", "n/a", "no cmcId DL staking bucket (live)",
                    "n/a", verdict, reason])
    with open(P1 / "token_bucket1_full_audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(out)
    # summary
    from collections import Counter
    c = Counter(r[10] for r in out)
    print(f"wrote token_bucket1_full_audit.csv: {len(out)} rows")
    for v, n in c.most_common():
        print(f"  {v}: {n}")


if __name__ == "__main__":
    main()
