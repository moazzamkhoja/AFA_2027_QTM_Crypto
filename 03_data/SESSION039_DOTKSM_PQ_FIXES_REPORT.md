# Session 039 Report — DOT/KSM PQ probe; TRX staking-type fix; WARP identity review

**Date:** 2026-07-28
**Kickoff:** `04_code/CLAUDE_CODE_SESSION039_DOTKSM_PQ_FIXES_PROMPT.md`
**Decisions log:** Entry 90
**Model/interface:** Fable 5 via Claude Code CLI (autonomous run)

---

## Task A — DOT/KSM PQ source probe: NEGATIVE (no free source)

Goal: annualized on-chain transfer volume in USD (pq_usd) for DOT (6636) and
KSM (5034), the only gap keeping them from regression-ready.

### A1 — Subscan `/api/scan/daily` (key on file, same as ch1)

| Probe | Result |
|---|---|
| `format=month`, any category | HTTP 400 `format must be one of [day hour 6hour]` |
| `format=day`, 2020-08..2026-06, categories transfer / extrinsic / transaction / fee, both polkadot + kusama | HTTP 403 `history_window_exceeded` (all 8 combinations) |
| `format=day`, 2026-06-01..2026-06-30 (30 d) | 200, n=30 — keys: `time_utc, total, transfer_amount_total, balance_amount_total` |
| `format=day`, 2026-04-01..2026-06-30 (90 d) | 403 `history_window_exceeded` |

Free-tier history window ≈ **2 months** — the same wall session 037 hit for the
"Bonded" (staking) category. No multi-year history at any granularity.
Additionally the in-window data looks **degenerate**: 2026-06-01 returned
`total=3` transfers / `transfer_amount_total=5.98` DOT — plainly not
network-wide daily volume, so even the 2-month window would be unusable.

First 200 chars of the in-window response list:
`{"time_utc": "2026-06-01T00:00:00Z", ..., "total": 3, "transfer_amount_total": "5.9844520521", "balance_amount_total": "0"}`

### A3 — archive-RPC block iteration: NOT ATTEMPTED (forbidden, Entry 31/32)

### A4 — Blockchair polkadot/kusama (keyless)

| Probe | Result |
|---|---|
| `GET /polkadot/stats` | 200 — but `best_block_time: "2025-05-26"` (index FROZEN) |
| `GET /kusama/stats` | 200 — `best_block_time: "2025-05-09"`, `blocks_24h: 1` (FROZEN) |
| `GET /polkadot/calls?a=date(time),sum(value)&q=type(transfer)` | **404** (HTML Page Not Found) |
| `GET /kusama/calls?...` (same) | **404** |

Same no-aggregation-tables pattern as XTZ/MATIC (Entry 84). Decisive extra
finding: **both Blockchair Substrate indexes stopped updating in May 2025**, so
a paid Blockchair key could not cover the panel through 2026-06 regardless —
Blockchair is ruled OUT for DOT/KSM (do not include them in any support email;
that decision now concerns XTZ/MATIC only). Probing stopped at 4 keyless calls
(Entry-84 blacklist threshold).

**Verdict:** no free PQ source for DOT/KSM; candidates exhausted. Both stay
PARTIAL (gap = `pq_nvtgl` only, ch1 λ complete). Reopens only if Subscan Pro
(or another paid volume series) is procured — Moazzam decision.

Probe scripts: `04_code/s039_probe_subscan.py`, `s039_probe_subscan2.py`,
`s039_probe_blockchair.py`.

---

## Task B — TRX (1958) coin_staking_type fix

- **Where the label lived:** `03_data/universe_coverage_status.csv` itself.
  `build_coverage_status.py:33` carries `coin_staking_type` forward from the
  previous file version (static chain metadata first classified session 022 —
  no live source regenerates it), so the stale `pow_only` self-perpetuated.
- **Change:** CSV row edited `pow_only` → `pos` (TRON = DPoS, a PoS variant;
  ch1 TronScan freezeresource series, 78 λ months). Builder re-run.
- **Effect:** TRX `coverage_status` stays `complete`, but now derives via the
  pos-coin λ∩NVT same-month path (58 overlap months) instead of the
  pow_only NVT-alone path. λ-panel inclusion untouched (was already correct).
- **Counts:** coverage totals unchanged (189/315/1,435 at that point).
  Regression-ready coins now derive **cleanly to 22 with TRX included**
  (complete coins 33 − 11 pow_only-NVT-only = 22) — resolving the Entry-88
  "narrative 21 vs file 20" ±1 bookkeeping discrepancy. Headline 178 unchanged.

---

## Task C — WARP (1166) identity review: PERMANENT MISMATCH, CLOSED

- **Checkpoint** (`03_data/raw/phase1_onchain/holding/1166_WARP.json`):
  chainid 1, address `0x83e6f1E41cdd28eAcEB20Cb649155049Fac3D5Aa`,
  **n_transfers = 0** across 27,257 getLogs calls, 0 monthly rows.
- **CMC identity** (cached `03_data/raw/cmc_detail/1166.json`): id 1166 =
  "WARP", slug `warp`, **category "coin"**, dateAdded 2016-02-03, status
  **inactive**, latest update 2018-05-08, supply 1,095,224, website
  warpcoin.com, explorer chainz.cryptoid.info/warp — a 2016-era standalone
  PoS altcoin with its own chain. **It never deployed an ERC-20 token.**
- **Diagnosis:** the stored Ethereum contract belongs to a different, later
  "WARP"-named token (symbol collision); the `polkastarter` dl_slug came from
  DeFiLlama's registry, whose polkastarter entry wrongly lists cmcId 1166
  (Polkastarter = POLS, cmc 7208) — the Entry-52 collision, now acted on.
- **Actions:**
  1. `phase1_build_identity_map.py`: new `BAD_DL_CMCID = {"1166"}` override
     drops the bad registry match so identity rebuilds can't resurrect it.
  2. Identity CSV row cleared (dl_slug / dl_category / token_address /
     token_chain(s) / gecko_id blanked; dl_matched=False, has_address=False).
  3. **54 bogus polkastarter TVL months purged** from
     `03_data/phase2/tvl_panel.csv`: 8,120 → 8,066 asset-months,
     163 → 162 assets.
  4. Coverage status: partial → **not_started**.
- No λ rows ever existed for 1166 (the empty checkpoint contributed nothing),
  so the λ panel is unaffected. The checkpoint file is retained as the record
  of the burned probe.

---

## Post-assemble totals

| Metric | Pre-039 | Post-039 |
|---|---|---|
| λ asset-months / assets | 13,510 / 463 | **13,510 / 463** (unchanged) |
| tvl_panel | 8,120 mo / 163 assets | **8,066 mo / 162 assets** (WARP purge) |
| Coverage (complete/partial/not_started) | 189 / 315 / 1,435 | **189 / 314 / 1,436** (WARP) |
| Regression-ready | 178 (coins 22, tok/other 156) | **178 (coins 22, tok/other 156)** — now internally consistent |

## Open items (session 040+)

- Cosmos key → CRO/INJ/SEI/KAVA ch1 (unchanged).
- Blockchair support email: **scope reduced to XTZ/MATIC only** (DOT/KSM ruled
  out this session — frozen index).
- DOT/KSM PQ: reopen only on a Subscan Pro (or equivalent paid) decision.
- Bibliography sanity-check (carried).
