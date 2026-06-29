# Session 021 — Token Bucket-1 Exhaustive Re-Audit Coverage Addendum

**Project:** AFA 2027 QTM Crypto. **Session:** 021 (2026-06-29). **Model:** Claude Code / Opus 4.8.
**Scope (from `CLAUDE_CODE_TOKEN_BUCKET1_EXHAUSTIVE_REAUDIT_PROMPT.md`):** convert all 398 token-side
"unrecoverable" cmc_ids (+ a reconfirm of the 6 already-rejected + resolve VELO) into individually
documented, source-checked verdicts. No category-level write-offs. Token-side only; coin Bucket 1 and
Phase 3 untouched. **No paid tier used; no purchase made.** Source-of-truth for *why*:
`04_code/DATA_DECISIONS_LOG.md` Entries 50–52 (this session).

> **Headline.** The 398 figure was confirmed exact (live re-derivation, not the cached 290-file). Running
> the funnel found **5 recoverable tokens the session-020 category-level pass had written off** — **API3,
> ORBS, IQ, VVV** (all in the 398) plus **VELO** (the Entry-48 deferral, now resolved). Each is a clean
> single-contract base-token lock cross-checking to live `balanceOf` at **0.00%** (the Entry-26 / xSUSHI–
> stkAAVE–GMX standard). λ now covers **2,080 observed asset-months across 67 distinct assets** (up from
> 1,880 / 62). The remaining 393 of the 398 each carry an individual, source-checked rejection reason —
> none is a silent or category-level drop.

| λ metric | session 020 (before) | session 021 (after) | Δ |
|---|---|---|---|
| observed asset-months | 1,880 | **2,080** | +200 |
| distinct assets | 62 | **67** | +5 (API3, ORBS, IQ, VVV, VELO) |
| — token | 49 | **54** | +5 |
| — coin | 9 | 9 | 0 |
| — other | 4 | 4 | 0 |
| Ch1 token locks | 13 | **18** | +5 |

---

## Final verdicts across the 398 (+VELO +6 reconfirm) — `03_data/phase1/token_bucket1_full_audit.csv` (402 rows)

| Verdict | Count | What it means |
|---|---|---|
| **BUILD** | **5** | API3, ORBS, IQ, VVV (in the 398) + VELO (the deferral). Single-contract base-token lock confirmed; series built & folded into λ. |
| **REJECT-mechanism** | 367 | A specific protocol-design reason no single-contract base-token lock exists (multi-pool/native/composite/delegation/farming/Snapshot/meme/stablecoin). Money cannot fix it. |
| **REJECT-no-data** | 29 | A staking mechanism plausibly exists but no free source covers it (non-EVM chain outside the free EVM Dune curated-transfers method; or no single escrow reproduces the DL figure; or a cmcId collision). |
| **N/A out-of-universe** | 1 | ANGLE — confirmed never in the 448-token universe (named in Entry 41 only). |

402 rows = 398 worklist (which already contains AXS/RUNE/MKR) + VELO + the 3 reconfirm tokens not in the
worklist (BAL, COMP, ANGLE — BAL/COMP are already in λ via Channel-3 voting, so they were never in the 398).

---

## What was checked, by confidence tier (the point of the re-audit)

The Cowork challenge was that "398 unrecoverable" rested on three different levels of rigor. This session
applied a **uniform per-token check** and recorded exactly what was and was not done:

**Stage 0 — worklist rebuilt live.** Re-derived from `universe_panel.csv` + `lambda_panel.csv`:
in-universe `asset_class='token'` cmc_ids not in λ, minus VELO = **exactly 398** (448 − 49 in λ − 1 VELO).
The cached 290-candidate file was **not** trusted; the count reconciles to the penny.

**Stage 1 — bulk DeFiLlama triage, ALL 398, by `cmcId` (never symbol).** Live `api.llama.fi/protocols`
(7,742 protocols, 1,706 with a cmcId). Result tiers:
- **92** have a clean cmcId-matched DeFiLlama protocol (→ Stage 2).
- **306** have **no** cmcId DL protocol **and** no contract address on file → logged explicitly as
  "no on-chain identity available to check," which is itself the specific, honest reason (not a silent
  drop). Each still receives a token-specific sector reason from its CMC tags/sector.
- The symbol-matched DeFiLlama categories in `classification_table.csv` were deliberately **not** used to
  promote anything (Entry-20 symbol-collision landmine; e.g. DOT-cmc814, HONEY, DRIFT, VOLT, LAYER all
  carried spurious "Liquid Staking" tags from unrelated same-symbol protocols).

**Stage 2 — real per-token check of every DL-matched token (all 92, not a sample).**
- **2a (DeFiLlama TVL):** pulled `/protocol/{slug}` `chainTvls` for all 92 → **36** expose a `staking`
  bucket carrying a raw **staked-token-quantity** series (`chainTvls['staking']['tokens']`), a stronger
  proxy than the USD value the kickoff anticipated. Computed DL-staked-qty ÷ panel circulating for all 36.
- **2b (Dune top-holder cross-check = Etherscan-equivalent for the Entry-26 identity):** for **every** of
  the 36 with a non-zero staking bucket, ran a Dune `tokens_<chain>.balances` / net-transfers top-holder
  query to test: does **one** contract hold the base token in the DL-reported staked amount? Only when the
  top holder equals the DL staked quantity (single-contract base-token custody) does it pass. The full
  reconstruction then cumulates `tokens_<chain>.transfers` in/out of that escrow and cross-checks to
  `balanceOf` (same method as Bucket 3 / Entry 48).
- **2c (Artemis):** tested live — `app.artemis.xyz` 308-redirects to `classic.artemis.ai`, which serves a
  JS-rendered SPA shell with **no** server-side per-asset staking data retrievable without a login. No free
  per-asset staking-ratio surface exists (reconfirms Entry 2/14). **Not signed up, not paid.**

**Stage 3 — every non-DL-matched / non-staking-bucket token gets a specific sector line** (meme / wrapped-LST
/ DEX / lending / derivatives / gaming / L1-L2 / DePIN / governance-only / no-identity), not a category verdict.

**Stage 4 — the 6 reconfirmed + VELO resolved** (see below).

### The 5 BUILDs (each cross-checks to live `balanceOf` at 0.00%)

| cmc | sym | chain | escrow (holds BASE token) | ratio | mechanism |
|---|---|---|---|---|---|
| 7737 | API3 | Ethereum | Api3Pool `0x6dd655…c76d76` | ~74% | single reward-staking pool (xSUSHI/stkAAVE-style) |
| 3835 | ORBS | Ethereum | StakingContract `0x01d59a…656c3` | ~42% | single staking contract |
| 2930 | IQ | Ethereum | HiIQ veIQ `0x1bf545…e16ba` | ~9% | Curve-style vote-escrow |
| 35509 | VVV | Base | Venice staking `0x321b7f…f340ff` | ~73% | single reward-staking contract |
| 7127 | VELO | Optimism | veVELO VotingEscrow `0xfaf8fd…06787d` | ~7.4% | vote-escrow (deferral resolved) |

**FLAG (rides along in the per-series `flag` column):** API3 and ORBS show `staking_ratio>1` in some months
— CMC's `circulating_supply` excludes the pooled/staked tokens (the same AERO/SOL denominator artifact,
Entry 49). Kept un-capped and flagged; λ z-scores on relative rank, not level.

### VELO — Entry-48 deferral RESOLVED (not left deferred)
Entry 48 deferred VELO believing cmc 7127's token `0x9560e827…` was a defunct "v1" token distinct from the
live v2 lock. This session found the **documented, non-guessed mapping** the kickoff asked for: DeFiLlama's
**own** Velodrome **V2 and V3** protocol entries both carry `address=optimism:0x9560e827…` — i.e. `0x9560e827`
is the **current canonical** Velodrome token, not defunct. CMC (7127→`0x9560e827`) and DeFiLlama (V2/V3→
`0x9560e827`) **agree**. The veVELO VotingEscrow `0xfaf8fd17…` holds **1,295,615,052** of that token directly
on Optimism (= 7.4% of circulating). No cmcId/symbol collision remains → built to the same standard.

### Rejections at Stage 2b (DL staking bucket exists but fails the single-escrow test)
Multi-contract / no-single-escrow (the CELO lesson — an honest gap beats a wrong number): **EIGEN**
(EigenLayer restaking spread across strategy contracts), **ILV** (multi-pool), **KEEP** (migrated to T),
**HEX** (staking internal to the HEX contract). No single contract reproduces the DL staked figure:
**BTCST, ZBU, PEAK, KAITO, MBOX, TIME, ATH, AKRO, SUPER, EPS, AUCTION, MVL, MAGIC, BAKE, RFOX, MYX, SFI**.
DL staking bucket reads 0: **HEX, SFUND, ADF, FLEX, CASINO**. Non-EVM staking outside the free EVM method:
**HXRO** (Solana), **SUN** (Tron), **ORN** (TON), **TLM** (WAX), **C98** (TomoChain), **BRISE** (Bitgert).
cmcId-collision artifact: **WARP** (DL maps slug `polkastarter` to cmcId 1166 → impossible 1764% ratio).

### The 6 already-rejected — reconfirmed unchanged
**MKR** (DSChief in-wallet voting, ~0.5%), **BAL** (veBAL locks an 80/20 BPT, not BAL), **COMP** (in-wallet
delegation), **RUNE** (native THORChain L1 bonding), **AXS** (Ronin appchain, no free EVM index) — all
reconfirmed via live DeFiLlama (none exposes a cmcId-matched staking bucket) + the prior on-chain findings.
**ANGLE** confirmed out-of-universe.

---

## Resource accounting (no purchase, free budget respected)
- **Dune free tier:** ~36 `small` executes this session (top-holder probes + 5 reconstruction builds);
  est. ≈350–400 of the 2,500 monthly query-credit budget (~15%). Well within headroom; flagged here per the
  kickoff's request to watch it rather than assume headroom.
- **Etherscan free key:** not newly required (Dune top-holder probes replaced per-token Etherscan holder
  lookups, which are PRO-gated).
- **Artemis / any paid tier:** not used, not signed up, not paid.
- Every join is on `cmc_id`, never symbol. Every built series cross-checks to a live on-chain `balanceOf`.
  No staking ratio was guessed or interpolated. The DL token-quantity series was used only to **locate** the
  escrow; the shipped numerator is the on-chain Dune transfers reconstruction.

## Open follow-ups (flagged, not started)
1. **Coin-side Bucket 1 (456 coins) has NOT had this individual re-audit** and may warrant the same
   treatment in a future session — explicitly out of scope here; do not start without review.
2. **GATED — none.** No priced self-serve free-tier-blocked option surfaced for any of the 398 that would
   recover a token Moazzam could buy his way into; the rejections are mechanism- or non-EVM-data-bound, not
   paywalled. (Subscan-style free-key gaps remain coin-side, Entry 44.)
3. The KAITO/ATH/AKRO-type "treasury dominates balances" cases could in principle be revisited with a Dune
   query that filters to the protocol's named staking contract if its address is later documented — but none
   passed the single-escrow `balanceOf` identity this session, so none was shipped.
