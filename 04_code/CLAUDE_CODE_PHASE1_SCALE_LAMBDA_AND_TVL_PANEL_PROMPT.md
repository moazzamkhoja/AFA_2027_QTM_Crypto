# Claude Code Kickoff Prompt — Scale λ Coverage + Build a Real TVL Panel

Paste everything below the line into a new Claude Code session with working directory
`C:\AFA_2027_QTM_Crypto`.

---

You're working in the AFA 2027 QTM Crypto research repo (`github.com/moazzamkhoja/AFA_2027_QTM_Crypto`).

## Step 0 — Repo hygiene check (do this before anything else)

A prior session left a stale `.git\index.lock` and the local working copies of
`04_code\DATA_DECISIONS_LOG.md` / `06_documentation\time_log.md` had silently fallen behind
`HEAD` (Entries 33–39 and the last several time-log rows were committed and pushed, but missing
from the local files — diagnosed and fixed in Cowork as Decisions Log Entry 40; see that entry
for the full account). Before touching any data:

1. Confirm no git process is actually running on this machine (check Task Manager / any open
   terminal running `git`), then run `git status`. If you see `.git\index.lock` and no process
   is running, delete it.
2. Run `git status` again. If every tracked file shows as simultaneously staged-deleted and
   untracked, the index itself is stale — run `git add -A` (this rebuilds the index from the
   working tree; it does **not** delete anything, since the files are already present on disk)
   and confirm `git status` afterward shows either a clean tree or a small, sensible diff. If
   `git add -A` instead produces a huge, every-file-changed diff, stop and report it — don't
   commit blindly.
3. Read `04_code/DATA_DECISIONS_LOG.md` in full and confirm live what the actual last entry
   number is (it should be 40, per Entry 40 itself, but verify — don't trust this prompt's
   number). Do the same for the last session number in `06_documentation/ai_conversations/`
   (should be 018) and the last row of `06_documentation/time_log.md`. This project has twice
   now had a kickoff prompt state a stale next-number; always re-derive it live.

## Required reading (in full)

1. `04_code/DATA_SPECIFICATION.md` — Section 3 (λ: all three channels, including 3.2's
   acknowledgment that holding-duration is the hardest to source), Section 2.5 (per-asset
   source map: chain explorer per native chain, Snapshot/Tally/Boardroom/DeepDAO for voting),
   Section 4.1–4.2 (TVL's role as a *denominator*, not a PQ proxy).
2. `04_code/DATA_DECISIONS_LOG.md` — Entries 21 (live free-access audit methodology — the
   template to repeat for PoS coins below), 22 (DeFiLlama as a registry/address-book only, never
   the λ measurement itself), 23 (ETH native staking via beacon deposit-contract logs), 24
   (Channel 2 holding-duration — still NOT BUILT, still out of scope this session), 25 (Channel
   3: Snapshot GraphQL + the curated space map + the token-weight guard, and the explicit
   "not on Snapshot" gap list), 26 (Channel 1: the curated EVM vote-escrow set and *why* veBAL
   and SNX were deliberately excluded, not silently proxied), 27 (the z-score/equal-weight/
   ≥2-asset-standardizability assembly rule — unchanged this session), 30 (TVL is a stock, not a
   PQ flow — still true; this session uses TVL only as a valuation-multiple denominator, never as
   a PQ substitute), 40 (this session's own framing and the repo-hygiene incident from Step 0).
3. `03_data/phase1/asset_onchain_identity.csv` and the script that built it,
   `04_code/phase1_build_identity_map.py` — the authoritative `cmc_id → dl_slug` /
   `token_address` / `snapshot_space` registry. Re-derive the current counts live (don't trust
   numbers below) — as of 2026-06-26: 127/448 tokens have a `dl_slug` match, 123/448 have
   `has_address=True`, 29/448 have `has_snapshot=True` (auto-matched only).
4. `03_data/phase1/snapshot_space_map.csv` (the broader, curated 56/57-space map — 56 spaces
   covering 55 of the 448 tokens in `channel3_voting.csv`, wider than the 29 auto-matched above)
   and `04_code/phase1_channel3_voting.py`.
5. `04_code/phase1_channel1_evm_locks.py` and `04_code/phase1_channel1_eth_staking.py` — the
   existing, working event-log-reconstruction method (Etherscan `getLogs`) for Channel 1. The
   current curated EVM vote-escrow set is 6 tokens: veCRV, vlCVX, veFXS, xSUSHI, stkAAVE, veYFI.
6. `04_code/phase1_assemble_lambda.py` — the channel-combination logic. **Do not change the
   z-scoring / standardizability / equal-weight logic.** This session only widens the channel
   *input* files (`channel1_*.csv`, `channel3_voting.csv`, and a new `channel1_pos_coins.csv` —
   see Part A.3); the assembly script should pick up wider inputs automatically since it globs
   `channel1_*.csv`.
7. `04_code/phase2c_defillama_metadata.py` — specifically `check_tvl()` (currently fetches
   `api.llama.fi/protocol/{slug}`'s full `tvl[]` series and discards everything except
   presence/range/last-value). This session turns that into a real panel write — see Part B.

## Funding / cost context (same standing rule as every prior session)

DeFiLlama's TVL data and Snapshot's GraphQL API are free and keyless. Etherscan V2 requires the
existing free API key already stored gitignored at `04_code/.api_keys.json` ("AFA Paper" key,
~60 EVM chains via `chainid`) — free tier only, no archive-state access (Entry 21: historical
`eth_call`/`balanceOf` silently returns latest-state, not historical state; only `getLogs` gives
genuine point-in-time data). **Do not sign up for, key into, or use any paid tier of any
service this session — DeFiLlama Pro, Etherscan Pro/archive, beaconcha.in, Boardroom, Tally, or
anything else — under any circumstance.** If a real source turns out to be paywalled, log it as
a gap and stop there; do not work around it by paying. Moazzam handles any purchase decision
himself, after reviewing evidence, same as the standing rule for Dune and Artemis.

## Scope boundary — read this twice

This session is **λ scale-up + a real TVL panel for tokens. Nothing else.**

- **Do not build PQ for coins.** Coin PQ sourcing (currently 58/633 with real data) is
  explicitly deferred to a separate, later, explicitly-authorized session. If you notice a
  promising PQ-for-coins lead while working on λ, write it down in the deliverable report as a
  flagged observation — do not chase it or build it this session.
- **Do not touch Channel 2 (holding duration).** Still a documented gap (Entry 24). Out of
  scope.
- **Do not re-derive or change the λ assembly logic** in `phase1_assemble_lambda.py` — only add
  channel inputs.
- Join everything on `cmc_id`, never `symbol` (Entry 25's veBAL/SNX exclusions and Entry 39's
  NVT/nerve, VELO/velodrome symbol collisions are exactly the failure mode this guards against).

## Part A — Scale λ coverage

### A.1 — Token Channel 1 (staking/locking): widen the curated EVM vote-escrow/staking set

The current set (6 tokens: CRV, CVX, FXS, SUSHI, AAVE, YFI) was built by individually verifying,
per protocol, that the escrow-balance-equals-locked-supply identity holds cleanly (Entry 26) —
explicitly excluding protocols like veBAL (locks an 80/20 BPT, not BAL) and SNX (a C-ratio
system, not a lock) **by design**. Using the *same individual-verification standard* (not
broad automated matching), check the other DeFiLlama-matched tokens (`dl_slug` non-null,
`has_address=True`, ideally cross-referenced against DeFiLlama's `*-staking`/`*-vesting`
chainTvl buckets in the `/protocol/{slug}` payload, which Entry 21 already confirmed exist) for
additional EVM tokens where a vote-escrow or staking-lock contract cleanly equals locked supply
of *that* token. Plausible candidates to check (verify each individually — do not assume any of
these work without checking): GMX (escrowed GMX), RPL (Rocket Pool), COMP, MKR, BAL itself (not
veBAL), PENDLE (vependle), LQTY, RUNE, ANGLE, 1INCH. For each one added, use the same
`getLogs`-based event-log reconstruction already proven for the existing 6 — don't invent a new
method. For each one checked and rejected, write down why (same honesty standard as the
veBAL/SNX exclusions).

### A.2 — Token Channel 3 (voting): widen past the current 55-asset build

`snapshot_space_map.csv` has 56/57 curated spaces; `channel3_voting.csv` covers 55 of the 448
tokens. Two concrete widening paths:

- Cross-check `asset_onchain_identity.csv`'s `governanceID` field (DeFiLlama's own
  auto-matched Snapshot space, currently only surfaced for 29 tokens) against the full
  127-token `dl_slug`-matched set for any space not yet in the curated map, and add it if a
  direct lookup against Snapshot's GraphQL API (`hub.snapshot.org/graphql`) confirms it's a real,
  active space.
- Entry 25 documented a specific "not on Snapshot, on-chain governance only" gap list: MKR,
  LQTY, PENDLE, RUNE, PERP, WLD, ONDO, ENA. For any of these that are EVM-based with a
  Governor-style on-chain voting contract, attempt on-chain `VoteCast` event-log reconstruction
  (the same `getLogs` method already used for Channel 1, applied to a different event signature)
  rather than Snapshot. Verify each protocol's actual governance contract address and ABI before
  assuming Governor Bravo compatibility — don't guess a log signature.

### A.3 — Coin Channel 1 (staking/locking): live source-verification pass for PoS coins

Today only ETH (1 of 633 coins) has any λ-channel data. Before building anything, do an
Entry-21-style **live** free-access audit (not assumed from general knowledge) for the
highest-market-cap PoS/staking coins in the 633-coin roster. Derive your own candidate list from
`classification_table.csv` (coins with a known PoS/DPoS/NPoS consensus mechanism) rather than
taking any example list at face value — but for reference, chains worth checking first: SOL,
ADA, DOT, ATOM, AVAX, NEAR, ALGO, TRX, XTZ, EOS, ICP, KSM, CELO, KAVA, HBAR, INJ, SEI, SUI, APT.
For each chain, check whether its own free, keyless block explorer or API publishes a
staking-ratio / bonded-supply time series (e.g. a chain-native explorer's stats endpoint —
verify the actual current endpoint and access tier live, the same discipline Entry 21 applied to
beaconcha.in/Boardroom and found them now paywalled). Build a `channel1_pos_coins.csv` (same
shape as the existing `channel1_*.csv` files: `cmc_id, month_end, staking_ratio`) for whatever is
genuinely free and historical; for everything else, log it as a documented gap with the specific
reason (paywalled, current-state-only, no public API at all) — same standard as Entry 21/24.
**Do not guess a value or interpolate a current ratio backward in time.**

## Part B — Build a real, persistent TVL panel (tokens)

`check_tvl()` in `phase2c_defillama_metadata.py` already calls `api.llama.fi/protocol/{slug}`
and receives the full `tvl` array (`[{date: unix_ts, totalLiquidityUSD: float}, ...]`) in the
response — it currently discards everything except presence flag, date range, and the last
value. Extend this (or write a new script alongside it — your call, but reuse the working
fetch/cache/retry logic, don't rebuild it) to persist the **full series**, at monthly grain
(last observation per calendar month, matching `universe_panel.csv`'s convention), for **every
token with a confirmed `dl_slug` match** in `asset_onchain_identity.csv` — not just the
104/111-token NaN-PQ worklist subset used by the Phase 2c diagnostic. That's 127 tokens as of
this session; re-derive live.

Output: `03_data/phase2/tvl_panel.csv` with columns `cmc_id, symbol, dl_slug, month_end, ym,
tvl_usd`. Cache raw per-token JSON under `03_data/raw/phase2/tvl/` (same caching discipline as
every prior phase). Use `time.sleep(0.2)` between calls per the existing script's pattern.

**Optional, time-permitting, secondary to the core 127-token build:** the 127-token ceiling
comes from `phase1_build_identity_map.py`'s `cmcId`-keyed join against DeFiLlama's `/protocols`
list. Check whether any of the 321 currently-unmatched tokens can be picked up via a looser
match (e.g. name/symbol similarity against DeFiLlama's protocol list) — but **verify each
candidate match individually before adding it** (same standard as every identity-mapping
decision in this log; a wrong slug match would silently corrupt the panel). If this turns out to
be slow or low-yield, stop and note it in the report rather than grinding on it — it's a stretch
goal, not the deliverable.

**Re-affirm, in the report, that this panel is a valuation-multiple denominator (NV/TVL), not a
PQ substitute** — Entry 30's stock-vs-flow distinction is unchanged by this build.

## What NOT to do

- No PQ-for-coins work. No Channel 2 (holding duration) work.
- No paid tier of anything (DeFiLlama Pro, Etherscan archive, Boardroom, Tally, beaconcha.in).
- No symbol-only joins — always `cmc_id`.
- No silently proxying an excluded escrow/staking relationship (the veBAL/SNX standard applies
  to every new candidate in A.1 and A.3 equally).
- No guessing a staking ratio, a Snapshot space, or a slug match — verify live or flag the gap.
- No editing `phase1_assemble_lambda.py`'s z-scoring/standardizability/weighting logic.
- No financial/purchase action of any kind.

## Deliverable

Write `03_data/PHASE1_LAMBDA_SCALE_AND_TVL_PANEL_REPORT.md` containing:
- Before/after λ coverage: by channel, by asset class (coin/token), asset-month counts and
  distinct-asset counts, same format as the existing `PHASE1_COVERAGE_REPORT.md`.
- Every new Channel-1 candidate checked in A.1, with a verified/rejected verdict and why.
- The Channel-3 widening result from A.2 (new spaces added, on-chain `VoteCast` attempts and
  outcomes for the Entry-25 gap list).
- The live PoS-coin source audit from A.3: which chains had a free historical staking series,
  which were paywalled/current-state-only/absent, and the resulting coin-side Channel 1
  coverage.
- TVL panel coverage: token count, date range, any tokens where the fetch failed or returned an
  empty series, and the result of the optional slug-widening attempt if you did it.
- A clear closing note on what's still NOT covered and why, so the next session (coin PQ) starts
  from an accurate picture.

Then:
- Log this session as `06_documentation/ai_conversations/session_019_<date>_<topic>.md` (verify
  019 is actually next per Step 0.3).
- Continue `04_code/DATA_DECISIONS_LOG.md` from the live-verified next entry number (per Step
  0.3 — should be 41, confirm).
- Add a row to `06_documentation/time_log.md`.
- Commit and push to `main` on `github.com/moazzamkhoja/AFA_2027_QTM_Crypto` — but only after
  re-running `git status` per Step 0 and confirming the diff looks sane (the real files you
  intentionally changed, nothing more).

**Stop after the report.** Do not start coin PQ sourcing, and do not touch Channel 2, before
this is reviewed.
