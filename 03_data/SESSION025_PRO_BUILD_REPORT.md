# Session 025 — Etherscan Pro BUILD report (Phase 2: paid getLogs)

**Date:** 2026-06-30 · **Decisions Log:** Entries 61–64 · Parallel to `SESSION024_FREE_BUILD_REPORT.md`.

Moazzam purchased **Etherscan API Pro** (Standard, $199/mo, 200k calls/day, 10/s, all chains;
activated 2026-06-30; Entry 61). This session is the payoff: (A) the 16 BSC/Base/Optimism/Linea
paid-gated Channel-1/3 candidates (P2-2), and (B) Channel-2 (holding duration / coin-age) at
panel scale — the Entry-24 "single highest-value addition" that the free getLogs cap blocked.

**Pro verified before any build:** `getLogs` returns real data on BSC (56), Base (8453),
Optimism (10), Linea (59144), Avalanche (43114) — all "Free API access not supported" on the
free tier. Confirmed, not assumed.

---

## Task A — P2-2: the 16 paid-gated tokens (Entry 62)

Mechanism VERIFIED on-chain first (`phase1_p2p2_probe.py`) before any build (the AKRO/Entry-55
discipline). Verdict table:

| Token | cmc_id | chain | candidate | events (probe/full) | verdict | reason |
|-------|--------|-------|-----------|--------|---------|--------|
| AWE   | 4006  | Base     | Ch3 deleg | 208,687 | **BUILD** | fires; delegated/circ = **15.25%** (material) |
| CHEEL | 23054 | BSC      | Ch3 deleg | 251     | **BUILD** | fires; ~0% ratio (low activation) |
| FORM  | 23635 | BSC      | Ch3 deleg | 218     | **BUILD** | fires; ~0% ratio |
| LINEA | 27657 | Linea    | Ch3 deleg | 7       | **BUILD** | fires; ~0% ratio |
| ZORA  | 35931 | Base     | Ch3 deleg | 3,311   | **BUILD** | fires; ~0% ratio |
| ALT   | 10897 | BSC      | Ch3 deleg | 2       | EXCLUDE | 2 events net to 0 delegated → no ratio (CYBER pattern) |
| OP    | 11840 | Optimism | Ch3 deleg | 46,974+ | **DEFER** | verified firing but full history too large to complete (>80min/400MB, killed) |
| BAKE  | 7064  | BSC      | Ch3 deleg | 0       | DORMANT | ERC20Votes ABI present, event never fired |
| BNX   | 9891  | BSC      | Ch3 deleg | 0       | DORMANT | " |
| EDG   | 5274  | BSC      | Ch3 deleg | 0       | DORMANT | " |
| ESPORTS|37414 | BSC      | Ch3 deleg | 0       | DORMANT | " |
| MCT   | 16946 | BSC      | Ch3 deleg | 0       | DORMANT | " |
| MDX   | 8335  | BSC      | Ch3 deleg | 0       | DORMANT | " |
| PONKE | 29150 | Base     | Ch3 deleg | 0       | DORMANT | " |
| TKO   | 9020  | BSC      | Ch3 deleg | 0       | DORMANT | " |
| TNC   | 5524  | BSC      | Ch1 lock  | n/a     | REJECT  | `Locked(address)` bare/no-amount → fails Entry-26 (AKRO/VSL pattern) |

**P2-2 net λ contribution:** `ch3_delegation` primary set **560 asset-months / 21 assets → 627 / 26**
(+67 / +5). Only AWE is economically material; CHEEL/FORM/LINEA/ZORA enter at ~0% (genuine
low governance-activation, z-scored on rank, consistent with the existing BLAST/BLUR/EIGEN ~0%
precedent). OP is the single carried-forward item (verified, deferred on throughput).
A `DELEG_CAP` guard (default 6000 getLogs/token) was added to the delegation builder so a future
giant defers gracefully instead of hanging.

---

## Task B — Channel 2 (holding duration / coin-age) at panel scale (Entries 63–64)

### Engine + the denominator fix (the key methodology change this session)
`phase1_channel2_panel.py` reuses the proven session-024 FIFO coin-age functions and adds:
resumable per-token checkpoints (now storing the raw events so the metric is re-computable
without re-fetching), a per-token getLogs cap (`PER_TOKEN_CAP`; the high-volume tail defers
rather than building a wrong partial series), an active daily-budget guard, and an all-month
contract screen (`eth_getCode` over the union of each month's top >6m holders; a contract is
a contract in every month, so one classification pass cleans the whole series — fixing the
session-024 last-month-only screen).

**DENOMINATOR FIX:** the session-024 prototype divided on-chain coin-age supply by **CMC
circulating supply**, which produced HODL shares **>100%** (RAD raw 148–398%) because CMC
circulating *excludes* locked/treasury/vested tokens (the Entry-49 pattern) while the coin-age
numerator counts all on-chain tokens. The fix divides by **on-chain supply** (sum of all live
lots at the month-end block) — the supply whose age the channel actually measures — making the
share a proper fraction in [0,1].

### B3 — clean-token validation (RAD; AAVE/CRV swapped out)
AAVE/CRV were the kickoff's suggested validation tokens but their multi-year Transfer histories
are 1M+ events (the same throughput wall as OP) and did not complete; **RAD** (Radicle, 397,423
transfers, single deployment, clean governance token) was used instead. Post-fix series:

| metric | range | latest (2026-05) |
|--------|-------|------------------|
| raw HODL-6m (incl. contracts) | 59.8–85.7% | 67.3% |
| **screened HODL-6m (EOA only)** | **11.2–27.1%** | **22.0%** |
| HODL-12m | 56.6–78.0% | 57.4% |

Bounded, economically reasonable (not 95%+ or 0.1%): ~1/5 of RAD's on-chain supply is held >6mo
by non-contract addresses. **Gate passed → wired into λ.** RAD cost 1,357 getLogs + 80
eth_getCode ≈ 1,437 calls / ~15 min wall — the wall-clock per token, not the daily quota, is the
binding constraint.

### B2 — size-driven batch (metadata-first, not hit-and-trial)
The first cut fetched each token until a per-token call cap, then deferred — wasting ~cap calls
per giant just to *discover* it was too big. Replaced with a **metadata pre-pass**
(`phase1_channel2_sizeprobe.py`): Etherscan Pro `tokenholdercount` = **1 call/token** gives a
holder count that is a monotone proxy for Transfer-log volume (calibration: MET 748 holders /
24.6k transfers / 79 getLogs; RAD 7,785 / 397k / 1,357; XAN 12,963 / giant → ~30-50 transfers
per holder). All 793 free-chain tokens sized in one ~793-call pass (`_channel2_sizes.csv`).
Size distribution: **113 tokens ≤1,000 holders (~≤80 getLogs each), 165 ≤2,000, 215 ≤3,000,
295 ≤5,000, 404 ≤10,000.** The panel builder now (a) processes SMALLEST-FIRST, (b) DEFERS BY
METADATA any token above `HOLDER_MAX` (skipped without fetching — zero wasted calls), and (c)
caches month-end block numbers once per chain (not once per token-month). This makes the build
deterministic and budget-predictable rather than trial-and-error.

**Result (HOLDER_MAX=3,000):** **207 tokens completed** (197 with a screened HODL series;
the rest 0-transfer / pre-history-only), 5,064 asset-month rows, **0 network failures** on the
clean re-run. The ~586 tokens > 3,000 holders were deferred by metadata (skipped without
fetching) as the resumable worklist. Data quality is strong: **median screened HODL-6m =
40.6%**, 80.6% of token-months < 95%, and only **2 of 197 assets** are degenerate (≈100% every
month = dead/illiquid). The occasional 100% months are token-specific early/illiquid periods,
not systemic — the assembler's cross-sectional z-score (std>0, n≥2) drops degenerate cross-
sections.

### Data-integrity incident (overnight network outage) — found & fixed
During an unattended overnight run the machine's network dropped intermittently. The engine's
`api()` swallowed the DNS failure into an EMPTY result, and `fetch_capped` treated that empty
getLogs range as "0 transfers here" — **silently dropping a block range = a corrupted coin-age
series**. Fixed with a panel-local `_robust_getlogs` that RAISES `NetworkError` on a dropped
connection (so the token aborts+retries instead of checkpointing a partial history), a
`month_block` that no longer caches failed (None) lookups, and a network-failure backoff +
circuit-breaker in `main()`. All 65 possibly-affected overnight checkpoints were **deleted and
re-fetched** with the robust code; the clean re-run logged 0 network failures across all 207
tokens. (RAD, validated during a stable session, was kept.) Lesson: a swallowed network error
is worse than a crash — it corrupts silently.

### Named limitation (carried, documented in the output `cex_screened` flag)
CEX custodial **EOA** wallets are NOT screened (no free address-label feed). Contract addresses
(LP/treasury/staking/bridge) ARE removed via `eth_getCode`. Residual bias: long-held supply
sitting in a CEX omnibus EOA is counted as holder conviction. A paid label feed is the only fix
and is explicitly out of scope (no additional subscriptions).

---

## Assembled λ panel (after) — Entry 64
- **λ 2,699 → 6,097 observed asset-months; 90 → 288 distinct assets** (+3,398 / +198). Month
  range 2016-12 → 2026-05 (older Transfer histories reach further back).
- **Sources of the delta:** `ch2_holding` 3,413 asset-months / 197 assets (Entry 63) + P2-2
  `ch3_delegation` +67 / +5 (AWE/CHEEL/FORM/LINEA/ZORA, Entry 62).
- **Channel coverage (asset-months):** ch2_holding 3,331 single + ch1_staking 937 + ch3_voting
  834 + ch3_delegation 560 + (ch1+ch3_voting) 354 + (ch2+ch3_delegation) 67 + (ch2+ch3_voting)
  14. ch2_holding is standardizable in 114 monthly cross-sections — the most of any channel.
- **n_channels:** 5,662 single-channel, 435 two-channel, 0 three-channel. By class: token 128,
  other 151, coin 9.
- **Depth (the headline metric), honestly:** 2-channel asset-months **354 → 435 (+81)**, but the
  2-channel SHARE fell **13.1% → 7.1%** because breadth tripled with single-channel ch2 assets.
  Channel 2 massively WIDENED the panel (mostly new small/mid tokens) yet added a 2nd channel to
  only 4 already-in-λ assets — the large in-λ governance/staking tokens are > 3,000 holders and
  were metadata-deferred. **Lifting depth (toward 3-channel assets) is exactly what the deferred
  > 3,000-holder tail run delivers next** — those are the tokens that already have ch1/ch3.

## Budget accounting
- Sizeprobe: **793 `tokenholdercount` calls** (all 793 free-chain tokens sized in one pass).
- Channel-2 build: **~15–20k getLogs + eth_getCode calls** for 207 tokens (~59 getLogs/token
  average, thanks to smallest-first + the per-chain month-block cache).
- P2-2 delegation (AWE 208k events, etc.) + RAD validation: a few thousand more.
- **Total well under the 200,000/day Pro quota.** The binding constraint this session was
  per-token **wall-clock** (fetching a full Transfer history is minutes for a real-volume token),
  NOT the daily call quota — which is why the > 3,000-holder tail is deferred, not the budget.

## Resumable worklist (next session)
1. **Channel-2 tail:** the ~586 tokens > 3,000 holders (`_channel2_sizes.csv`), especially the
   large in-λ governance/staking tokens (UNI/COMP/AAVE/CRV/ENS/… and DDX) — a dedicated
   higher-cap / block-windowed run gives them ch2 and creates the first 3-channel assets.
2. **OP delegation** (verified firing, deferred on volume) — block-windowed incremental fetch.
3. Per-token checkpoints store raw events → `phase1_channel2_panel.py --aggregate --recompute`
   re-derives the metric with no re-fetch if the methodology changes.

## Method compliance
Mechanism-verified-before-build (Entry 55); no partial/degenerate series shipped; cmc_id joins
only; logs-not-eth_call; Entry-26 bar applied to TNC (rejected); assembler z-score/equal-weight
logic untouched (only a channel input added); Pro key only, no other paid tier. Decisions Log
appended 61–64 (append-only).
