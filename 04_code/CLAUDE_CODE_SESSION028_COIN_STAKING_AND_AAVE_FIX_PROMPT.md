# Claude Code Kickoff Prompt — Session 028: Coin Staking (ch1) Expansion + AAVE ch2 Fix

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`.

Context: Sessions 025–027 built Channel-2 for 260 tokens, created the first 3-channel assets,
and expanded TVL to 130 tokens. λ is 7,051 asset-months / 282 assets. The coin side of the
regression is thin: only 5 coin assets have BOTH λ AND NVT_GL (ETH, TRX, ADA, SOL + 1 more).
49 coins have NVT_GL but NO λ. This session expands coin ch1: first via EVM chains already
covered by the Etherscan Pro key (no new signups), then via non-EVM probes. Secondary task:
AAVE ch2 spam-window fix.

NOTE: Moazzam's Etherscan Pro Standard Plan (activated 2026-06-30) covers the following
chains that are relevant to coin staking this session — all accessible with the existing
"etherscan" key in `.api_keys.json`:
  chainid 56   = BNB Smart Chain (BNB staking)
  chainid 1284 = Moonbeam (GLMR staking via ParachainStaking precompile)
  chainid 1285 = Moonriver (MOVR staking via ParachainStaking precompile)
  chainid 146  = Sonic Mainnet (S/Sonic staking via SFC contract)
  chainid 80094= Berachain (BERA Proof-of-Liquidity staking contract)
  chainid 50   = XDC Network (XDC validator staking)
  chainid 5000 = Mantle Mainnet (MNT staking — lower priority, verify mechanism first)
  chainid 42220= Celo Mainnet (CELO — getLogs failed Entry-26 cross-check; try balance history)
  chainid 43114= Avalanche C-Chain (AVAX — note: AVAX staking is P-Chain, NOT C-Chain;
                 this chainid does NOT help with AVAX staking)
DOT/KSM Subscan signup failed (code verification error at pro.subscan.io) — skip this session.

---

```
You're working in the AFA 2027 QTM Crypto research repo. λ is 7,051 asset-months / 282 assets
(session 027, Entry 70). Two tasks this session, in priority order.

## Required reading before starting

- 04_code/DATA_DECISIONS_LOG.md Entries 41–47, 70 — the full coin-staking audit:
    Entry 41 = first live coin-staking pass (ADA/XTZ built; gaps documented)
    Entry 42 = Bucket-2 four-way gap reclassification (free/engineering/paid/none)
    Entries 43–47 = per-chain build/reject/gap outcomes (TRX/SOL built; DOT/KSM key-gated;
                    HBAR/SUI engineering; CELO EVM-reclassified but cross-check failed;
                    ATOM/INJ/SEI/KAVA/AVAX/NEAR/EOS/ICP/APT gates documented)
    Entry 70 = session 027 close-out, coin staking listed as top next priority
- 03_data/universe_coverage_status.csv — the NEW post-027 coverage map; filter to
    asset_class='coin' AND has_nvt_gl=True AND has_ch1=False to get the 49-coin target list.
    These are coins with the denominator ready but no lambda — each one built enters regression.
- 04_code/phase1_channel1_pos_coins.py — ADA, XTZ builder (extend, don't rewrite)
- 04_code/phase1_channel1_pos_coins_bucket2.py — TRX, SOL builder (extend, don't rewrite)
- 04_code/.api_keys.json — check for keys: "etherscan" (Pro, 200k/day, all chains incl. BSC),
    "subscan" (may or may not be present — see Task A2)
- 03_data/SESSION027_TVL_AND_CH2_REPORT.md — full session 027 account

Continue DATA_DECISIONS_LOG from Entry 71. One entry per coin/chain group.

---

## TASK A — Coin staking ch1 expansion (Entries 71+)

Work through the chains below in priority order. For EACH chain: (1) verify the source live
before building — an actual API call, not docs inference; (2) cross-check the reconstructed
series against a live on-chain reference (the Entry-26 bar applied to coins — e.g. compare the
reconstructed month-end total to the chain's own reported staked supply for the same date);
(3) build only if cross-check passes; (4) log the result in DATA_DECISIONS_LOG regardless of
whether you build or document a gap.

The standard pattern for ALL EVM coin staking builds below:
- Use `eth_getLogs` (via Etherscan Pro V2 API, `?chainid=<id>`) on the staking contract
- Replay events to reconstruct net staked total at each month-end block
- Cross-check reconstructed total vs live on-chain `eth_call` to the staking contract's
  getter function (e.g. `totalStaked()`, `totalPooledBNB()`, etc.) at ~0% drift
- Denominator = circulating supply from universe_panel.csv (cmc_id join), NOT max_supply
- Extend `phase1_channel1_pos_coins_bucket2.py` (or a new `_evm.py`) — do not rewrite

### A1 — BNB via BSC (Etherscan Pro, cmc_id 1839)

BNB's coin-level conviction is BSC validator/delegator staking. Since the Luban upgrade
(~2023-06), BSC uses the StakeHub system contract at
`0x0000000000000000000000000000000000002002` (chainid 56). Before Luban, an older Staking
system contract (`0x0000000000000000000000000000000000001000`) handled validator staking.

a. Probe StakeHub getLogs on BSC (chainid 56, Etherscan Pro key):
   - Event: `Delegated(address indexed operatorAddress, address indexed delegator,
     uint256 bnbAmount, uint256 shares)` — confirms delegation in.
   - Event: `Undelegated(address indexed operatorAddress, address indexed delegator,
     uint256 shares, uint256 bnbAmount)` — confirms delegation out.
   - Use a recent short block range first (last 10k blocks) to confirm the events fire and
     the amounts are in BNB (wei) and are plausible (billions of BNB delegated = nonsense;
     tens of millions = plausible).
b. If events confirmed: replay all Delegated and Undelegated events (same streaming FIFO
   approach as ch2, or a running-net approach since the net staked total at each month-end
   block is: cumsum(Delegated.bnbAmount) - cumsum(Undelegated.bnbAmount) + pre-Luban state).
   NOTE: for the pre-Luban period, the old staking contract may need a separate probe. If it
   is too complex to reconcile the two contracts, start from the Luban upgrade block and note
   pre-2023-06 is a documented gap.
c. Cross-check: compare reconstructed month-end total against BscScan's reported staked BNB
   on the same date (BscScan staking dashboard, or `totalPooledBNB()` on the StakeHub).
   Must reproduce the on-chain figure at ~0% drift.
d. Denominator = BNB circulating supply from universe_panel.csv (cmc_id join), same as
   all other Channel-1 builds. Do NOT use max_supply.
e. If getLogs or cross-check fail, document the specific reason (event topic mismatched,
   reconstruction >10% off on-chain, etc.) and move on.

### A2 — GLMR / MOVR via Moonbeam/Moonriver (Etherscan Pro, cmc_id 6836 / 9285)

Moonbeam (chainid 1284) and Moonriver (chainid 1285) are EVM-compatible Polkadot/Kusama
parachains. Their validator/collator staking is exposed as an EVM precompile:
  Moonbeam:  `0x0000000000000000000000000000000000000800` (ParachainStaking)
  Moonriver: `0x0000000000000000000000000000000000000800` (same address, different chain)

a. Probe getLogs on the ParachainStaking precompile for staking-relevant events. Likely
   candidates: `Delegation(...)`, `DelegationIncreased(...)`, `DelegationDecreased(...)`,
   `DelegatorLeft(...)`. Try a short recent block range first to confirm events fire and
   amounts are in GLMR/MOVR (18 decimals).
b. If events confirmed and net staked balance is reconstructable: build the monthly series
   from chain genesis (Moonbeam ~2021-12, Moonriver ~2021-08) to 2026-05.
c. Cross-check: compare reconstructed total staked against `totalStake()` or equivalent
   getter on the precompile, or Moonscan's reported staked supply.
d. If getLogs on the precompile fails or events are insufficient to reconstruct net staked
   (e.g. events track per-delegator changes but no aggregate is reconstructable): try
   querying `totalStake()` directly via `eth_call` at each month-end block on Etherscan Pro.
   This is ~70 calls for Moonbeam's history — cheap and clean.
e. Log result (Entry 71).

### A3 — S (Sonic) via Sonic Mainnet (Etherscan Pro, cmc_id 32684)

Sonic Mainnet (chainid 146) uses the SFC (Special Fee Contract / Staking Facility Contract)
for validator staking — the same contract family as Fantom Opera (Sonic's predecessor).
SFC contract address on Sonic: likely `0xFC00FACE00000000000000000000000000000000`
(verify on sonic.ftmscan.com / sonicscan.org before using).

a. Probe getLogs on the SFC contract for staking events. Key candidates:
   `Delegated(address indexed delegator, uint256 indexed toStakerID, uint256 amount)` and
   `Undelegated(...)`. A recent short block range first.
b. If events confirmed: replay Delegated/Undelegated to reconstruct net staked total per
   month-end. SFC also has `totalActiveStake()` getter for cross-check.
c. Cross-check vs `totalActiveStake()` via eth_call at a recent month-end block.
d. Log result (Entry 71).

### A4 — BERA via Berachain (Etherscan Pro, cmc_id 24647)

Berachain (chainid 80094) uses Proof of Liquidity. BERA staking involves the BeaconDeposit
contract or a dedicated validator staking contract.

a. Identify the correct staking contract on Berachain (check beratrail.io or berascan.com
   for the main staking/deposit contract address).
b. Probe getLogs for deposit/stake events (likely `Deposit(...)` on a deposit contract, or
   similar). If Berachain launched recently (~2025), the history may be short — that's fine,
   build what's available.
c. Cross-check vs reported total staked BERA.
d. If the staking mechanism is purely Cosmos-side (Berachain is a Cosmos-EVM hybrid) and
   getLogs cannot reconstruct it: document as gap and move on.
e. Log result (Entry 71).

### A5 — XDC via XDC Network (Etherscan Pro, cmc_id 2634)

XDC Network (chainid 50) uses a Proof-of-Stake-XinFin consensus. Masternodes stake XDC.
Check xdcscan.com for the staking/masternode contract.

a. Identify the staking contract (XDC uses a `XDCValidator` contract for masternode staking;
   likely at a known address — check xdcscan.com or XDC's official docs).
b. Probe getLogs for `Staked(...)` / `Unstaked(...)` or equivalent events.
c. Cross-check vs reported total staked XDC.
d. Log result (Entry 72).

### A6 — DOT / KSM (DEFERRED — Subscan signup failed)

DOT (cmc_id 6636) and KSM (cmc_id 5034): Subscan free-tier signup failed at verification
step (code delivery issue at pro.subscan.io). Log as "deferred — Subscan free key needed;
signup blocked by verification code failure; retry later." Do NOT attempt to build without
a key. Do NOT purchase Subscan Pro.

Note: if a "subscan" key IS found in `.api_keys.json` at runtime, build DOT/KSM using the
method in Entry 44 (`era_stat` endpoint, paginate, cross-check). Otherwise log and skip.

### A7 — CELO via Etherscan Pro balance history (cmc_id 5567)

Entry 46: getLogs reconstruction underperformed (3× undercount) because native CELO locking
does not emit ERC20 Transfer logs. Etherscan Pro has a `balancehistory` endpoint
(`/api?module=account&action=balancehistory&address=<contract>&blockno=<block>&chainid=42220`)
that returns the native coin balance of an address at a specific block — i.e. the LockedGold
contract's native CELO balance at each month-end block, without needing to reconstruct from
events.

a. Probe Celoscan (chainid 42220) balance history: for the LockedGold contract
   `0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E`, call `balancehistory` at the most recent
   month-end block. Confirm the endpoint is accessible with the Etherscan Pro key on
   chainid 42220 and returns a non-zero CELO balance in wei.
b. If the endpoint works: fetch month-end CELO balance for the LockedGold contract at each
   month-end block from 2020-06 (CELO mainnet) to 2026-05. Cross-check: latest month-end
   balance vs `getTotalLockedGold()` live call (Entry 46 found live balance of 82.43M CELO).
   Must reproduce at ~0% drift.
c. If endpoint works and cross-check passes: build the series, add to pos_coins_bucket2.py.
d. If endpoint is blocked on chainid 42220 or returns all zeros: document as still-open gap
   (the ONLY fix is a paid balance-history endpoint or archive eth_call node), move on.

### A8 — AVAX via AvaCloud Metrics API (cmc_id 5805)

Entry 42/47: AvaCloud has a historical "Staking Information" feature but the free vs paid
gate was genuinely unclear from public pricing pages.

a. Make a direct GET to the AvaCloud Metrics API staking endpoint:
   `https://glacier-api.avax.network/v1/chains/mainnet/metrics/staking` (try both with
   and without an `x-glacier-api-key` header). Also try:
   `https://metrics.avax.network/v2/network/staking/historic` if that exists.
   Record: (1) HTTP status code, (2) whether it requires a key, (3) whether a free key
   can be obtained self-serve without purchasing.
b. If a free endpoint exists: fetch the historical total staked AVAX series, build,
   cross-check against the Avalanche Explorer's reported staked supply.
c. If key-gated with a self-serve free signup: do NOT sign up (non-interactive session).
   Log the exact gate and URL so Moazzam can complete the signup in 5 minutes.
d. If paid-only or contact-sales: log as documented gap, no purchase.

### A9 — NEAR via NearBlocks (cmc_id 6535)

Entry 47: NearBlocks confirmed current `/v1/stats` only; historical staking endpoint and
pricing unconfirmed.

a. Probe `https://api.nearblocks.io/v1/stats` — confirm it returns current staking data
   (total staked NEAR, validators, etc.).
b. Check if NearBlocks has a `/v1/staking/history` or similar historical endpoint. Try:
   `https://api.nearblocks.io/v1/validators/stats?from=2021-01-01&to=2021-12-31` or
   similar date-windowed queries. Also check `https://api3.nearblocks.io/v1/stats` (v3).
c. If a free historical endpoint exists: build the monthly series from NEAR genesis
   (~2020-10) to 2026-05. Cross-check against NEAR's reported total staked.
d. If not available free: log the specific gate and move on.

### A10 — Cosmos chains: ATOM, INJ, SEI, KAVA (alternative free sources)

Entry 47: Mintscan is contact-sales; Bitquery has a trial-only free tier; public LCD is
current-state-only. Try two alternative sources NOT checked before:

a. **StakingRewards.com API** (`https://api.stakingrewards.com/public/query`):
   StakingRewards has an undocumented or documented GraphQL API. Try:
   - Query for ATOM staking history: `{ assets(where: { slug: "cosmos" }) { metrics
     { rewardRate stakedTokens } } }` or similar. Determine if the response includes
     historical time-series data (not just current snapshot).
   - If historical data is available for ATOM, try INJ/SEI/KAVA with their respective slugs.
   - If only current state: document and move on.
b. **Numia (open Cosmos data)** (`https://data.numia.xyz`): Numia provides indexed Cosmos
   data as BigQuery public datasets. Check if they have a REST endpoint for historical
   bonded tokens per chain, or if data is BigQuery-only (requires a Google account, outside
   scope of this non-interactive session).
c. If neither source provides free historical Cosmos staking: leave ATOM/INJ/SEI/KAVA as
   documented gaps (Entry 47 stands). Do NOT contact Mintscan.

### A11 — Assemble and report

After all attempts:
a. Re-run `phase1_channel1_pos_coins.py` and `phase1_channel1_pos_coins_bucket2.py` to
   regenerate the Channel-1 pos-coin CSVs.
b. Re-run `phase1_assemble_lambda.py` to fold new coin ch1 series into lambda_panel.csv.
c. Report:
   - Which coins were newly built (cmc_id, source, cross-check drift, months built)
   - Which gates remain open (chain, gate type, what Moazzam needs to do)
   - New λ asset-month count, new coin λ count, new coin λ∩NVT_GL count (regression-ready)

---

## TASK B — AAVE ch2 spam-excluded window recovery (Entry ~72)

Context (Entry 66): AAVE's 2024-08→2026-05 ch2 months were nulled by the contamination fix
because AAVE's address-poisoning spam pushed its reconstructed on-chain supply to 1.16e60
tokens in that window. The per-event VAL_CAP_MULT=100 fix removed phantom lots and restored
real data for months where per-event capping was enough — but some months still exceeded the
CONTAM_MULT=100 threshold and were nulled. The Entry-66 note flagged a per-token totalSupply
approach as a more precise fix.

AAVE currently has 67 ch2 months (max n_channels=3), with 22 nulls in the recent window.
Recovering them gives AAVE 3-channel coverage through 2026-05 (the full panel window).

a. Check: for AAVE (cmc_id 7278), inspect the ch2 checkpoint (in
   `03_data/raw/phase1_onchain/holding/`). Identify which months have null ch2.
b. The fix: use AAVE's actual ERC20 `totalSupply()` at each month-end block (via
   `eth_call`) as the denominator instead of the reconstructed lot-sum (which is polluted
   by phantom lots from spam). The CONTAM_MULT check compares reconstructed supply to CMC
   circulating; with the real totalSupply as denominator, the HODL share is anchored to
   actual on-chain supply even when phantom lots exist in the numerator.
   NOTE: this is a PER-TOKEN fix for AAVE only — do NOT change the global thresholds
   (VAL_CAP_MULT and CONTAM_MULT) or apply this approach universally.
c. For each null month: call `eth_call` on AAVE's token contract
   (`0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE8`, mainnet) at the month-end block to get
   `totalSupply()`. Use this as the denominator. Recompute screened HODL-6m = (sum of
   lots >6m old held by non-contract addresses) / totalSupply.
d. Cross-check: for a month where ch2 was not null, verify that using totalSupply vs
   the reconstructed lot-sum gives similar HODL shares (they should be close for clean months,
   since totalSupply ≈ on-chain lot-sum when no phantom lots exist).
e. If the recovered series looks economically reasonable (0.5%–80%, not 100% every month),
   write the updated rows back. Use `--recompute` if supported; otherwise patch the ch2
   checkpoint and re-aggregate.
f. Re-run `phase1_assemble_lambda.py` after AAVE fix. Report: months recovered, HODL-6m
   range for the recovered months.

---

## Rules (unchanged)

- cmc_id joins ONLY, never symbol.
- Entry-26 cross-check bar: reconstructed series must reproduce the on-chain state at ~0%
  drift before being folded into lambda. A series that fails cross-check is NOT shipped —
  it becomes a documented gap. "Flag, don't guess" (spec §0).
- DATA_DECISIONS_LOG.md append-only. Continue from Entry 71.
  Entry 71 = EVM coin builds: BNB + GLMR/MOVR + Sonic/S + BERA + XDC (built or gap per chain)
  Entry 72 = DOT/KSM deferral note + CELO balance-history probe
  Entry 73 = AVAX/NEAR/Cosmos probes
  Entry 74 = AAVE ch2 fix
  Entry 75 = session close-out (new λ count, new coin regression-ready count)
- No additional paid subscriptions. Etherscan Pro (existing) only.
- Do NOT sign up for anything (non-interactive session). If a free self-serve key is needed,
  document the exact URL and what Moazzam needs to do.
- Do NOT pay for Subscan Pro, AvaCloud paid tier, Pikespeak, Mintscan.
- PYTHONUTF8=1.
- Update 06_documentation/time_log.md.
- Write session log to 06_documentation/ai_conversations/session_028_*.md.
- Write 03_data/SESSION028_COIN_STAKING_REPORT.md.
- Commit and push at session end.

## Deliverables

1. Extended `phase1_channel1_pos_coins.py` or `_bucket2.py` with any newly built coin series
2. Updated `lambda_panel.csv` with new coin ch1 + AAVE ch2 fix
3. DATA_DECISIONS_LOG entries 71–75
4. `03_data/SESSION028_COIN_STAKING_REPORT.md` — per-chain: built / gate-open / gap
5. Gap register update: exact gate and Moazzam action for each open chain
   (e.g. "Subscan free key: sign up at pro.subscan.io; drop key in .api_keys.json under
   'subscan'; re-run the builder")
6. time_log.md updated; session_028 log written
7. Commit and push

## Not in scope this session

- ch2 for the ~500 breadth-only (non-lambda) tokens — defer.
- PQ/NVT_GL expansion — defer.
- Any Phase-3 / regression work — defer.
- EOS, ICP, APT — Entry 47 documents no source exists; do not re-check unless a new source
  is found in the Cosmos/alternative probe above.
- HBAR, SUI — engineering-intractable without a keyed indexer (Entry 45); defer.
- ALGO — structural gap confirmed (Entry 42); do not retry.

STOP at end of session or when all viable coin chains have been attempted. Report the gap
register with enough detail that Moazzam can action the open items (Subscan signup, etc.).
```
