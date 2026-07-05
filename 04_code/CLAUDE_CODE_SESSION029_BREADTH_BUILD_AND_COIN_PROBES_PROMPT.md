# Claude Code Kickoff Prompt — Session 029: Token ch2 Breadth Build + PoS Coin Probes

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`.

Context: Session 028 added 7 PoS coins (+358 coin asset-months) and recovered AAVE's 22
spam-nulled ch2 months. λ is now 7,409 asset-months / 289 assets; 90 assets are
regression-ready (12 coin λ∩NVT_GL + 78 token/other λ∩TVL). Three high-value tasks this
session, in priority order: (A) build ch2 for the 47 non-lambda EVM tokens that already have
confirmed TVL — these enter the NV/TVL regression immediately on λ assignment; (B) verify and
fetch TVL for the 9 lambda tokens that have a DeFiLlama slug but no TVL yet; (C) probe every
unresearched PoS coin for free historical staking data and build what passes the Entry-26
cross-check. Deferred to a later session by design: DOT/KSM (Subscan signup pending), NEAR,
ATOM/INJ/SEI/KAVA (Cosmos — Moazzam sourcing keys separately).

---

```
You're working in the AFA 2027 QTM Crypto research repo. λ is 7,409 asset-months / 289 assets
(session 028, Entry 75). Regression-ready: 12 coin (λ∩NVT_GL) + 78 token/other (λ∩TVL) = 90.
Etherscan Pro key (200k calls/day, 10/s, all EVM chains) is in `.api_keys.json` under
"etherscan". DeFiLlama free/keyless. Three tasks this session in priority order.

## Required reading before starting

- 04_code/DATA_DECISIONS_LOG.md — read Entries 68–75 (session 027-028 full account). Continue
  from Entry 76.
- 03_data/SESSION028_COIN_STAKING_REPORT.md — full session 028 account
- 03_data/phase1/asset_onchain_identity.csv — token contract addresses (erc20_address column
  or equivalent), chain info, dl_slug for TVL
- 04_code/phase1_channel2_stream.py — the validated streaming engine (sessions 025-027).
  READ IT FULLY before Task A. Do not change guard thresholds (VAL_CAP_MULT/CONTAM_MULT=100).
  The AAVE self-transfer skip (`from == to`) added in session 028 is already in the engine.
- 03_data/phase1/lambda_panel.csv — current λ panel (post-028)
- 03_data/phase2/tvl_panel.csv — current TVL panel
- 04_code/phase1_channel1_pos_coins_evm.py — session 028 EVM coin builder (reference for
  multi-chain Etherscan Pro API pattern: `?chainid=<id>`)

## TASK A — ch2 for non-lambda EVM tokens that already have TVL (Entry 76)

### Why these are the priority

47 tokens are in the universe, have confirmed TVL in `tvl_panel.csv`, but have ZERO λ
channels. Building ch2 (HODL-wave via Transfer event replay) assigns them λ with one channel.
Since they already have NV (from universe_panel.csv) and TVL, they are regression-ready the
moment λ is assigned. Up to +47 assets enter the NV/TVL regression with no further work.

### A0 — Multi-chain adaptation

The streaming engine was built for Ethereum mainnet. Several tokens in this list are on other
chains. Before building:
a. Check if `phase1_channel2_stream.py` accepts a `chainid` parameter. If not, add a
   `--chainid` CLI argument that is passed through to the Etherscan Pro API call
   (`?chainid=<id>`). Default = 1 (Ethereum mainnet). Use the same API key for all chains.
b. Verify Etherscan Pro getLogs coverage for the non-mainnet chains used below:
   - BSC (chainid 56): already confirmed (session 028 BNB build)
   - Polygon (chainid 137): probe one recent block to confirm
   - Arbitrum (chainid 42161): probe one recent block to confirm
   - Base (chainid 8453): probe one recent block to confirm
   Log which chains are confirmed in the DATA_DECISIONS_LOG entry.
c. For multi-chain tokens: get the correct token contract address for THAT chain from
   asset_onchain_identity.csv. If missing, look up via Etherscan's token-info endpoint
   (`?module=token&action=tokeninfo&contractaddress=...&chainid=<id>`).

### A1 — Target list (ordered by est_getlogs_calls within each chain group, smallest first)

Build in the order below. Load checkpoints and skip if a token was already completed.
Do NOT build HEX (permanently deferred, Entry 66).

**Ethereum mainnet (chainid 1)** — 36 tokens:

| cmc_id | symbol | est_getlogs_calls | notes |
|--------|--------|-------------------|-------|
| 7242 | CORE (cVault) | 277 | DL slug: cvault-finance |
| 14783 | MAGIC | 465 | DL slug: treasure |
| 9119 | TLM | 466 | DL slug: alien-worlds |
| 11079 | BRISE | 300 | DL slug: bitgert |
| 14803 | AURORA | 611 | DL slug: aurora-plus |
| 6929 | HEGIC | 602 | DL slug: hegic |
| 8602 | AUCTION | 744 | DL slug: bounce-finance |
| 10903 | C98 | 426 | DL slug: coin98 |
| 7654 | RFOX | 773 | DL slug: rfox |
| 3748 | HXRO | 534 | DL slug: hxro-network |
| 1552 | MLN | 759 | DL slug: enzyme-finance |
| 8615 | EPIC | 753 | DL slug: ethernity-chain |
| 5601 | STAKE | 708 | DL slug: xdai-stake-bridge |
| 2933 | BMX | 696 | DL slug: bitmart |
| 2982 | MVL | 939 | DL slug: mvl-staking |
| 4134 | AKRO | 1526 | DL slug: akropolis |
| 1104 | REP | 1628 | DL slug: augur |
| 7617 | SFI | 978 | DL slug: saffron-finance |
| 5566 | KEEP | 949 | DL slug: keep-network |
| 5957 | YFII | 1159 | DL slug: yfii |
| 5829 | SWAP | 1390 | DL slug: team-finance |
| 17799 | AXL | 982 | Axelar; check addr in aoi.csv |
| 9543 | BICO | 1403 | DL slug: hyphen |
| 3814 | CELR | 1832 | DL slug: cbridge |
| 1166 | WARP | 2543 | DL slug: polkastarter |
| 7857 | MIR | 2317 | DL slug: mirror |
| 1732 | NMR | 3126 | DL slug: erasure |
| 8290 | SUPER | 3407 | DL slug: superfarm |
| 30083 | ATH | 4320 | DL slug: aethir |
| 7232 | ALPHA | 924 | DL slug: stella |
| 34812 | BIO | 894 | DL slug: bio-protocol |
| 5631 | ORN | 784 | DL slug: dedust |
| 8719 | ILV | 4276 | DL slug: illuvium |
| 5845 | BTCST | — | BSC item listed below |
| 6945 | AMP | 8106 | DL slug: flexa; large |
| 10804 | FLOKI | 8199 | DL slug: flokifi-locker; large |

**BSC (chainid 56)** — 7 tokens (probe getLogs on BSC first):

| cmc_id | symbol | notes |
|--------|--------|-------|
| 8335 | MDX | DL slug: mdex |
| 8938 | EPS | DL slug: ellipsis-finance |
| 7064 | BAKE | DL slug: bakeryswap |
| 8891 | BTCST | DL slug: btcst |
| 9175 | MBOX | DL slug: mobox |
| 8972 | SFUND | DL slug: seedify |
| 36410 | MYX | DL slug: myx-finance |

**Polygon (chainid 137)** — 1 token (probe first):

| cmc_id | symbol | est_getlogs_calls | notes |
|--------|--------|-------------------|-------|
| 24796 | ADF | 1871 | DL slug: artdefinance |

**Arbitrum (chainid 42161)** — 1 token (probe first):

| cmc_id | symbol | est_getlogs_calls | notes |
|--------|--------|-------------------|-------|
| 38341 | RAIN | 13637 | DL slug: rain; LARGEST — build last |

**Base (chainid 8453)** — 3 tokens (probe coverage first; build only if getLogs confirmed):

| cmc_id | symbol | notes |
|--------|--------|-------|
| 38299 | AVNT | DL slug: avantis |
| 35763 | KAITO | DL slug: kaito |
| 35509 | VVV | DL slug: venice |

**Skip (non-EVM, cannot build with current APIs):**
SXP (4279), RUNE (4157), OSMO (12220), SUN (10529), CASINO (1573)

### A2 — Build protocol

For each token:
a. Get the ERC-20 contract address from asset_onchain_identity.csv. If missing, use
   Etherscan's `tokeninfo` endpoint for the relevant chain.
b. Run the streaming engine with `--chainid <id>` (or equivalent). Same guard thresholds:
   VAL_CAP_MULT=100, CONTAM_MULT=100. Per-token checkpoint saves automatically.
c. If a token is a known scam/dead/zero-transfer contract (0 Transfer events in last 100k
   blocks), log it and move on — do not spend getLogs budget.
d. After completing each chain group, verify B2 integrity scan: reconstructed on-chain supply
   vs CMC circulating. Log any contaminated months (there should be few — these tokens were
   pre-screened).

### A3 — Budget management

DAILY_CAP = 200,000 getLogs calls. Reserve 20k headroom. Checkpoint per-token.
Build smallest-first so large tokens (AMP 8k, FLOKI 8k, RAIN 14k) land at the end of each day.
If daily cap approaches, stop cleanly at the current token boundary — the checkpoint makes
resumption zero-loss. Session 028 used only ~45k calls — this session has a full 200k budget.

### A4 — Aggregate and assemble (after Task A completes)

a. Run `phase1_channel2_panel.py --aggregate` to rebuild channel2_holding.csv
b. Run `phase1_assemble_lambda.py` to update lambda_panel.csv
c. Report: new λ asset-months, how many of the 47 targets newly entered λ, how many were
   skipped (dead/non-EVM/LUT), new NV/TVL regression-ready count

---

## TASK B — TVL for lambda tokens with orphaned dl_slugs (Entry 77)

Nine lambda tokens have a dl_slug in `asset_onchain_identity.csv` but are absent from
`tvl_panel.csv`. Three were explicitly rejected in session 027 (GBYTE/oswap-amm = third-party
DEX, not protocol TVL; PENGU/pudgy-penguins = not Abstract's fee token; CYBER/cyberconnect =
chain TVL ~$0). Do NOT re-attempt those three.

The remaining 6 to check (probe DeFiLlama, accept if TVL is non-trivial and continuous):

| cmc_id | symbol | dl_slug | notes |
|--------|--------|---------|-------|
| 19269 | COW | cowswap | CoW Protocol — batch-auction DEX; should have genuine TVL |
| 1896 | ZRX | 0x-aggregator | 0x limit-order system; may have low TVL |
| 9421 | FORTH | forth-dao | Ampleforth governance; probably minimal TVL |
| 13855 | ENS | ens | ENS is a naming service, not a DeFi protocol — likely $0 TVL |
| 10052 | GTC | gitcoin | Gitcoin grants — likely $0 TVL |
| 23054 | CHEEL | cheelee | Verify if DeFiLlama reports non-trivial TVL |

For each:
a. GET `https://api.llama.fi/protocol/{slug}` — inspect the TVL series.
b. Accept if: TVL series exists, at least 6 months non-zero, values in USD (not fractions
   of a cent). Add to tvl_panel.csv and asset_onchain_identity.csv (dl_matched=True).
c. Reject if: TVL is $0 or near-zero throughout, or the protocol is clearly a
   different entity than the token. Log the rejection reason.
d. After any adds: re-run `phase2_build_tvl_panel.py` and re-run `phase1_assemble_lambda.py`
   so newly TVL-covered lambda tokens reflect in the regression-ready count.

---

## TASK C — Probe and build unresearched PoS coins (Entry 78)

Goal: find free historical staking data for PoS coins not previously researched, build any
that pass the Entry-26 cross-check (~0% drift vs the chain's own on-chain figure). Deferred
scope (do NOT probe this session): DOT/KSM, NEAR, ATOM/INJ/SEI/KAVA.

The Entry-26 bar applies to coins exactly as to tokens: the reconstructed series must
reproduce the chain's own on-chain staked total at ~0% drift at ≥3 probe points before
being accepted. If a source is found but drift is >5% and unexplained, document as a gap.
"Flag, don't guess."

Build in sub-task order below. EVM-accessible chains first (highest probability of success
with the Etherscan Pro key already in hand), then native-chain API probes.

### C1 — EVM-accessible PoS coins (probe Etherscan Pro + chain RPC)

**POL (cmc_id 28321, Polygon 2.0 token)**

Polygon PoS validator staking is managed by the `StakeManager` contract on Ethereum MAINNET
at `0x5e3Ef299fDDf15eAa0432E6e66473ace8c13D908` (chainid 1). Before 2024, MATIC was the
staked token; after the Polygon 2.0 migration (Sept 2023) POL replaced MATIC, but the
staking contract on Ethereum still accepts both via migration contracts.

a. Probe StakeManager getLogs on Ethereum mainnet for staking events. Key events:
   `Staked(address indexed signer, uint256 indexed validatorId, uint256 nonce,
   uint256 indexed activationEpoch, uint256 amount, uint256 total, address indexed contractAddress)`
   and `UnstakeInit(...)` / `Unstaked(...)`. The `total` field in Staked may give running
   aggregate directly (spot-check).
b. If reconstruction is feasible: build the monthly series from 2020-06 (Polygon PoS launch)
   to 2026-05. Cross-check: reconstructed month-end total vs live `currentValidatorSetSize()`
   or `totalStaked()` on StakeManager.
c. Denominator: POL/MATIC circulating supply from universe_panel.csv (cmc_id 28321 or
   MATIC cmc_id 3890 — check which is in the universe; join on cmc_id only).
d. If getLogs approach fails (too complex event accounting, MigrateSuccess-like inflation):
   try Etherscan's `balancehistory` on StakeManager for native MATIC balance — this would
   give total staked MATIC at each block.

**FLR (cmc_id 7950, Flare Network, chainid 14)**

Flare has FTSO2 staking (direct validator staking) and delegation contracts. Staking launched
~2023. Check whether chainid 14 is covered by Etherscan Pro (probe a recent getLogs).
If covered:
a. Identify the staking contract on Flare (check flare-explorer.flare.network or
   flare.network/developers for ValidatorRewardManager or StakingManager address).
b. Probe getLogs for Stake/Unstake events. Build if reconstructable.
c. Cross-check vs live total staked reported by the chain explorer.

**RON (cmc_id 14101, Ronin Network, chainid 2020)**

Ronin is an Ethereum sidechain. Check if chainid 2020 is covered by Etherscan Pro.
If covered:
a. Identify Ronin's staking contract (`RoninValidatorSet` or `StakingContract` —
   check app.roninchain.com or docs.roninchain.com).
b. Probe getLogs for Staked/Unstaked events. Build if cross-check passes.

**KLAY/KAIA (cmc_id 4256, Kaia blockchain, chainid 8217)**

Klaytn rebranded to Kaia. Kaia uses a governance council model. Check if chainid 8217
is in Etherscan Pro. If so, probe the staking/governance contract for getLogs.
Note: Kaia's GC staking may be managed through off-chain governance — if no staking events
exist on-chain, document and move on.

**CRO (cmc_id 3635, Cronos EVM, chainid 25)**

Cronos EVM is an EVM chain but CRO staking is primarily on the Crypto.org chain (Cosmos SDK),
not on Cronos EVM. Probe chainid 25 for a staking contract; if none found, note this and
log as gap (Cosmos-side, same gate as ATOM).

**CHZ (cmc_id 4066, Chiliz chain, chainid 88888)**

Chiliz 2.0 has an EVM-compatible chain. Check if chainid 88888 is in Etherscan Pro.
If so, probe for validator staking events. If not covered, check if Chiliz has a free
native API (chiliscan.com API) with historical staking totals.

**LSK (cmc_id 1214, Lisk)**

Lisk migrated to an Ethereum L2 (Lisk chain, chainid 1135, built on OP Stack) in 2024.
LSK staking may now exist as an EVM contract on chainid 1135. Check Etherscan Pro coverage
for chainid 1135; also check lisk.com/documentation for a staking contract address.
If staking exists and the chain is covered: probe and build.

### C2 — Native-chain API probes (non-EVM)

For each coin below: make at least one live API call to confirm the endpoint structure,
then determine if historical monthly data is freely available. Build if yes; document gate if no.

**TON (cmc_id 11419, The Open Network)**
- Primary: `https://tonapi.io/v2/blockchain/masterchain/stats` or
  `https://toncenter.com/api/v3/statistics` — check for a `staking` or `total_stake` field.
- Historical: try `https://tonapi.io/v2/rates/history?tokens=TON&start=<unix>&end=<unix>` to
  see what history is served; separately check if ton.org/v3 has a staking timeseries endpoint.
- If historical staking tonnage available: build monthly series from TON mainnet (~2021-12).
  Cross-check vs tonviewer.com reported staked TON.

**EGLD (cmc_id 6892, MultiversX / formerly Elrond)**
- Primary: `https://api.multiversx.com/economics` — confirmed to return a `staked` field
  (check live). This is the current snapshot.
- Historical: try `https://api.multiversx.com/economics?timestamp=<unix>` or check if the
  MultiversX data API serves historical economics snapshots. Also try:
  `https://tools.multiversx.com/analytics-api/query?series=totalValueStaked&resolution=month`
  (the Grafana-style analytics endpoint that powers their explorer charts).
- If historical series available: build from EGLD mainnet launch (~2020-09).

**FLOW (cmc_id 4558, Flow blockchain)**
- Primary: `https://rest-mainnet.onflow.org/v1/network/parameters` and
  `https://flowscan.io/api/staking` (or similar).
- Historical: try `https://flowdiver.io/api/v1/staking/history?interval=monthly` or
  the Flow Access API's `GetAccountAtLatestBlock` for the staking contract.
- The Flow staking contract is at `0x8624b52f9ddcd04a`. Try querying `totalCommitted()`
  via the Flow Access API Cadence script at historical block heights.
  Block height ↔ timestamp mapping via `https://rest-mainnet.onflow.org/v1/blocks/{height}`.
- If historical series feasible: build from FLOW launch (~2020-10).

**STRK (cmc_id 22691, Starknet)**
- Starknet staking launched ~2024-11 via the staking contract at
  `0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d` on Starknet mainnet.
- Try `https://alpha-mainnet.starknet.io/feeder_gateway/get_state_update?blockNumber=<n>` or
  `https://starknet.io/api/staking/total` (if it exists).
- Starknet IS an Ethereum L2 but uses its own transaction format (not EVM). Etherscan Pro does
  NOT cover Starknet. Try the official Starknet API or Starkscan API
  (`https://api.starkscan.co/api/v0/statistics/staking`) for historical total staked.
- Note: if staking series only covers 2024-11 onward (~8 months), still build — a short
  series is better than no series.

**DFI (cmc_id 5804, DeFiChain)**
- DeFiChain uses its own blockchain (not EVM). Staking via masternodes.
- Try `https://ocean.defichain.com/v0/mainnet/stats` — check if it includes a staking/
  masternode total. Also try `https://defiscan.live/api/stats`.
- Historical: check `https://ocean.defichain.com/v0/mainnet/stats?timestamp=<unix>` or
  look for a DeFiChain analytics API with time-series staking data.

**DASH (cmc_id 131, Dash)**
- Dash masternodes require a 1,000 DASH collateral lock. This is economically equivalent
  to staking for the purposes of Channel 1 (capital locked in consensus participation).
- Try `https://insight.dash.org/insight-api/masternode/count` for current count.
- Historical: check `https://stats.masternode.me/api/history` or the official Dash data
  API for monthly masternode count + collateral (1000 DASH × count = total locked).
- Cross-check: reconstructed total locked DASH vs live masternode count × 1000.
- If monthly masternode count history is available: build the series. Flag that the
  mechanism is masternode-collateral (not PoS delegation) in the DATA_DECISIONS_LOG.

**Additional low-probability probes (attempt if budget allows, document gate if not):**

XRD (cmc_id 11948, Radix): try `https://babylon-mainnet-gateway.radixdlt.com/statistics/validators/uptime`
or `https://radix-babylon-gateway.api.radixdlt.com` for historical staking statistics.

PEAQ (cmc_id 14588): check peaq.network docs/API for historical staking series.

CORE (cmc_id 23254, Core blockchain): check `https://openapi.coredao.org` for historical
total staked CORE.

HYPE (cmc_id 32196, Hyperliquid): Hyperliquid is a new chain (~2024). Check if
`https://api.hyperliquid.xyz/info` returns staking data, and if history is available.

WAN (cmc_id 2606, Wanchain): try `https://www.explorewanchain.org/api/staking/history` or
similar; Wanchain has PoS since ~2020.

For any coin where data is found but the series is <6 months: build anyway (short series
still enters the cross-section; annotate in the flag column).

### C3 — EVM coin build protocol (same as session 028)

If an EVM staking source is found:
a. Verify live: make the actual API call, check response shape and magnitude.
b. Build from chain genesis (or earliest available month) to 2026-05.
c. Entry-26 cross-check: reconstructed month-end total vs chain's own live figure at ~0%
   drift (≤5% accepted if the source of drift is fully explained and documented).
d. Denominator: coin circulating supply from universe_panel.csv (cmc_id join only).
e. Add to `phase1_channel1_pos_coins_evm.py` or create `phase1_channel1_pos_coins_native.py`
   for non-EVM native-API coins.
f. The assembler's `channel1_*.csv` glob picks up any new `channel1_*.csv` file automatically.

---

## TASK D — Assemble, update coverage CSV, report (Entry 79)

After all tasks complete:

a. Final assemble: `phase1_assemble_lambda.py` → updated lambda_panel.csv
b. Rebuild TVL panel if any new slugs confirmed: `phase2_build_tvl_panel.py`
c. **Regenerate `03_data/universe_coverage_status.csv`**: the existing file is stale
   (generated pre-session-027, reflects none of sessions 027/028 progress). Run the same
   generation script (or recreate it inline) using the updated lambda_panel, nvt_gl_panel,
   and tvl_panel. Columns must include: cmc_id, symbol, name, asset_class, sector,
   coin_staking_type, lambda_months, lambda_n_channels, lambda_channels, has_ch1, has_ch2,
   has_ch3_v, has_ch3_d, has_nvt_gl, nvt_months, pq_source, has_tvl, tvl_months,
   holder_count, est_getlogs_calls, evm_chain, etherscan_reachable, coverage_status,
   what_needed.
d. Report in `03_data/SESSION029_BREADTH_AND_COIN_PROBE_REPORT.md`:
   - Task A: which tokens built, which skipped (reason), new λ count, new regression-ready count
   - Task B: TVL slug verdicts (accepted/rejected + reason for each)
   - Task C: per-coin probe outcome (built / gate-open / gap-confirmed), with the exact gate
     and Moazzam action for any open items
   - Final regression-ready tally: coin (λ∩NVT_GL) + token/other (λ∩TVL) = total

---

## Rules (unchanged)

- cmc_id joins ONLY, never symbol.
- Entry-26 cross-check bar for all new coin series: ~0% drift vs the chain's own figure.
  A series that fails cross-check is NOT shipped — it becomes a documented gap.
- DATA_DECISIONS_LOG.md append-only. Continue from Entry 76:
  Entry 76 = Task A results (ch2 breadth build — tokens built, skipped, budget used)
  Entry 77 = Task B results (TVL slug verification verdicts)
  Entry 78 = Task C results (coin probe outcomes — built / gate / gap per coin)
  Entry 79 = session close-out (new λ count, new regression-ready count, gap register)
- No additional paid subscriptions. Etherscan Pro (existing) + keyless sources only.
- Do NOT sign up for anything. If a source requires a free self-serve signup, log the exact
  URL and what Moazzam needs to do — do NOT complete the signup in a headless session.
- Deferred this session (Moazzam sourcing separately): DOT/KSM (Subscan), NEAR (Pikespeak),
  ATOM/INJ/SEI/KAVA (Cosmos Mintscan/Numia), BERA (no beacon-kit archive API).
- PYTHONUTF8=1.
- Update 06_documentation/time_log.md.
- Write session log to 06_documentation/ai_conversations/session_029_*.md.
- Write 03_data/SESSION029_BREADTH_AND_COIN_PROBE_REPORT.md.
- Commit and push at session end.

## Deliverables

1. Updated `03_data/phase1/channel2_holding.csv` — new ch2 rows for Task A tokens
2. Updated `03_data/phase1/lambda_panel.csv` — all new λ assignments
3. Updated `03_data/phase2/tvl_panel.csv` — any new TVL series from Task B
4. New/extended `04_code/phase1_channel1_pos_coins_evm.py` or `_native.py` — any new coin
   ch1 series from Task C
5. Updated `03_data/universe_coverage_status.csv` — fresh post-029 coverage map
6. DATA_DECISIONS_LOG entries 76–79
7. `03_data/SESSION029_BREADTH_AND_COIN_PROBE_REPORT.md`
8. Gap register: for each open item, the exact gate and Moazzam action (e.g., "sign up at
   X, get key Y, drop in .api_keys.json under 'Z', re-run script W")
9. time_log.md updated; session_029 log written
10. Commit and push

## Not in scope this session

- DOT/KSM — deferred (Subscan signup pending; Moazzam will retry and run a dedicated session)
- NEAR — deferred (Pikespeak gate; Moazzam sourcing)
- ATOM/INJ/SEI/KAVA — deferred (Cosmos keys; Moazzam sourcing)
- BERA — permanent gap unless Berachain ships a public CL archive API
- HBAR/SUI/ALGO/EOS/ICP/APT — unchanged from Entry 45/47; do not re-check
- Phase-3 / regression work — defer
- PQ/NVT_GL expansion — defer
- ch3 for new tokens — defer (ch2 single-channel is the priority; ch3 can be added later)

STOP at end of session or when daily getLogs budget approaches. All stops are clean via
per-token checkpoints. Resume with the next uncompleted token in the priority list.
```
