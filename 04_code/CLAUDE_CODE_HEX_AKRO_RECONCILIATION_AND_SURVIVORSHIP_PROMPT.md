# Claude Code Kickoff Prompt — HEX/AKRO Reconciliation + Survivorship-Bias Documentation

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`. This follows a Cowork review of session 022's full-universe
feasibility pass (`06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md`), which read verified
contract source code and confirmed mechanisms live via `getLogs` — a materially more rigorous,
Etherscan-direct method than session 021's Dune top-holder substitute. Two of session 022's "6
genuine Channel-1" tokens, HEX and AKRO, directly contradict explicit session-021 rejections. The
decision is to trust session 022's contract-code-read + getLogs method as the higher-fidelity
standard and resolve the contradiction with it — not to referee 021 vs. 022 by assumption. A second,
separate task documents the ~284 dead 2014-2018 listings (no chain/contract identity on any
explorer) as an acknowledged survivorship-bias limitation rather than a pending data gap.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Two things to resolve this session, in
order. Read everything in "Required reading" before touching either.

## Required reading
1. 04_code/DATA_DECISIONS_LOG.md Entry 26 (the single-escrow custody standard) and Entry 53
   (session 022's feasibility-finding entry) — read the full text, not a summary.
2. 03_data/SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md — the exact rejection lines for HEX
   ("staking internal to the HEX contract", Stage 2b) and AKRO ("no single contract reproduces
   the DL staked figure", Stage 2b, grouped with KAITO/ATH/SUPER/etc.).
3. 06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md section 2a — HEX and AKRO are listed
   under "Channel 1 genuine lock/stake, getLogs-CONFIRMED: 6", but the parenthetical splits them:
   HEX is "amount-bearing, build-ready"; AKRO is "bare Locked(), need contract-balance reads" — a
   weaker confirmation than the other 4 (NMR, stkAAVE, XAN, and the other amount-bearing one).
4. The raw per-event caches already produced by session 022 for these two cmc_ids — pull their
   rows directly rather than re-querying Etherscan from scratch: 03_data/phase1/
   universe_lambda_channel_map.csv, 04_code/_universe_lambda_findings.csv (or the bucket-1 subset
   04_code/_etherscan_lambda_findings.csv / 03_data/phase1/etherscan_lambda_channel_map.csv), and
   03_data/raw/etherscan_src/ for the cached verified source.

## Part 1 — HEX and AKRO reconciliation (apply session 022's method, not session 021's)

For each of HEX and AKRO, run the FULL Entry-26 test using session 022's higher-fidelity method —
do not stop at "an event fires." The bar is the same one the 5 session-021 BUILDs cleared: a
specific contract/event must let you reconstruct a monthly locked-quantity series that cross-checks
to a live on-chain balance, not just confirm a mechanism exists.

**HEX:**
- Identify the exact staking event(s) in the cached verified source (likely `StakeStart`/
  `StakeEnd`-style events). Confirm via getLogs whether the event itself carries the staked amount
  directly (amount-bearing) — if so, this is a genuinely different construction path than
  Entry-26's transfer-based reconstruction (no separate escrow contract needed), and that's fine,
  but it must be stated explicitly as a new method, not silently treated as equivalent.
- Resolve the custody question directly, don't infer it: does HEX's staking move the staked
  tokens out of the holder's wallet balance into the HEX contract's own balance (custodial,
  `balanceOf` of the contract rises), or does the holder's `balanceOf` stay unchanged while a
  separate internal struct/mapping just flags the stake (non-custodial bookkeeping)?
- If non-custodial: check HEX's actual CoinMarketCap `circulating_supply` field/methodology
  directly (don't assume) — does it already exclude staked HEX, or does it include it? This
  determines whether building this series double-counts against the existing AERO/SOL/API3/ORBS
  denominator artifact (Entry 49). State the answer plainly before deciding to build.
- Reconstruct the monthly staked-HEX series via event replay (sum of active stakes by month from
  `StakeStart`/`StakeEnd` amounts) and spot-check it against at least 2-3 months of the contract's
  own on-chain state (e.g. a public `globalInfo`/`stakeShares` read if one exists) the same way the
  5 BUILDs were cross-checked to 0.00% drift in session 021.

**AKRO:**
- Locate the actual named staking/lock contract address from the cached verified source (the
  "bare Locked()" event implies a contract was found but not yet confirmed amount-bearing).
- Confirm via getLogs + a direct contract-balance read whether that ONE contract holds a
  meaningful, reproducible share of AKRO's base-token supply — i.e. satisfy the SAME single-escrow
  test that rejected it in session 021, not a looser "a Locked event exists somewhere" bar.
- If the contract's balance does not reproduce a stable, sensible staked-supply figure (e.g. it's
  a treasury/multisig holding an unrelated allocation, the original session-021 suspicion for this
  whole cohort — KAITO/ATH/SUPER etc.), say so explicitly and explain what the contract actually
  is.

**Resolution for each:**
- If it now passes the full standard: build it into λ via the existing `phase1_channel1_*.py`
  scripts (extend, don't rebuild), and log a NEW DATA_DECISIONS_LOG entry (continue from Entry 54
  — do not edit the session-021 entry) stating explicitly: "session 021's rejection of [HEX/AKRO]
  is superseded by Entry [N], using session 022's contract-code-read + getLogs method, which found
  [specific reason]." Name the superseded entry by number.
- If it still fails once fully reconstructed: log that explicitly too, with the specific reason
  the getLogs confirmation wasn't sufficient (e.g. "mechanism exists and is active, but is
  non-custodial / multi-contract / doesn't reproduce a usable figure") — restate the session-021
  rejection with the new evidence, don't leave it ambiguous between the two sessions' reports.
- Either way, write a short addendum note (append to a new
  `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md`) so the contradiction between 021 and 022 has a
  documented resolution on record, not two conflicting reports sitting side by side.

## Part 2 — Survivorship-bias documentation (the dead 2014-2018 listings)

Session 022 found 284 of the 405 non-EVM/off-Etherscan tokens have NO chain/contract identity
recoverable on any explorer checked (EVM or non-EVM) — dead listings from 2014-2018. Re-derive this
count live from `03_data/phase1/non_evm_lambda_recoverability.csv` (and cross-check against
`03_data/phase1/universe_lambda_channel_map.csv`) rather than reusing the report's number without
confirming it — reconcile it to the penny against the documented universe the same way session 021
reconciled its 398.

These are not a pending data gap to keep chasing — they are genuinely, permanently unrecoverable
(no contract, no chain identity, on any free or paid source). Document them as an acknowledged
survivorship-bias limitation:
1. A new DATA_DECISIONS_LOG entry (next number after the HEX/AKRO entries) stating the live-
   reconciled count, the criteria used to call a token "dead" (no chain/contract identity on any
   explorer, EVM or non-EVM, checked across sessions 021-022), and that no further recovery effort
   is planned for this group.
2. A short, paper-ready paragraph (3-5 sentences, citable) for the data/methodology section
   stating: these tokens were active CMC listings in 2014-2018 with no recoverable on-chain
   identity today (delisted, abandoned, or rug-pulled), their exclusion is a genuine survivorship-
   bias source rather than a methodological choice, and this should be named explicitly rather than
   absorbed silently into the broader "no-data" rejection category. Note for the paper's limitations
   discussion whether survivors are likely to differ systematically from this dead cohort in ways
   correlated with λ or returns (e.g. dead tokens disproportionately being low-conviction/no-
   governance assets to begin with), since that's the actual bias-direction question a referee
   would ask.
3. Save the paragraph as a clearly-labeled section in `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md`
   (or a separate `03_data/SURVIVORSHIP_BIAS_NOTE.md` if cleaner) so it can be pulled directly into
   `05_paper/` later without re-deriving it.

## Rules (unchanged)
- Trust session 022's contract-code-read + getLogs method over session 021's Dune-substitute method
  wherever they conflict — that's the explicit basis for this session, not a neutral re-litigation.
- Never sign up for or pay for any paid tier (Etherscan Pro included). Flag, don't act.
- Join everything on `cmc_id`, never `symbol`.
- Never guess or interpolate a numerator — reconstruct from real events/balances or flag the gap.
- DATA_DECISIONS_LOG.md is append-only — never edit Entries 1-53. Continue at Entry 54.
- Do NOT touch the Channel-3 dedup, the 16 BSC/Base/Avax paid-gated tokens, or the Channel-2
  prototype from session 022's other open items — this session is scoped to HEX/AKRO + the
  survivorship-bias note only. Those remain separate, pending review.
- Update `06_documentation/time_log.md` and log this session as
  `06_documentation/ai_conversations/session_023_*.md`. Commit and push to
  github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end.

Stop when HEX and AKRO each have a final, explicitly-resolved verdict (BUILD or REJECT, with the
021-vs-022 contradiction named and settled) and the survivorship-bias note is written. Do not start
any of session 022's other open items without review.
```
