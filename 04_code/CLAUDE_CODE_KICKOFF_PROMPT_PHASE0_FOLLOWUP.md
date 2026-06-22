# Claude Code Kickoff Prompt — Phase 0 Follow-Up (pre-Phase 1 cleanup)

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This is a short follow-up
to Phase 0, not Phase 1 itself. Run it to completion, review the output, then come back
for the Phase 1 (lambda channels) kickoff prompt.

---

```
You're working in the AFA 2027 QTM Crypto research repo. A prior session (logged as
Session 006) completed Phase 0 (asset universe) and stopped for review. That review is
done. Before doing anything else, read in full:

1. 04_code/DATA_SPECIFICATION.md — including new section 2.6 (sector/economic-function
   classification), added after this review.
2. 04_code/DATA_DECISIONS_LOG.md — read Entries 1-16. Entries 10-16 are the review
   decisions you're implementing in this session.
3. 03_data/PHASE0_COVERAGE_REPORT.md
4. 06_documentation/PHASE0_SESSION_STATUS.md

Your task right now is a FOCUSED FOLLOW-UP to Phase 0, not Phase 1. Do not start
Phase 1 (lambda channels) in this session. There are three deliverables:

1. CARRY-FORWARD SPLIT (implements Decisions Log Entry 10).
   For every asset-month currently marked status='carried_forward' in
   03_data/universe_panel.csv, classify it into one of two subtypes:
   - 'presumed_failed': the asset never reappears in the observed top-1000 snapshot
     for the remainder of the sample (2026-05-31).
   - 'temporarily_out': the asset drops out of the top-1000 snapshot but reappears in
     a later month.
   Add this subtype as a new column (don't overwrite the existing status column).
   Report: total carried-forward asset-months, split by subtype; the count of
   distinct assets in each subtype; the distribution of gap lengths for
   temporarily_out (min/median/max months out); and the count of presumed_failed
   assets whose gap, if it had continued to the end of the sample, would have looked
   identical to a temporarily_out case still mid-gap as of 2026-05-31 (i.e. flag the
   right-censoring risk explicitly — don't silently treat "never seen again so far" as
   equivalent to "permanently dead" for assets whose gap started recently).
   Do NOT pick or implement a death-return formula. That decision is intentionally
   deferred — just produce the split and the diagnostic counts so the next decision can
   be made with real numbers in front of it.

2. CLASSIFICATION CONFIRMATION PASS (implements Decisions Log Entry 11).
   From 03_data/classification_table.csv, select 'other'/ambiguous_flag=True assets
   with >=12 observed asset-months in 03_data/universe_panel.csv (count months where
   the asset is actually observed, i.e. exclude carried_forward months from this
   count — carried-forward months aren't real observations of the asset's behavior).
   For each selected asset, do a quick evidence-based review using whatever tags,
   DeFiLlama category data, and public knowledge of the project you can verify, and
   propose: keep as 'other', reclassify to 'coin', or reclassify to 'token' — with a
   one-line rationale per asset. Do not invent classifications you can't support;
   if an asset is genuinely ambiguous after review, say so explicitly and leave it
   'other' with a note, rather than forcing a label.
   Within this pass, specifically check whether any of these reviewed names are
   meme coins (DOGE, SHIB, PEPE, WIF, BONK, FLOKI, and similar) or NFT-adjacent
   tokens. Per Decisions Log Entry 12, meme coins are correctly left as 'other' (no
   change needed) — just confirm they're in fact landing there and aren't being
   mis-flagged as coin/token by the existing tag rules. Also explicitly check the
   universe for anything that looks like an actual NFT collection (not a fungible
   token) — confirm none exist in the panel (the CMC fungible-listings endpoint
   shouldn't have any), and say so explicitly in your report rather than assuming it.

3. SECTOR/ECONOMIC-FUNCTION CLASSIFICATION (implements Decisions Log Entry 16, spec
   section 2.6). This is a SECOND, INDEPENDENT classification field — do not merge it
   with or use it to revise the coin/token `asset_class` field from deliverable 2 or
   from Section 2.3; it sits alongside it, not inside it.
   For every asset in 03_data/classification_table.csv, add a `sector` column:
   - Primary source: the existing `defillama_categories` field (already populated for
     574/2010 assets) — these values (Dexs, Lending, Derivatives, Liquid Staking, CDP,
     Bridge, RWA, Gaming, NFT Marketplace, Synthetics, Options, Restaking, Staking Pool,
     etc.) are themselves usable sector tags; carry them into `sector` as-is (keep
     multi-value semicolon-separated strings rather than forcing one pick).
   - Fallback source: CMC `tags`, specifically `layer-1` and `layer-2` (134 and 43
     assets respectively) for base-layer coins that have no DeFiLlama protocol entry,
     plus any other clearly sector-like tags you find useful (oracle, privacy, depin,
     meme, etc.). If both sources give a signal for the same asset, keep both rather
     than discarding either.
   - Leave `sector` blank/null where neither source gives a usable signal — do not
     guess or infer a sector from the asset name alone.
   Report coverage: total assets with a non-null `sector`, broken out by `asset_class`
   (coin/token/other) — i.e., what fraction of coins get a sector tag (expect this to
   lean on layer-1/layer-2 tags) versus what fraction of tokens do (expect this to lean
   on DeFiLlama categories), and the residual with no tag from either source.
   Do NOT decide or propose which sector-level comparisons (e.g. DEX vs. Perpetuals,
   Lending vs. Staking, L1 vs. L2) will actually be used in the paper — that decision is
   explicitly deferred (Decisions Log Entry 16). Your job here is only to get the field
   populated and report its coverage.

Update 04_code/DATA_DECISIONS_LOG.md as you go for any new judgment call (e.g. the
exact rule you use to call something 'temporarily_out' vs 'presumed_failed' at the very
end of the sample window, any specific reclassification you make, or any sector-tagging
edge case). Produce a short written report (similar in format to
PHASE0_COVERAGE_REPORT.md) covering all three deliverables — save it as
03_data/PHASE0B_FOLLOWUP_REPORT.md.

When all three deliverables are done, stop. Summarize the carry-forward split numbers,
list every reclassification you made (from -> to, with rationale), confirm meme-coin/NFT
handling, report sector-tag coverage by asset_class, and flag anything that still needs
a human decision. Do not proceed to Phase 1 without that review.
```
