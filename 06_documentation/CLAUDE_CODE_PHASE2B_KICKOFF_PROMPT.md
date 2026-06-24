# Claude Code Kickoff Prompt — Phase 2b: PQ for the 81 coins DeFiLlama can't cover

Paste the prompt below as the first message in a new Claude Code session, working directory
`C:\AFA_2027_QTM_Crypto`. Phase 2 (session 013) built NVT_GL for every asset it could source PQ
for, and **deliberately deferred 81 material coins** whose transacted value is not on DeFiLlama
and whose only ladder option (Artemis Settlement Volume, Entry 32 Rung 2) turned out **paid-only**.
This session sources those 81 coins. It does **not** touch tokens or the NVT_GL machinery — both
are done and correct; this only fills the `pq_coins.csv` GAP-R2 rows and re-runs the assembly.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0/0B/1 are complete; Phase 2
(session 013) is complete except for 81 coins flagged GAP-R2 (PQ=NaN). Before doing anything else,
read in full:

1. 03_data/PHASE2_COIN_PQ_VERIFICATION_B1.md — why these 81 coins have no free DeFiLlama PQ, the
   materiality threshold used, and the Artemis-paid-only finding.
2. 03_data/phase2_coin_rung_table.csv — the per-coin rung table; the rows with rung == 'GAP-R2'
   are this session's targets (81 material coins: XRP, DOGE, LTC, BCH, XMR, ZEC, DASH, ATOM, DOT,
   MATIC, VET, THETA, FIL, IOTA, NEO, ETC, BSV, XTZ, KAS, …).
3. 04_code/DATA_DECISIONS_LOG.md Entries 30, 31, 32, 33, 34 — PQ = transacted value (not toll/TVL),
   the coin source ladder, and what session 013 built + deferred.
4. 03_data/PHASE2_COVERAGE_REPORT.md §1b, §4 — the coin ladder as actually applied.

## The object you are sourcing
Per Entry 30/32: PQ = transacted value (the dollar flow that moved on-chain), sector-appropriate.
For these coins that means NATIVE SETTLEMENT VALUE (on-chain payment/transfer value in USD), the
coin-side analogue of Bitcoin's NVT denominator — NOT fees (a toll, rejected Entry 30), NOT DEX
volume (degenerate for these chains, the whole reason they're here), NOT TVL.

## Source plan (verify each live before building, exactly as Phase 1/2 did)
Work the ladder per coin; log the rung actually used per coin in the coverage report.

1. **XRP (cmc_id 52)** — the single highest-value uncovered coin. XRP Ledger exposes payment
   volume natively: check live the XRPL Data API / data.ripple.com successor, xrpscan, or
   xrplmeta for a historical USD (or XRP) payment-volume series. XRPL DEX volume is also on-ledger.
   This is a Rung-3-native series, not raw block iteration.
2. **UTXO payment coins (LTC, BCH, DOGE, DASH, BTG, BSV, XEC, DGB, RVN, ZEC, XVG, …)** — same
   *type* of series blockchain.com gives BTC (Estimated Transaction Value, change-excluded). Check
   live whether a free/keyless equivalent exists per chain: bitinfocharts ("sent in USD"),
   blockchair stats, or each coin's own explorer charts API. Confirm whether change outputs are
   excluded; if only a change-inflated "total sent" exists, flag it (parallel to the BTC caveat).
3. **Cosmos/IBC + app-chains (ATOM, OSMO-already-done, TIA, INJ-already-done, KAVA-already-done,
   …)** — check Mintscan / Cosmos REST for transfer/IBC volume where DeFiLlama chain DEX was
   degenerate. Several Cosmos chains may already be R1; only do the ones still GAP-R2.
4. **DOT/KSM/Polkadot parachains, and other non-EVM (NEO, ICP-done, VET, IOTA, XTZ, EGLD-done,
   FIL, KAS, …)** — per-chain check for a native transfer-value series; many will have none free.
5. **XMR (Monero)** — STOP: RingCT cryptographically hides transaction amounts. Native transacted
   value is unobservable on ANY source. Mark permanently NaN with that reason; do not proxy it.
6. **Artemis Settlement Volume (paid)** — only if the user has by now procured API access and put a
   key in 04_code/.api_keys.json under "artemis". Then it covers most of these at once. Use
   Settlement Volume ONLY, never the Total Economic Activity composite (it bundles Chain Fees &
   MEV + Application Fees — toll measures rejected for tokens). If no key present, skip Artemis.

## Rules (unchanged from Entry 32 / spec §0)
- Verify free access live before building; log every dead/paywalled source.
- Where a coin has a confident native transacted-value series → fill PQ, note the rung+source.
- Where only a toll measure (chain fees) or a change-inflated proxy exists → flag it explicitly in
  a column (Rung 4 / "toll-based" or "change-inflated"), do NOT let it blend in silently.
- Where nothing free and credible exists → leave PQ=NaN with the reason. Flag, don't guess.
- Do NOT attempt full multi-year native block iteration across chains (the call-volume wall,
  Entry 31/32) — a ready-made series or an API, or NaN.

## Deliverable
Append the newly-sourced GAP-R2 coins into 03_data/phase2/pq_coins.csv (replace their NaN marker
rows with monthly PQ rows; keep the rung/source columns honest), then re-run
04_code/phase2_nvt_gl.py to extend the NVT_GL panel, and 04_code/phase2_pq_diagnostics.py if TVL
applies. Update PHASE2_COVERAGE_REPORT.md headline + §1b with the new coin coverage and per-coin
rungs. Continue DATA_DECISIONS_LOG.md from Entry 35; log session as
06_documentation/ai_conversations/session_014_*.md; update time_log.md. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main). Do not start Phase 3 without review.
```
