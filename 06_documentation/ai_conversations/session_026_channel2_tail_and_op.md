# Session 026 — Channel-2 tail (3-channel creators) + OP delegation (block-windowed)

**Date:** 2026-07-01 · **Working dir:** C:\AFA_2027_QTM_Crypto · **Key:** Etherscan API Pro (200k/day)
**Decisions Log:** Entries 65–67 · **Report:** `03_data/SESSION026_TAIL_BUILD_REPORT.md`

Starting λ (session 025 close, Entry 64): **6,097 asset-months / 288 assets**, 0 three-channel.

## Objective
Two carried-forward Phase-2 items:
- **Task A — OP delegation:** finish the one deferred P2-2 item (Entry 62). OP (cmc 11840,
  Optimism, ERC20Votes) verified firing but its full DelegateVotesChanged history was too large
  to complete in session 025 (>80 min, killed). Block-windowed incremental fetch is the fix.
- **Task B — Channel-2 tail:** add ch2 (coin-age/HODL) to the >3,000-holder tokens deferred by
  the session-025 metadata filter — especially the tokens that already have ch1 and/or ch3, so
  ch2 turns them into 2-/3-channel assets (the depth the session-025 breadth expansion lacked).

## What was done

### Task A — OP delegation (`phase1_op_delegation.py`, NEW)
Root-caused the session-025 hang: the delegation builder binary-splits getLogs from block 0 to
~153M; the first calls span 100M+ blocks, which Optimism getLogs cannot serve in one shot →
60-second timeouts cascading = the >80 min. Two fixes in a dedicated OP script:
1. **Block-windowing** — never issue getLogs over a range larger than BLOCK_WINDOW (500,000);
   within a window that hits the 1000-log page cap, binary-split (shallow, no timeout).
2. **Streaming replay** — OP's DelegateVotesChanged history is *enormous* (the "46,974" in
   Entry 62 was just the first 60 calls; the real count is **351,186 events / 23,138 delegates
   by block 15M alone — only 10% of the range**, projecting to ~1.5–2M events). Storing the full
   event list is the ~400MB/1GB memory wall session 025 also hit. Instead each event is folded
   into a per-delegate running balance AS IT ARRIVES and the total is snapshotted at each
   month-end block; the raw log is discarded. Memory is bounded by delegate count (~130–440MB
   observed), not event count. Windows are fetched in increasing block order and getLogs returns
   logs in (block, logIndex) order → the stream is monotonic → the incremental replay is
   identical to the batch replay. Checkpoint is incremental (every 30 windows) and resumable.

**Timing decision (user-steered):** at the calibrated rate (~1.2s/call on Optimism, with some
connection resets retried), full OP completion projects to ~2–3.5 hours. OP is a **cross-check**
(role=crosscheck; it does NOT enter λ — OP stays on its Snapshot ch3_voting turnout per the
governance waterfall, Entry 57). Because Task B (Channel-2 → first 3-channel λ assets) is the
higher-value, λ-moving work and the two cannot run concurrently (shared 10 calls/s limit), the
user chose **Task B first, OP after**. OP was paused at block 15M (checkpoint resumable) and the
wall-clock redirected to Task B. **OP FINAL STATUS: COMPLETED** — 11,722,683 events / 245,439
delegates; delegated/circ median 7.98% (range 3.54–13.05%), role=crosscheck (NOT in λ; OP is in λ
via Snapshot ch3_voting). The serial resume STALLED at 68% on an Optimism ConnectionReset storm
(fresh-connection-per-call churn on the very active recent-blocks region — 810k events in the
first 2M blocks alone); fixed by adding the ch2 engine's pooled keep-alive Session + 8-way
concurrency + raise-not-swallow retry, finishing the last 32% cleanly in ~59 min (CPU fell from
~4,000 s of reset churn to near-idle).

### Task B — Channel-2 tail, 3-channel creators only (`phase1_channel2_panel.py`, extended)
Added a `WORKLIST` env: process an explicit priority-ordered cmc_id list (not smallest-first),
bypassing the HOLDER_MAX metadata-defer for the listed tokens (they are deliberately requested).

**Classification first (the key efficiency step, user-steered):** verified per token which
existing channels it has, so ch2 is fetched only where it creates the most value:
- **3-CHANNEL creators (have ch1 AND ch3v):** RPL(12k), FRAX(18k), CVX(31k), YFI(52k),
  CRV(100k), 1INCH(112k), SUSHI(127k), AAVE(200k), GMX(299k).
- **2-channel only (one channel):** DDX, ORBS, XAN, LQTY, CAKE, API3, PENDLE.

An initial run interleaved 2-channel tokens and hit **ORBS** — 9k holders but a *hidden giant*
(holder_count under-counts transfer volume; ORBS is a heavily-traded 2019 token, >2M transfers,
442MB, still going after ~40 min) for ZERO 3-channel value. Stopped and **restricted the build
to 3-channel creators only, smallest-first** (RPL done → FRAX → CVX → YFI → giants), with a
per-token memory heartbeat to catch any further hidden giant within ~5 min. This is the "no
wasted effort on 2-channel tokens" discipline.

**Built this session (screened HODL-6m = supply held >6mo by non-contract addresses / on-chain
supply; the session-025 denominator + contract-screen methodology, unchanged):**

| token | holders | transfers | getLogs | scr months | screened HODL-6m (range / median) | 3-channel months |
|-------|--------:|----------:|--------:|-----------:|-----------------------------------|-----------------:|
| RPL   | 12,253  | 690,529   | 2,165   | 57 | 0.0–22.1% / 17.4% | 28 |
| DDX (2-ch) | 2,969 | 42,367 | 143 | 32 | 0.0–62.9% / 49.2% | — |
| FRAX  | 17,726  | 1,310,744 | 3,967   | 54 | ~ / 10.9% | 52 |
| CVX   | 31,170  | 2,827,597 | 8,477   | 56 | ~ / 10.7% (last 21.3%) | 56 |
| YFI   | 52,242  | 2,152,448 | 14,916* | 70 | ~ / 53.1% (last 68.8%) | 29 |
| CRV/1INCH/SUSHI/AAVE | 100k–200k | (streaming) | | | | 21/41/35/60 |
| GMX   | 299,448 | deferred to fresh quota day | | | | 32 |

*YFI gl is cumulative-at-completion in the stream run. YFI median HODL-6m 53% is high but
economically legitimate (YFI's small-supply, famously long-term holder base — not degenerate;
it varies month-to-month). RPL/FRAX/CVX 10–17% match the RAD governance-token precedent.

### STREAMING + CONCURRENT engine (`phase1_channel2_stream.py`, NEW — the giant-token unlock)
The session-025 panel engine loads a token's ENTIRE Transfer history into RAM before replaying —
fine to ~2M transfers (FRAX 1.3M ≈ 460MB) but OOMs on the 100k+-holder giants (AAVE ~40M ≈
10GB, GMX ~60M ≈ 15GB; the "did not complete" wall) and is serial (~1.5 calls/s, far under the
Pro 10/s). New engine, **validated byte-identical** to the panel engine before use:
- **Streaming FIFO replay:** events fetched in block-order batches, folded into per-address FIFO
  lots AS THEY ARRIVE, month-end HODL snapshots taken when a month-end block is crossed, raw
  events discarded. Memory bounded by live-address lot state (CVX 2.8M transfers held in only
  ~96k lots; the old engine would hold 2.8M events). Empty-deque pruning (`PRUNE_EVERY`) drops
  sold-out addresses (correctness-preserving) to bound churn/dust-heavy giants (YFI/AAVE/GMX).
- **Concurrent windowed fetch:** ThreadPoolExecutor (8 workers) under a global ~9 calls/s token
  bucket, in block-ordered batches (each batch fully fetched + sorted before feeding the replay
  → the stream stays monotonic → identical to the batch replay). Thread-local pooled Session
  (HTTP keep-alive) — WITHOUT it, 8 workers × ~9 TLS handshakes/s burned ~6 CPU cores on crypto;
  with it the job is properly I/O-bound (near-idle CPU) at the full 9 calls/s.
- **Validation gates (both passed, 0 diffs):** (1) `--validate 2943` — streaming replay vs
  panel._replay on RPL's stored events, IDENTICAL (incl. with pruning forced every 50k events);
  (2) `--checkfetch 7228` — full concurrent-fetch + stream pipeline re-fetching DDX vs its stored
  serial checkpoint, transfers 42,367 = 42,367, max|screened diff| = 0.

### Intermediate λ (RPL+DDX+FRAX+CVX+YFI folded; CRV/1INCH/SUSHI/AAVE still fetching)
**FIRST 3-channel assets in the panel's history:** n_channels 1→5558 / 2→374 / **3→165**
(was 0). 3-channel assets: **RPL(28mo), YFI(29), FRAX(52), CVX(56)** — all
ch1_staking+ch2_holding+ch3_voting. 2+ channel share 7.1% → **8.8%**. CRV/1INCH/SUSHI/AAVE add
~157 more 3-channel asset-months + 4 more 3-channel assets when they land.

RPL screened HODL-6m median 17.4% (raw incl-contracts 61.8%; 22 LP/staking/treasury contracts
removed) — bounded and economically sensible, matching the RAD governance-token precedent.

## λ result (after `--aggregate` + `phase1_assemble_lambda.py`)
- **λ 6,097 → 6,021 observed asset-months / 288 → 282 assets.** The count dips because the
  contamination fix removed 6 spam-only dead tokens (their sole channel was a now-nulled
  contaminated ch2). This session's value is DEPTH + INTEGRITY, not breadth.
- **n_channels: 1 → 5,356 · 2 → 333 · 3 → 332** (was 5,662 / 435 / **0**).
- **First 3-channel assets (9):** CVX(56), FRAX(52), 1INCH(41), AAVE(38), SUSHI(35), GMX(32),
  YFI(29), RPL(28), CRV(21) = **332 three-channel asset-months** (all ch1_staking+ch2_holding+
  ch3_voting). **2+ channel share 7.1% → 11.0%.**
- Data-integrity: an address-poisoning spam / phantom-lot bug was caught (11 tokens) and fixed
  with a two-layer guard (per-event value cap VAL_CAP_MULT=100 + per-month exclusion CONTAM_MULT=
  100), re-validated byte-identical on RPL. AAVE's spam-contaminated 2024-08→2026-05 ch2 window is
  excluded (documented limitation; a per-token totalSupply cap would recover it — future work).

## Budget / method compliance
cmc_id joins only; screened HODL denominator = on-chain supply (not CMC circulating); assembler
z-score/equal-weight logic untouched (channel input only); OP delegation role=crosscheck (not in
λ); no additional paid subscriptions. getLogs budget well under 200k/day (wall-clock per token,
not the daily quota, is the binding constraint — the session-025 finding, reconfirmed).
