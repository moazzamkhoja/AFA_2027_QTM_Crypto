"""
classify_confirmation_pass.py  --  Phase 0 follow-up, deliverable 2
Implements DATA_DECISIONS_LOG.md Entry 11 (+ confirms Entry 12 meme/NFT handling).

Scope (Entry 11): assets that are asset_class=='other' AND ambiguous_flag==True in
03_data/classification_table.csv AND have >=12 OBSERVED asset-months in
universe_panel.csv (carried_forward months excluded from that count -- they are not
real observations of the asset's behaviour). ~630 names.

For each, a proposal is recorded: keep 'other', reclassify 'coin', or reclassify
'token', with a one-line rationale. The overwhelming majority are genuine
utility/sector tokens (AI, gaming, payments, DePIN, storage, identity, exchange,
meme) that are correctly 'other'. A small, individually-verified set of native-chain
coins and DeFi governance tokens that the first-pass tag rules missed are flipped;
a documented gray-zone set is left 'other' with an explicit "ambiguous" note rather
than forced into a label (per the spec's instruction not to invent classifications).

Outputs:
  03_data/classification_confirmation_review.csv  -- all candidates + proposal/rationale
  updates 03_data/classification_table.csv         -- applies the confident flips:
        adds `asset_class_original` (preserves the pre-confirmation label),
        adds `confirmation_basis`, updates `asset_class`, clears ambiguous_flag on flips.
Idempotent: re-running only re-applies the listed overrides; asset_class_original is
preserved on first run and not overwritten.
"""

from pathlib import Path
import io
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "03_data"
MIN_OBS = 12

# --- Manual reclassifications (other -> coin/token), each publicly verifiable. -----
# Keyed by cmc_id (verified against the candidate dump). Rationale is one line.
# COIN = native chain asset with a security/seigniorage staking-or-mining benefit
#        (b_t>0, H1a). The first pass missed these because their CMC tags carried
#        'platform'/ecosystem labels (or a non-standard consensus tag), or because a
#        DeFiLlama category mislabelled the base chain.
RECLASS = {
    # other -> coin (native PoS/DPoS/mineable chain, validators/stakers earn rewards)
    5034:  ("coin",  "Kusama: Polkadot canary-net L1, NPoS; validators/nominators stake KSM for chain security+rewards (DeFiLlama 'Liquid Staking' is a mislabel)."),
    28321: ("coin",  "Polygon (POL): native gas+staking token of Polygon PoS; validators stake POL to secure the chain (DeFiLlama 'Chain')."),
    28932: ("coin",  "Dymension (DYM): Cosmos-SDK L1 RollApp settlement chain; DYM bonded by validators for PoS security."),
    15185: ("coin",  "Kujira (KUJI): sovereign Cosmos L1; KUJI staked by validators for chain security (DeFiLlama 'Liquidations' tags its apps, not the chain)."),
    8677:  ("coin",  "Symbol (XYM): native coin of the Symbol chain; PoS+ ('posplus') harvesting rewards (consensus tag the first-pass exact-set missed)."),
    2405:  ("coin",  "IOST: native coin of the IOST L1 (Proof-of-Believability); staked for block-production rewards."),
    1230:  ("coin",  "Steem (STEEM): native coin of the Steem DPoS chain; staked as Steem Power, witnesses/producers earn issuance."),
    1320:  ("coin",  "Ardor (ARDR): native coin of the Ardor PoS chain (Nxt successor); forging rewards."),
    2840:  ("coin",  "QuarkChain (QKC): native coin of the QuarkChain sharded L1; staked/mined block rewards."),
    4747:  ("coin",  "Velas (VLX): native coin of the Velas L1 (AIDPoS); staked for chain security."),
    2346:  ("coin",  "WaykiChain (WICC): native coin of the WaykiChain DPoS L1."),
    1955:  ("coin",  "Neblio (NEBL): native coin of the Neblio PoS chain; staking rewards."),
    4189:  ("coin",  "Ultra (UOS): native coin of the Ultra L1 (EOSIO/DPoS)."),
    2585:  ("coin",  "CENNZnet (CENNZ): native coin of the CENNZnet L1; staking for security."),
    1925:  ("coin",  "Waltonchain (WTC): native coin of the Waltonchain L1 (Proof-of-Stake-and-Trust)."),
    # other -> token (DeFi protocol governance token w/ vote-escrow fee-share, b_t=0, H1b)
    18934: ("token", "Stargate Finance (STG): LayerZero bridge protocol; veSTG vote-escrow with protocol fee-share + governance (bridge category the first pass didn't promote)."),
}

# --- Gray zone: left 'other' deliberately, with an explicit ambiguity note. --------
# These have a plausible coin OR token reading but no clean, defensible mechanism;
# per the spec we leave them 'other' rather than force a label. Revisit in Phase 1.
GRAY = {
    11840: "Optimism (OP): L2 governance token -- no security-staking (not coin), governance-only without a vote-escrow fee-share lock (not a clean token). Ambiguous; left other.",
    27075: "Mantle (MNT): L2 gas+governance token; same coin/token ambiguity as OP. Left other.",
    13631: "Manta (MANTA): hybrid L1(Atlantic)/L2(Pacific); staking on one side, rollup gas on the other. Ambiguous; left other.",
    10603: "Immutable (IMX): zkEVM L2 token; staking exists but security leans on Ethereum. Ambiguous; left other.",
    2943:  "Rocket Pool (RPL): liquid-staking protocol governance/collateral token; left other per Entry 8 (LST sector kept out of the coin/token cut).",
    3783:  "Ankr (ANKR): DePIN/RPC + liquid-staking utility/governance token; ambiguous, left other.",
    12999: "ssv.network (SSV): distributed-validator staking infrastructure; fee/governance token, not chain security itself. Ambiguous; left other.",
    21781: "Stride (STRD): Cosmos liquid-staking appchain; native-staking-coin vs LST-protocol-token identity unresolved (Entry 8). Left other.",
    5268:  "Energy Web (EWT): own chain but Proof-of-Authority; weak/empty seigniorage benefit. Ambiguous; left other.",
    1492:  "Obyte (GBYTE): native DAG coin but historically no staking rewards (b_t ~ 0). Ambiguous; left other.",
    1087:  "Factom (FCT): data-anchoring credit/entry-credit model, no clean staking-for-security reward. Ambiguous; left other.",
    23121: "Blur (BLUR): NFT-marketplace governance/incentive token; NFT-sector gray zone, left other.",
    17081: "LooksRare (LOOKS): NFT-marketplace token; NFT-sector gray zone, left other.",
    32197: "Magic Eden (ME): NFT-marketplace token; NFT-sector gray zone, left other.",
    3581:  "Kleros (PNK): jurors stake PNK for case selection + fees (a work/fee-share token) -- borderline token; left other pending review.",
    62:    "BitShares PTS (PTS): likely the mineable ProtoShares predecessor (=> coin), but symbol-collision + obscurity make it low-confidence. Left other.",
}

# Tag keywords -> short sector label, used to auto-generate the 'keep other' rationale
# (priority order: first match wins).
SECTOR_HINTS = [
    ("memes", "meme token"), ("animal-memes", "meme token"), ("cat-themed", "meme token"),
    ("doggone-doggerel", "meme token"), ("ai-memes", "meme token"), ("celebrity-memes", "meme token"),
    ("centralized-exchange", "exchange/discount token"), ("discount-token", "exchange/discount token"),
    ("wrapped-tokens", "wrapped/tokenized asset"), ("tokenized-assets", "wrapped/tokenized asset"),
    ("liquid-staking-derivatives", "liquid-staking derivative (Entry 8: other)"),
    ("real-world-assets", "RWA/tokenized asset"), ("real-world-assets-protocols", "RWA/tokenized asset"),
    ("ai-agents", "AI/agent utility token"), ("ai-big-data", "AI/data utility token"),
    ("depin", "DePIN/infrastructure token"), ("distributed-computing", "DePIN/compute token"),
    ("storage", "storage/DePIN token"), ("filesharing", "storage/DePIN token"),
    ("gaming", "gaming/metaverse token"), ("metaverse", "gaming/metaverse token"),
    ("play-to-earn", "gaming/metaverse token"), ("collectibles-nfts", "NFT-ecosystem fungible token"),
    ("privacy", "privacy utility token"), ("oracle", "oracle utility token"),
    ("payments", "payments utility token"), ("medium-of-exchange", "payments utility token"),
    ("identity", "identity utility token"), ("iot", "IoT utility token"),
    ("prediction-markets", "prediction-market token"), ("telegram-bot", "trading-bot token"),
    ("content-creation", "media/social token"), ("communications-social-media", "media/social token"),
    ("enterprise-solutions", "enterprise/platform token"), ("platform", "platform utility token"),
    ("services", "services utility token"), ("marketplace", "marketplace utility token"),
]


def sector_rationale(tags, dl):
    tl = (str(tags) + ";" + str(dl)).lower()
    for kw, label in SECTOR_HINTS:
        if kw in tl:
            return f"keep other -- {label} (no security-staking benefit and no governance/fee-share lock)."
    return "keep other -- no coin (security-staking) or token (governance/fee-share) mechanism evident from tags/DeFiLlama."


def main():
    panel = pd.read_csv(DATA / "universe_panel.csv")
    obs = (panel[panel["status"] == "observed"].groupby("cmc_id").size()
           .rename("obs_months"))

    ct = pd.read_csv(DATA / "classification_table.csv")
    # preserve original class once
    if "asset_class_original" not in ct.columns:
        ct["asset_class_original"] = ct["asset_class"]
    if "confirmation_basis" not in ct.columns:
        ct["confirmation_basis"] = ""

    inu = ct[ct["in_universe"] == True].merge(obs, on="cmc_id", how="left")
    inu["obs_months"] = inu["obs_months"].fillna(0).astype(int)
    cand = inu[(inu["asset_class_original"] == "other") &
               (inu["ambiguous_flag"] == True) &
               (inu["obs_months"] >= MIN_OBS)].copy()

    rows = []
    for _, r in cand.iterrows():
        cid = int(r["cmc_id"])
        if cid in RECLASS:
            new_cls, rat = RECLASS[cid]
            rows.append((cid, r["symbol"], r["name"], r["obs_months"],
                         "other", new_cls, rat, True))
        elif cid in GRAY:
            rows.append((cid, r["symbol"], r["name"], r["obs_months"],
                         "other", "other", "GRAY ZONE -- " + GRAY[cid], False))
        else:
            rat = sector_rationale(r["tags"], r["defillama_categories"])
            rows.append((cid, r["symbol"], r["name"], r["obs_months"],
                         "other", "other", rat, False))

    review = pd.DataFrame(rows, columns=[
        "cmc_id", "symbol", "name", "obs_months", "current_class",
        "proposed_class", "rationale", "changed"]).sort_values(
        ["changed", "proposed_class", "obs_months"], ascending=[False, True, False])
    review.to_csv(DATA / "classification_confirmation_review.csv", index=False)

    # ---- apply the confident flips back to classification_table.csv ----
    for cid, (new_cls, rat) in RECLASS.items():
        m = ct["cmc_id"] == cid
        ct.loc[m, "asset_class"] = new_cls
        ct.loc[m, "ambiguous_flag"] = False
        ct.loc[m, "confirmation_basis"] = "Entry11 confirmation pass: " + rat
    # tag gray-zone rows with the note (class unchanged)
    for cid, note in GRAY.items():
        m = ct["cmc_id"] == cid
        ct.loc[m, "confirmation_basis"] = "Entry11 gray-zone (left other): " + note
    ct.to_csv(DATA / "classification_table.csv", index=False)

    # ---- summary ----
    buf = io.StringIO()
    w = lambda s="": buf.write(s + "\n")
    w("CLASSIFICATION CONFIRMATION PASS (deliverable 2, Entry 11)")
    w("=" * 60)
    w(f"Candidates reviewed (other & ambiguous & >={MIN_OBS} obs months): {len(cand)}")
    nflip = review["changed"].sum()
    w(f"Reclassified: {int(nflip)}  (coin: "
      f"{sum(1 for v in RECLASS.values() if v[0]=='coin')}, token: "
      f"{sum(1 for v in RECLASS.values() if v[0]=='token')})")
    w(f"Gray-zone, left 'other' with note: {len(GRAY)}")
    w(f"Kept 'other' (utility/sector tokens): {len(cand) - int(nflip) - len(GRAY)}")
    w("")
    w("Reclassifications (from -> to):")
    for _, r in review[review.changed].iterrows():
        w(f"  {r['symbol']:8s} {str(r['name'])[:26]:26s} other -> {r['proposed_class']:5s}"
          f"  | {r['rationale']}")
    diag = buf.getvalue()
    (DATA / "_classification_confirmation_summary.txt").write_text(diag, encoding="utf-8")
    print(diag)
    print(f"Wrote classification_confirmation_review.csv ({len(review)} rows) and "
          f"updated classification_table.csv.")


if __name__ == "__main__":
    main()
