# Claude Code Kickoff Prompt — Session 027: TVL Expansion + Channel-2 Tail (continued)

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`.

Context: Session 026 built the first 3-channel assets (332 asset-months across 9 tokens) and
completed OP delegation as a crosscheck. λ is now 6,021 asset-months / 282 assets. A fresh
universe coverage CSV (`03_data/universe_coverage_status.csv`) maps all 1,939 in-universe
assets with current data status and what's needed per asset. Two tasks this session, in priority
order: (A) TVL expansion, and (B) ch2 holding tail continued.

---

```
You're working in the AFA 2027 QTM Crypto research repo. λ is 6,021 asset-months / 282 assets
(session 026, Entry 67). Etherscan Pro key (200k calls/day, 10/s) is in `.api_keys.json` under
"etherscan". DeFiLlama API is free/keyless. Two tasks this session, in priority order.

## Required reading before starting

- 04_code/DATA_DECISIONS_LOG.md — read Entries 63–67 (ch2 methodology, TVL scope, session 026
  close). Continue from Entry 68.
- 03_data/SESSION026_TAIL_BUILD_REPORT.md — full session 026 account (read entirely)
- 03_data/universe_coverage_status.csv — NEW: coverage map for all 1,939 universe assets.
  Columns: cmc_id, symbol, name, asset_class, lambda_months, lambda_n_channels, lambda_channels,
  has_ch1, has_ch2, has_ch3_v, has_ch3_d, has_nvt_gl, has_tvl, holder_count, coverage_status,
  what_needed. Use this to drive priority ordering in both tasks.
- 03_data/phase1/asset_onchain_identity.csv — dl_slug column is the DeFiLlama protocol slug
- 04_code/phase2_build_tvl_panel.py — existing TVL panel builder (idempotent, cached per slug)
- 04_code/phase1_channel2_stream.py — streaming ch2 engine (session 026, validated)
- 03_data/phase1/lambda_panel.csv — current λ panel

## TASK A — TVL Expansion (Entry 68)

### Motivation
TVL is the denominator in the tokens' valuation multiple (NV/TVL). Five 3-channel assets
(CRV/YFI/FRAX/GMX/RPL) have full λ but no TVL — they cannot enter the regression without it.
76 more 1–2-channel tokens also have no TVL. TVL fetches are free (api.llama.fi, keyless),
cached per slug, and take <1s each — this is the highest-ROI task in the session.

### Step A1 — Slug discovery for priority tokens

Four of the five 3-channel tokens have NO dl_slug in asset_onchain_identity.csv:
- CRV (cmc_id 6538, Curve DAO Token)
- YFI (cmc_id 5864, Yearn Finance)
- FRAX (cmc_id 6953, Frax / prev. FXS)
- GMX (cmc_id 11857, GMX)

RPL (cmc_id 2943) already has dl_slug = "rocket-pool" → skip discovery, fetch directly.

For each of the four missing tokens:
a. Call `https://api.llama.fi/protocols` (returns the full DeFiLlama protocol list as JSON).
   Match by CMC ID first (field `cmcId`), then by name/symbol if CMC ID is absent or stale.
   The protocol list is ~2000 entries; cache it locally so you don't re-fetch per token.
b. Confirm the match is the right protocol (name + TVL series looks right — not a chain-level
   entry or an unrelated protocol with the same ticker).
c. Candidate slugs to expect: "curve-dex" or similar for CRV; "yearn-finance" for YFI;
   "frax" for FRAX; "gmx" for GMX. Verify against the list, do not assume.
d. Write the confirmed slug back into asset_onchain_identity.csv (cmc_id join only, never
   symbol; update dl_slug column, also update dl_matched=True if that column exists).
e. Log the slug decisions in DATA_DECISIONS_LOG (Entry 68), noting any slug that was
   ambiguous or could not be confirmed.

### Step A2 — TVL fetch for all lambda tokens with missing TVL

After confirming slugs for the 5 priority tokens, extend the fetch to ALL lambda assets
missing TVL that have a confirmed dl_slug:

From asset_onchain_identity.csv, collect all rows where:
  - cmc_id is in lambda_panel.csv (has_lambda)
  - dl_slug is not null
  - cmc_id NOT already in tvl_panel.csv (no need to re-fetch existing TVL rows)

The existing script `phase2_build_tvl_panel.py` already does this derivation. Read it
fully before running — the join logic uses IDENT (asset_onchain_identity.csv) to derive
the slug list. Run it; it will skip already-cached protocol JSONs and only fetch new ones.

Expected coverage gain: ~23 tokens immediately (have existing slugs), + 4 more if slugs
confirmed above. Report how many new token-TVL months were added.

### Step A3 — Slug discovery for the broader lambda-but-no-TVL list

After the priority tokens, attempt slug discovery for the remaining lambda assets without
TVL (about 200 tokens have no dl_slug and no TVL). Method:

a. For each token, try `https://api.llama.fi/protocols` matched by CMC ID (`cmcId` field).
   This is a BULK operation — fetch the protocol list ONCE, build a dict keyed by cmcId,
   then look up each token's cmc_id directly.
b. For hits: confirm the name/symbol match is correct (same spot-check as A1), write slug
   to asset_onchain_identity.csv, queue for TVL fetch.
c. For misses (cmcId not in DeFiLlama list): check if the token is a CHAIN-level protocol
   on DeFiLlama (i.e. the TVL is at chain level, not protocol level). If so, try
   `https://api.llama.fi/v2/chains` for the chain TVL series. This applies to:
     - Coin λ assets (ETH, SOL, TRX, ADA — their "TVL" is the chain's DeFi TVL, not a
       protocol). NOTE: for COINS we use NVT (not NV/TVL) per the framework, so chain TVL
       is NOT needed in the denominator — skip coins for TVL.
     - Governance tokens whose protocol TVL is tracked at chain level (e.g. ARB, OP).
d. Log total: how many new slugs confirmed, how many still unmatched, how many were coins
   (excluded from TVL requirement).

### A4 — Rebuild tvl_panel.csv

After all slug updates, re-run `phase2_build_tvl_panel.py` to build the updated TVL panel.
Report: old rows / new rows, distinct tokens before/after.

### A5 — Cross-check priority token TVL plausibility

For the 5 three-channel tokens (CRV, YFI, FRAX, GMX, RPL), spot-check the TVL series:
- Series should span at least 24 months
- No month should show TVL ≈ 0 for a major protocol except during genuine early-launch
- TVL should be in USD (not raw token units — the DeFiLlama API returns USD)
Report any anomalies; do NOT fold into panel if series looks wrong.

---

## TASK B — Channel-2 Tail continued (Entry 69)

### Motivation
43 assets in λ have ch1 OR ch3 but NO ch2. Adding ch2 upgrades them from 1-channel
to 2-channel (or 2-channel to 3-channel). All are EVM/Ethereum tokens with holder counts
≤500k and buildable via the session-026 streaming engine.

### Priority list (sorted smallest-first, build in this order)

Derived from universe_coverage_status.csv: cmc_id IN lambda_panel AND has_ch2=False AND
(has_ch1=True OR has_ch3_v=True) AND holder_count <= 500000.

Key tokens in approximate holder-count order:
- NFTX (8191, ~3.7k), HAKKA (6622, ~4k), IQ (2930, ~4.1k), BZRX (5810, ~5k)
- COW (19269, ~7k), MC (13523, ~7k), SSV (12999, ~7.4k), OHM (9067, ~8.4k)
- KP3R (7535, ~8.5k), ORBS (3835, ~9k), RGT (7486, ~9.4k), SYN (12147, ~10.4k)
- PNT (5794, ~10.8k), STRK-token (8911, ~11.9k), XAN (38481, ~13k)
- LQTY (7429, ~14.4k), ALCX (8613, ~14.5k), PERP (6950, ~14.6k)
- HFT (22461, ~16.2k), TRU (7725, ~16.2k), FARM (6859, ~16.2k)
- CAKE (7186, ~20.6k), GNS (13663, ~20.6k), LINA (7102, ~22.8k), API3 (7737, ~23.9k)
- MNT (27075, ~29.8k), BADGER (7859, ~30.3k), BNT (1727, ~38.5k), STG (18934, ~39.2k)
- BAL (5728, ~48.8k), REN (2539, ~59.6k)
- ARB (11841, ~63.9k), LDO (8000, ~65.5k), ENS (13855, ~67.6k)
- PENDLE (9481, ~72.8k), GTC (10052, ~89.6k), ENA (30171, ~97.8k)
- LRC (1934, ~167k), GRT (6719, ~173k), APE (18876, ~188k), ZRX (1896, ~190k)
- COMP (5692, ~220k), UNI (7083, ~385k)

Do NOT re-run tokens already completed in session 026. Load their checkpoints and skip.
Use `phase1_channel2_stream.py` (the streaming engine from session 026, NOT the old panel
engine). Do NOT attempt HEX (cmc_id 5015, 9M holders — permanently deferred, Entry 66).

### B1 — Run the tail smallest-first

Set HOLDER_MAX high enough to cover the full list (HOLDER_MAX=500000 or unlimited since
all targets are pre-screened here). Process in holder-count order. Monitor memory heartbeat
for any hidden giant (a token with low holder_count but unexpectedly large Transfer history
— like ORBS in session 026). If a token's est_getlogs_calls from `_channel2_sizes.csv`
exceeds 50k, log it and evaluate budget before proceeding.

Daily budget: DAILY_CAP = 200,000 getLogs calls. Stop and checkpoint before hitting the
cap (leave 20k headroom). All stops are clean because the streaming engine checkpoints
per-token.

### B2 — Address-poisoning two-layer guard (already in the engine)

The session-026 engine already has:
1. Per-event VAL_CAP_MULT=100 (skip events exceeding 100× max circulating supply)
2. Per-month CONTAM_MULT=100 (emit NULL for months where on-chain supply > 100× circulating)

Do NOT change these thresholds. Do run the B2 full-panel integrity scan on completion
(reconstructed on-chain supply vs circulating) to catch any new contaminated tokens.

### B3 — Aggregate and assemble

After all newly completed tokens:
a. Re-run `phase1_channel2_panel.py --aggregate` to rebuild channel2_holding.csv
b. Re-run `phase1_assemble_lambda.py` to update lambda_panel.csv
c. Report: new asset-month count, n_channels distribution, new 2-channel and 3-channel assets

### B4 — Screened HODL-6m sanity check

For any token with >50k holders newly completed, spot-check: median screened HODL-6m
should be >0.1% and <95%. Flag any degenerate series.

---

## Rules (unchanged from session 026)

- cmc_id joins ONLY, never symbol.
- DATA_DECISIONS_LOG.md append-only. Continue from Entry 68. One entry per task cluster:
  Entry 68 = TVL expansion (slug discovery + fetch results + panel rebuild stats)
  Entry 69 = ch2 tail results (tokens completed, 3-channel count, integrity scan)
  Entry 70 = session close-out (new λ count, new TVL count, next priorities)
- No additional paid subscriptions. DeFiLlama is free/keyless; Etherscan Pro for ch2.
- Track getLogs call budget for Task B. STOP before DAILY_CAP - 20k.
- Per-token checkpoints make every stop resumable with no data loss.
- PYTHONUTF8=1.
- Update 06_documentation/time_log.md.
- Write session log to 06_documentation/ai_conversations/session_027_*.md.
- Write 03_data/SESSION027_TVL_AND_CH2_REPORT.md (parallel structure to session 026 report).
- Commit and push at session end.

## Deliverables

1. Updated `03_data/phase1/asset_onchain_identity.csv` — new dl_slug entries for priority tokens
2. Updated `03_data/phase2/tvl_panel.csv` — expanded TVL coverage
3. Updated `03_data/phase1/channel2_holding.csv` and `03_data/phase1/lambda_panel.csv`
4. DATA_DECISIONS_LOG entries 68–70
5. `03_data/SESSION027_TVL_AND_CH2_REPORT.md`
6. time_log.md updated; session_027 log written
7. Commit and push

## Not in scope this session

- Coin staking (ch1 for AVAX/BNB/NEAR/INJ/SUI/APT etc.) — multiple non-EVM chains,
  separate research effort; defer to session 028.
- PQ/NVT_GL expansion — defer.
- Any Phase-3 or regression work — defer.
- HEX ch2 — permanently deferred (Entry 66).

STOP at end of session or when DAILY_CAP approaches. If ch2 tail is not fully complete,
checkpoint and report how far down the priority list you reached.
```
