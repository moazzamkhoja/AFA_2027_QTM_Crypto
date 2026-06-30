# Session 024 status + Session 025 kickoff (PHASE 2 — paid sources)

## Where session 024 left λ
- **λ = 2,699 observed asset-months / 90 distinct assets, 2019-12 → 2026-05** (commit this session).
- Baseline in was 2,130 / 68 (session 023). Delta **+569 asset-months / +22 assets**, all from FREE
  sources on free chains.
- Decisions Log: **Entries 57–60.** Full account: `03_data/SESSION024_FREE_BUILD_REPORT.md`.

## What is DONE (free phase) — do not redo
- **Channel-3 on-chain delegation** (`ch3_delegation`): 21 net-new ERC20Votes tokens, 560 asset-months
  (`channel3_onchain_delegation.csv`, builder `phase1_channel3_onchain_delegation.py`). A DISTINCT
  sub-channel from Snapshot turnout; primary-only in λ (no governance double-count).
- **Channel-1 XAN** (`channel1_freebuild.csv`): cross-checked to live `lockedSupply()` at 0.0000%.
- **Channel-2 engine** proven (`phase1_channel2_holding.py`) + **budget measured** → free cap binds.
- VSL rejected (AKRO-pattern pause); NMR deferred; stkAAVE excluded (double-count). HEX/AKRO were
  session 023.

## PHASE 2 worklist (paid — requires explicit human purchase approval; do NOT pre-empt)

### P2-1 — Channel 2 panel-scale (the highest-value item, Entry 24/59)
The free getLogs cap binds (RAD mid-size = 700+ calls, did not complete; tail is 100–1000× worse).
Options to price: (a) a paid getLogs throughput tier / archive indexer for full Transfer history;
(b) a HODL-wave/coin-age API (Glassnode/CoinMetrics) if cheaper than reconstructing. PLUS a paid
**address-label feed** for CEX-EOA screening — without it raw HODL is dominated by contract/CEX
addresses (MET demo: 90.8% → 1.3% after contract screen). Pick a clean single-deployment token to
re-validate (MET's v2 migration muddied its 12m window).

### P2-2 — Etherscan Pro getLogs on BSC/Base/Avalanche (the 16 paid-gated candidates)
ALT, AWE, BAKE, BNX, CHEEL, EDG, ESPORTS, FORM, LINEA, MCT, MDX, OP, PONKE, TKO, ZORA, TNC — run the
session-022 contract-read + getLogs method once getLogs is unlocked on those chains.

### P2-3 — NMR proper Erasure treatment
Reconstruct net-outstanding staked NMR from the modern Numerai/Erasure contracts (multi-event
stake-lifecycle, burn-on-stake) with whatever aggregate or paid-archive anchor exists; ship only if
it can be cross-checked (the Entry-26 bar).

### P2-4 — Task D KAIA candidates
KSP (KlaySwap) and BORA — verify a token-level lock/vote via KAIA Klaytnscope/Blockscout getLogs and
build if clean. The other ~19 EVM-non-Etherscan tokens are wrapped/native-gas (out of token-scope).

### P2-5 — Task E non-EVM historical (paid indexers)
Solana (53 tokens; Helius/Triton archival for historical token-account ages), Tron, Cosmos, Neo —
Channel-2 coin-age is the realistic target but needs paid historical state. Channel-1/3 there are
gas-coin staking/gov (low token-side yield).

### P2-6 (optional) — empirical cross-check of the 10 Snapshot-overlap delegation tokens
GTC/ENS/UNI/COMP/SUSHI/STRK/MNT/RGT/KP3R/HFT: run `CROSSCHECK=all phase1_channel3_onchain_delegation.py`
(env gate already wired) to compare on-chain delegation vs Snapshot turnout. Validation only —
does not change λ (these stay on Snapshot turnout).

## Method rules carried forward
Free phase is DONE — Phase 2 is paid and needs human approval per item. cmc_id joins only; logs not
eth_call; Entry-26 cross-check bar for any Channel-1 build; append-only Decisions Log (next entry =
61); extend `phase1_assemble_lambda.py` channel inputs, don't change its z-score/equal-weight logic;
run the assembler with `PYTHONUTF8=1` (the `→` print crash was fixed this session).

## Known gotchas (session 024)
- getLogs paging from block 0 over the full range is the right method but the high-volume tail is
  slow/expensive — checkpoint per token (all builders here do).
- A transient `getblocknobytime`→None for the LAST month poisons the whole fetch range — `block_at`
  now retries and the builders fall back to a high block. Delete a poisoned per-token checkpoint to
  re-fetch.
- DDX/XAN show ratio>1 (Entry-49: CMC circulating excludes locked/delegated supply) — expected,
  flagged, λ uses rank.
