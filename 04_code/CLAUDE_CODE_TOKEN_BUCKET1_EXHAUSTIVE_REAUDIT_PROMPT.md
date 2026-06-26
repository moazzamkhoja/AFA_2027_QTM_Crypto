# Claude Code Kickoff Prompt — Exhaustive Re-Audit of the 398 "Unrecoverable" Tokens

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`. This follows a Cowork session's challenge to session 020's
token-side Bucket-1 figure (398 tokens with no λ Channel-1 series): that figure rests on three very
different levels of rigor, not one uniform check, and the paper's sample size is thin enough that
no token should be written off without an individually documented, source-checked reason. Run to
completion, review the output, then come back before touching coin-side Bucket 1 or Phase 3.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Session 020 left the token universe (448
tokens) at: 49 recovered (λ Channel 1 built), 1 deferred (VELO, identity ambiguity), and 398 marked
unrecoverable. A Cowork review of that 398 found it is NOT one uniform level of checking:

  - ~6 tokens (MKR, BAL, COMP, RUNE, ANGLE, AXS) — individually verified, each with a specific
    documented protocol-design reason (no clean single-escrow lock exists, full stop). HIGH
    confidence these are genuinely unrecoverable by any vendor, free or paid.
  - ~287 tokens — were in the 290-candidate pool (`03_data/phase1/_bucket3_candidates.csv`) and
    were rejected, but the rejection was written at the CATEGORY level ("the overwhelming majority
    are DEX/lending/RWA/meme/chain tokens whose governance is delegation/farming/Snapshot") — not
    confirmed contract-by-contract for every single one. MEDIUM confidence at best.
  - ~111 tokens — never opened individually at all. They were excluded purely because
    `classification_table.csv` tags / `defillama_categories` didn't suggest a staking mechanism.
    That's a pre-filter heuristic, not a check. LOW confidence.

This session's job is to convert ALL 398 (+ a final confirmation pass on the 6 already-rejected +
resolve VELO's identity question) into individually documented verdicts, checked against every
named source (Etherscan, Dune, DeFiLlama, Artemis), before any of them are accepted as a real,
final rejection. Every one of the 398 must end this session with its own row and its own specific
reason — no category-level write-offs, no silent drops. Before doing anything else, read in full:

1. 04_code/DATA_DECISIONS_LOG.md Entries 26, 41, 48, 49 — the Entry-26 clean-escrow standard, the
   Part A.1 rejection list, and session 020's Bucket-3 build + the category-level rejection language
   that triggered this re-audit.
2. 03_data/SESSION020_BUCKET2_BUCKET3_COVERAGE_ADDENDUM.md Part B — the exact candidate-pool
   construction and the "~287 others" line being re-audited here.
3. 04_code/DATA_SPECIFICATION.md §0 (flag, don't guess) and §3.1 (Channel 1 definition).
4. 03_data/phase1/_bucket3_candidates.csv (290 rows) and 03_data/classification_table.csv — the
   290-candidate pool plus the ~111 tokens that pool excluded. Recompute the full 398 list directly
   from universe_panel.csv (every `asset_class='token'` cmc_id with zero Channel-1 months) — don't
   trust 398 as exact; confirm it live against the current panel.
5. 04_code/phase1_channel1_evm_locks_bucket3.py, phase1_channel1_evm_locks.py,
   phase1_channel1_evm_locks_ext.py — the Dune-transfers build method; extend, don't rebuild.
6. 04_code/.api_keys.json — confirm what's already there (etherscan, dune) before any new signup.

## Method — a triage funnel, not equal-depth effort on all 398

398 individual deep-dives across 4 sources each is not a uniform-depth task; do it as a funnel so
effort concentrates where it can change the outcome, while every token still gets logged.

**Stage 0 — rebuild the worklist live.** Recompute the exact 398 (or whatever the live number is)
from universe_panel.csv + classification_table.csv. Do not reuse the cached 290-candidate file
without re-deriving it — confirm it's still accurate against the current panel.

**Stage 1 — cheap bulk triage for ALL 398 (must cover every row).**
- Pull DeFiLlama's bulk `https://api.llama.fi/protocols` (one call, already cached by
  `phase1_build_identity_map.py` — refresh it). For every token's mapped protocol (by `cmcId`, NEVER
  symbol), check the `category` field. Flag HIGH if category is "Staking" or "Liquid Staking" or
  similar; flag MEDIUM if category is ambiguous but the protocol has ANY tag/category suggesting
  governance/locking; flag LOW if the protocol is clearly DEX/lending/meme/bridge/L1-L2/RWA with no
  staking signal anywhere in DeFiLlama's metadata.
- For the ~111 tokens with no DeFiLlama protocol mapping at all (no `cmcId` match in `/protocols`),
  do a second cheap pass: check the token's own `classification_table.csv` row for any docs URL,
  website, or platform/contract address already on file; if a contract address exists, that's
  enough to route into Stage 2. If NEITHER a DeFiLlama mapping NOR a contract address exists, log
  it explicitly as "no on-chain identity available to check at all" — that is itself a specific,
  honest reason, not a silent drop.
- Log every one of the 398 with its Stage-1 label. This stage must finish for all 398 before
  Stage 2 starts.

**Stage 2 — real per-token check for everything labeled HIGH or MEDIUM in Stage 1 (no sampling —
every HIGH/MEDIUM token gets this, not a subset).** For each:
  a. **DeFiLlama** — open the protocol's `/protocol/{slug}` endpoint; check `chainTvls` for a named
     staking/locking pool breakdown. If one exists, note the USD value and flag it as a VALUE-based
     proxy for locked supply (distinct from a literal token-quantity reconstruction) — do not treat
     a USD figure as equivalent to the existing Channel-1 token-quantity standard without saying so.
  b. **Etherscan (or the relevant EVM chain explorer under the existing free key)** — find the
     token's contract; check its verified-contract / top-holders surface for any contract plausibly
     named escrow/vault/stake/gauge/lock holding a meaningful share of supply. If a candidate
     contract is found, apply the EXACT Entry-26 standard: single contract, direct custody of the
     BASE token, not a wrapped/composite asset, not in-wallet delegation, not a collateral system.
  c. **Dune** — only for tokens that pass 2b with a real escrow candidate: confirm
     `tokens_<chain>.transfers` or `.balances` covers that chain/contract (per the session-020
     correction — `tokens_bnb` not `tokens_bsc`, etc.) before committing to a build. Track query
     credit usage against the free 2,500/month budget; flag, don't silently burn through it.
  d. **Artemis** — test live, unauthenticated, whether artemis.xyz exposes a public per-asset
     terminal/dashboard page (not the API) showing a staking-ratio or locked-supply chart. Try it on
     2-3 known-staking tokens (e.g. CRV, AAVE) and 2-3 known non-staking tokens first to learn the
     access pattern before deciding whether it's worth checking per-token at scale. If it requires
     login or a paid plan for the data you need, stop — do not sign up or pay.
  Classify each Stage-2 token: BUILD (ship it, same as Entry-26 builds) / REJECT-mechanism (specific
  contract/protocol reason, money can't fix it) / REJECT-no-data (mechanism plausible but no source,
  free or paid, covers it) / DEFER (specific blocker, e.g. an identity collision like VELO) /
  GATED (a real paid option exists — name it, price it if disclosed, do NOT subscribe; report to
  Moazzam for his own purchase decision).

**Stage 3 — fast confirmation pass for everything labeled LOW in Stage 1.** Don't deep-dive these,
but don't silently drop them either: for each, write one specific line (e.g. "wrapped/composite
asset, no underlying lock," "meme token, no protocol, no contract evidence of any lock," "CEX/
custodial token, governance is off-chain"). If anything in this pass looks ambiguous on a second
look, promote it back into Stage 2 rather than force a quick verdict.

**Stage 4 — final pass on the 6 already-rejected (MKR, BAL, COMP, RUNE, ANGLE, AXS) and VELO.**
Light-touch only: confirm via DeFiLlama + a quick Etherscan/Ronin check that nothing has changed
since Entry 26/41/48 (no new escrow contract shipped, no protocol redesign). For VELO, attempt to
resolve the v1/v2 identity question directly — check CMC's own platform/contract field for cmc_id
7127 and DefiLlama's protocol entry for Velodrome v2 to see if there's a documented, non-guessed
mapping between the in-universe v1 contract and the v2 lock; if no clean mapping exists, leave
deferred with that stated.

## Rules (unchanged from the spec and prior entries)
- Never sign up for or pay for any paid tier of anything (Etherscan Pro/archive, Artemis
  Enterprise, Dune paid, Subscan Pro, etc.). Flag a priced, self-serve option and report back to
  Moazzam — he executes any purchase himself, even with confirmed funding available.
- Join everything on `cmc_id`, never `symbol`.
- Never guess or interpolate a numerator. A USD-value proxy (Stage 2a) must be labeled as a proxy,
  never silently treated as the token-quantity standard.
- Every one of the 398 (+6 reconfirm +1 VELO) gets its own row with a specific reason. No
  category-level verdict, no row left blank.
- DATA_DECISIONS_LOG.md is append-only — never edit or delete Entries 1–49. Continue at Entry 50,
  one entry per stage/cluster of findings (not one giant entry covering all 398).
- Watch Dune's free query-credit usage given the larger scale of this session; flag if approaching
  a meaningful fraction of the monthly 2,500 budget instead of assuming there's always headroom.

## Deliverables
1. A single CSV, `03_data/phase1/token_bucket1_full_audit.csv`, one row per token in the 398 (+6
   reconfirmed +1 VELO) with columns: cmc_id, symbol, name, defillama_protocol_slug,
   defillama_category, stage1_label, stage2_etherscan_check, stage2_dune_check,
   stage2_defillama_tvl_check, stage2_artemis_check, final_verdict (BUILD / REJECT-mechanism /
   REJECT-no-data / DEFER / GATED), reason (specific, non-generic text).
2. Built series for every new BUILD verdict, folded into λ via the existing
   `phase1_channel1_evm_locks*.py` scripts (extend, don't rebuild) and re-run
   `phase1_assemble_lambda.py`; report new asset/asset-month counts against the session-020
   baseline (62 assets / 1,880 asset-months).
3. A coverage addendum, `03_data/SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md`, summarizing: how
   many of the 398 ended in each final-verdict bucket, how many were GATED (with named source +
   price if disclosed), and an explicit statement of what was and was not checked for each
   confidence tier — written so it can support the paper's methodology section as evidence that
   every reasonable free avenue was exhausted before any token was excluded.
4. DATA_DECISIONS_LOG.md continued from Entry 50. Log this session as
   `06_documentation/ai_conversations/session_021_*.md`; update `06_documentation/time_log.md`.
5. Commit and push to github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end.

Note: this session is token-side only (the 398 + 6 + VELO). The 456-coin Bucket-1 has NOT had this
level of individual re-audit and may warrant the same treatment in a future session — flag that as
an open follow-up in the addendum, but do not start it here without review.

Stop when all 398 (+6 +1) have a logged, specific, individual verdict. Do not start coin-side
Bucket 1 or Phase 3 without review.
```
