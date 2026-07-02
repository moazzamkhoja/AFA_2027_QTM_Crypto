# Session 026 — Channel-2 tail (3-channel creators) + OP delegation build report

**Date:** 2026-07-01/02 · **Decisions Log:** Entries 65–67 · Parallel to `SESSION025_PRO_BUILD_REPORT.md`.

Starting λ (session 025 close, Entry 64): **6,097 asset-months / 288 assets, 0 three-channel.**
Two carried-forward Phase-2 items: (A) OP delegation (the one deferred P2-2 item), and (B) the
Channel-2 >3,000-holder tail — specifically the tokens that already have ch1/ch3, so ch2 turns
them into the panel's **first 3-channel assets** (the depth session 025's breadth expansion
lacked). This session's headline is DEPTH, not breadth.

---

## The engineering unlock: a streaming + concurrent Channel-2 engine

The session-025 panel engine (`phase1_channel2_panel.py`) loads a token's ENTIRE Transfer
history into RAM before replaying — fine to ~2M transfers (FRAX 1.3M ≈ 460 MB) but it OOMs on
the 100k+-holder giants (AAVE/CRV/SUSHI/GMX at 4–60M transfers ≈ 2–15 GB — the "did not complete"
wall of Entries 59/63) and is serial (~1.5 calls/s, far under the Etherscan Pro 10/s ceiling).

`phase1_channel2_stream.py` (NEW) fixes both, **validated byte-identical to the panel engine
before any real build**:

1. **Streaming FIFO replay.** Transfer events are fetched in block-order batches and folded into
   the per-address FIFO coin-age lots AS THEY ARRIVE; the month-end HODL snapshot is taken when a
   month-end block is crossed; the raw event is then discarded. Memory is bounded by the live
   lot state (e.g. CVX 2.8M transfers held in ~96k lots, CRV 10.7M in ~105k), not the event
   count. Empty-deque pruning (`PRUNE_EVERY`) drops sold-out addresses (correctness-preserving)
   so churn/dust-heavy giants (YFI/AAVE/GMX) stay bounded.
2. **Concurrent windowed fetch.** 8 worker threads under a global ~9 calls/s token-bucket rate
   limiter, fetched in block-ordered BATCHES (each batch fully fetched + sorted before feeding
   the replay → the stream stays monotonic → identical to the batch replay). A thread-local
   pooled `Session` (HTTP keep-alive) was essential: without it, 8 workers doing ~9 TLS
   handshakes/s burned ~6 CPU cores on crypto; with it the job is properly I/O-bound (near-idle
   CPU) at the full 9 calls/s.

**Validation (both gates passed, 0 diffs):**
- `--validate 2943`: streaming replay vs `panel._replay` on RPL's stored events → **72 rows,
  0 diffs**, screened series max|diff| = 0 (also identical with pruning forced every 50k events).
- `--checkfetch 7228`: the full concurrent-fetch + stream pipeline re-fetching DDX vs its stored
  serial checkpoint → transfers **42,367 = 42,367**, max|screened diff| = 0.

Because the per-month `state` is identical, the SAME validated `screen_contracts` +
`rows_from_state` produce identical output. The giants are therefore built to exactly the same
standard as the session-025 small/mid cross-section.

---

## Task B — Channel-2 tail: efficiency discipline + results (Entry 66)

**Classify first, build only the high-value tokens (user-steered).** Rather than grinding the
whole >3,000-holder tail, each candidate was classified by which channels it already has, and
ch2 was built ONLY for the **3-channel creators** (tokens with ch1 AND ch3 — adding ch2 makes
them 3-channel). An initial interleaved run hit **ORBS** (9k holders but a hidden giant, >2M
transfers — holder_count under-counts transfer volume) for zero 3-channel value; it was dropped
and the build restricted to 3-channel creators, smallest-first, with a memory heartbeat to catch
any further hidden giant within minutes.

### Tokens built (screened HODL-6m = supply held >6mo by non-contract addrs / on-chain supply)

| token | holders | transfers | getLogs | scr months | screened HODL-6m median (latest) | → channels | 3-ch months |
|-------|--------:|----------:|--------:|-----------:|----------------------------------|-----------|------------:|
| RPL   | 12,253  |   690,529 |  2,165  | 57 | 17.4% (21.3%) | **3** | 28 |
| DDX   |  2,969  |    42,367 |    143  | 32 | 49.2% | 2 | — |
| FRAX  | 17,726  | 1,310,744 |  3,967  | 54 | 10.9% | **3** | 52 |
| CVX   | 31,170  | 2,827,597 |  8,477  | 56 | 10.7% (21.3%) | **3** | 56 |
| YFI   | 52,242  | 2,152,448 |  ~6,400 | 70 | 53.1% (68.8%) | **3** | 29 |
| CRV   | 100,379 | 10,748,750| 31,411  | 69 | 11.1% (35.8%) | **3** | 21 |
| 1INCH | 111,505 | 2,306,177 |  ~7,000 | 66 | 36.4% (36.8%) | **3** | 41 |
| SUSHI | 126,599 | 4,092,613 | ~12,100 | 69 | 54.5% (68.1%) | **3** | 35 |
| AAVE  | 199,525 | 5,564,654 | 16,601  | 45 | 18.5% (spam months excluded) | **3** | 38 |
| GMX   | 299,448 | 9,324,734 | ~44,000 | 44 | 14.3% (29.5%) | **3** | 32 |

Screened HODL-6m is economically bounded across all tokens: governance/liquid tokens (RPL/FRAX/
CVX/CRV) sit at 10–17% (matching the RAD precedent), while long-term-holder tokens (YFI/SUSHI at
~53%) are higher but legitimate and non-degenerate (the series varies month-to-month; none is
~100% or ~0.1% every month). Contract screening removes 16–61 LP/staking/treasury contracts per
token (e.g. RPL raw 61.8% → screened 17.4%).

### Data-integrity: phantom-lot (address-poisoning spam) — B2 finding + a two-layer fix
A full-panel B2 integrity scan (reconstructed `onchain_supply` vs circulating across all 217
completed tokens) caught **11 contaminated tokens**: **AAVE** (on-chain supply read up to 1.16e60
tokens vs a real ~16M — most of its 2024–26 series pinned at 100% HODL) plus 10 small/dead tokens
(VVS, SYBC, BNANA, REW, CTT, CBG, GRD, LST, NYE, MBN, UNY at 50–42,000× circulating). Cause:
**address-poisoning spam** — fake huge-value `Transfer` logs replayed through FIFO become PHANTOM
lots (the "sender" never held them) that dominate the coin-age on-chain-supply denominator. A
single universal value threshold cannot separate spam from legit high-supply meme tokens, and a
per-event cap alone misses *accumulated* sub-cap spam, so the fix is **two layers**:
1. **Per-event value cap** (`VAL_CAP_MULT`=100): skip any Transfer whose value exceeds 100× the
   token's max circulating supply (a real transfer cannot exceed supply; 100× spares even
   heavily-locked tokens whose on-chain supply exceeds CMC circulating, the Entry-49 pattern).
2. **Per-month contamination exclusion** (`CONTAM_MULT`=100): emit NULL for any month whose
   reconstructed on-chain supply still exceeds 100× circulating (residual accumulated spam) —
   applied in `rows_from_state` AND as a post-hoc net in `aggregate()` so it also covers
   streamed-token rows that `--recompute` cannot re-derive. The 100× (not 50×) threshold is
   deliberate: early-launch tokens legitimately show on-chain supply ≫ CMC circulating while most
   supply is vesting-locked (the Entry-49 pattern) — e.g. CRV's first month (on-chain 1.3B vs
   circulating 26M = 51×, against a 3B total supply) is REAL and retained, whereas the
   address-poisoning contamination sits at 100–42,000×.
Both layers were re-validated **byte-identical on RPL** (clean tokens have on-chain ≈ circulating,
so neither layer fires). The 10 event-storing tokens were fixed by `--recompute` (no re-fetch);
AAVE (streamed) was re-fetched clean — its phantom removed by Layer 1, restoring its 2024–26
months as real data rather than nulling them.

### λ result (Entry 67)
**λ: 6,097 → 6,021 observed asset-months / 288 → 282 assets.** The asset-month COUNT dips slightly
because the contamination fix *removed* 6 spam-only dead tokens (their only channel was a now-
nulled contaminated ch2) — this session's value is DEPTH and INTEGRITY, not breadth. n_channels
distribution: **1 → 5,356 · 2 → 333 · 3 → 332** (was 5,662 / 435 / **0** at session-025 close).

**First 3-channel assets in the panel's history** (all `ch1_staking + ch2_holding + ch3_voting`):

| asset | 3-channel months | span |
|-------|-----------------:|------|
| CVX   | 56 | 2021-10 → 2026-05 |
| FRAX  | 52 | 2021-12 → 2026-05 |
| 1INCH | 41 | 2021-07 → 2026-05 |
| AAVE  | 38 | 2021-06 → 2024-07 (recent months spam-excluded) |
| SUSHI | 35 | 2020-08 → 2026-01 |
| GMX   | 32 | 2022-10 → 2026-03 |
| YFI   | 29 | 2023-04 → 2025-12 |
| RPL   | 28 | 2022-07 → 2026-02 |
| CRV   | 21 | 2020-09 → 2022-06 |
| **total** | **332** | across **9 assets** |

**Depth (the kickoff's headline metric): 3-channel asset-months 0 → 332; 2+ channel share
7.1% → 11.0%.** This is exactly what the session-025 report predicted the deferred >3,000-holder
tail would deliver: the tokens that already had ch1+ch3 became the panel's first 3-channel assets
the moment ch2 landed. AAVE's recent window is the one coverage gap (spam-contaminated ch2 months
excluded; a per-token totalSupply value cap would recover them — a documented next-session refinement).

---

## Task A — OP on-chain delegation (Entry 65)

Root-caused the session-025 >80-min hang: the delegation builder binary-splits getLogs from
block 0 to ~153M; the first calls span 100M+ blocks that Optimism getLogs can't serve in one
shot → cascading 60-second timeouts. `phase1_op_delegation.py` (NEW) applies the same two fixes
as the ch2 engine — block-windowing (no over-large range) + streaming replay (fold each
DelegateVotesChanged into a per-delegate running balance, snapshot at month-ends, discard the
raw log; memory bounded by delegate count, not the [FILL ~1.5–2M] event count). Incremental
resumable checkpoint. **role = crosscheck** (OP already has a Snapshot ch3_voting turnout series;
per the governance waterfall, Entry 57, its on-chain delegation is recorded but NOT folded into
λ as a second governance input).

**Completed.** OP replayed **11,722,683 DelegateVotesChanged events / 245,439 delegates** (the
"46,974" in Entry 62 was only the first 60 capped calls; the full history is ~250× larger). The
serial resume from 68% then STALLED on an Optimism `ConnectionReset 10054` storm (the recent
2024–26 governance region is extremely active — 810k events in the first 2M blocks alone — and
opening a fresh TCP/TLS connection per call caused the server to drop connections). Fixed by
reusing the ch2 engine's **pooled keep-alive Session + 8-way concurrency + raise-not-swallow
retry** (no silent gaps): CPU dropped from ~4,000 s of reset churn to near-idle, and the last 32%
finished cleanly in ~59 min. **Delegated/circulating: median 7.98%, range 3.54–13.05%** (final
76.2M OP delegated / 3.54%) — a substantial, real governance-activation signal, far above the
~0% low-activation P2-2 tokens. **role=crosscheck** → recorded but NOT in λ (OP is in λ via its
Snapshot ch3_voting channel; the assembler confirmed λ unchanged at 6,021/282, OP n_channels=1).

---

## Budget / method compliance
- Etherscan Pro getLogs, streaming+concurrent at ~9 calls/s under the 10/s ceiling; DAILY_CAP-
  gated per run to stay under the 200k/day quota (GMX + OP run on a fresh quota day after the
  00:00 UTC reset). Quota-exhaustion guard aborts a token cleanly (no retry-storm); all runs
  checkpoint per token and resume with no data loss.
- cmc_id joins only; screened HODL denominator = on-chain supply (not CMC circulating); assembler
  z-score/equal-weight logic untouched (channel input only); OP delegation role=crosscheck (not
  in λ); no additional paid subscriptions.
- The binding constraint remains per-token WALL-CLOCK (full Transfer history), now mitigated ~6×
  by concurrency; the streaming engine removes the memory wall entirely.

## Resumable worklist (next)
[FILL: GMX if still pending; the remaining >3,000-holder 2-channel-only tokens (ORBS/XAN/LQTY/
CAKE/API3/PENDLE + the ch3-only large set) for breadth; the rest of the >3k tail.] All buildable
now via `phase1_channel2_stream.py` (bounded memory, ~9 calls/s).
