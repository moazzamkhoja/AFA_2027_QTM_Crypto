# Data Decisions Log

Append an entry every time the empirical pipeline deviates from
`04_code/DATA_SPECIFICATION.md` — a proxy substitution, a classification judgment
call, a threshold that needed adjusting, a source that didn't pan out, or any
data-availability gap that forced a choice. This is the audit trail behind Section 3's
eventual prose and is part of the AFA-required documentation of the AI-assisted
research process.

Do not edit or delete past entries — append only, even if a later entry supersedes one.

---

## Entry Template

**Date:**
**Spec section affected:**
**Asset(s)/period affected:**
**What the spec wanted:**
**What was actually available:**
**Decision made:**
**Rationale:**
**Downstream impact (what should be re-checked if this decision changes):**

---

## Entries

### Entry 1 — Primary market-cap source: CoinMarketCap, not CoinGecko
**Date:** 2026-06-22
**Spec section affected:** 2.1, 2.4 (historical rankings / candidate sources)
**Asset(s)/period affected:** all assets, entire 2015-08→2026-05 history
**What the spec wanted:** point-in-time monthly top-N rankings (incl. delisted coins)
built primarily from CoinGecko historical data.
**What was actually available:** CoinGecko's *public* API caps historical queries at the
past 365 days (verified live: error 10012, "Public API users are limited to querying
historical data within the past 365 days"). Full history requires a paid plan; no API key
was available in the environment. CoinMarketCap's free `data-api/v3/cryptocurrency/
listings/historical` endpoint, by contrast, serves daily point-in-time ranked listings
back to ~2013-04-28, requires no key, includes assets as ranked on that date (delisted/
dead coins included), and returns market cap, price, volume24h, circulating/total/max
supply, and tags. Limit ≥1000 confirmed.
**Decision made:** use the CMC free historical listings endpoint as the ranking backbone
for Phase 0. (Human approved this substitution explicitly when the constraint was
surfaced.)
**Rationale:** it is the only freely available source that satisfies the Section 2.1
anti-survivorship requirement (point-in-time rankings including delisted assets) over the
full sample without a paid key.
**Downstream impact:** if a CoinGecko Pro key is later obtained, cross-check CMC market
caps against CoinGecko for discrepancies (Section 2.4 asks for a two-source cross-check;
only CMC was usable here). All universe membership decisions rest on CMC mcap values.

### Entry 2 — Artemis Analytics: no accessible free API (deferred)
**Date:** 2026-06-22
**Spec section affected:** 2.4 (sources), 4 (PQ for tokens, Phase 2)
**Asset(s)/period affected:** n/a (source availability)
**What the spec wanted:** Artemis used as a cross-chain on-chain fundamentals source.
**What was actually available:** `api.artemisxyz.com` returned HTTP 410 Gone;
`api.artemis.xyz` / `app.artemisanalytics.xyz` failed DNS resolution. No documented free
public API endpoint responded.
**Decision made:** defer Artemis to a later phase; do not block Phase 0 on it.
**Rationale:** Phase 0 needs only rankings + classification, which CMC + DeFiLlama cover.
**Downstream impact:** if Artemis fundamentals are wanted for PQ in Phase 2, this needs
authenticated/paid access to be revisited.

### Entry 3 — Monthly snapshot date = last calendar day (daily data available)
**Date:** 2026-06-22
**Spec section affected:** 2.2 (monthly frequency)
**Asset(s)/period affected:** all months
**What the spec wanted:** month-end monthly frequency.
**What was actually available:** CMC's historical endpoint serves *daily* snapshots
(verified: distinct payloads for consecutive dates), not just weekly.
**Decision made:** pull the snapshot dated the last calendar day of each month; if that
exact date is empty, walk back up to 6 days and stamp the served date in `_meta`.
**Rationale:** exact month-ends are available, removing the need to approximate with the
nearest weekly snapshot.
**Downstream impact:** none expected; served-vs-requested date is auditable per file.

### Entry 4 — CMC tags are current metadata, not point-in-time
**Date:** 2026-06-22
**Spec section affected:** 2.3 (classification)
**Asset(s)/period affected:** all assets (classification evidence)
**What the spec wanted:** time-aware coin/token classification with evidence.
**What was actually available:** CMC's `tags` reflect the asset's *current* metadata
(e.g. ETH is tagged `pos` today; BTC carries present-day VC-portfolio tags). They are not
snapshot-specific, so they describe the asset's end-state, not its state in month t.
**Decision made:** use the union of tags across snapshots as classification *evidence*
(asset-class is treated as static), but handle known time-varying cases explicitly with
dated overrides, and flag the limitation in the coverage report.
**Rationale:** tags are still the best available structured signal of asset function; the
end-state label is correct for most assets and the few transition cases are handled.
**Downstream impact:** Phase 1 staking-channel availability must respect transition dates
(e.g. ETH staking only from 2020-12), not the static `coin` label.

### Entry 5 — ETH PoW→PoS handled as a dated transition
**Date:** 2026-06-22
**Spec section affected:** 2.3 (ambiguous/transition cases)
**Asset(s)/period affected:** ETH (cmc_id 1027)
**What the spec wanted:** explicit handling of ETH's staking onset, dates verified.
**What was actually available:** established public record: Beacon Chain genesis
2020-12-01 (staking first possible via the deposit contract opened Nov 2020); Merge to
full PoS 2022-09-15.
**Decision made:** classify ETH as `coin` but attach `staking_start=2020-12-01` and a
`transition_note` recording no staking-based λ channel before 2020-12 and full PoS at the
2022-09-15 Merge.
**Rationale:** the staking λ channel is undefined for ETH in most of the sample; a static
label would mislead Phase 1.
**Downstream impact:** apply the same dated-onset logic to any other PoW→PoS transition
discovered in Phase 1; ETH is the worked example, not necessarily the only one.

### Entry 6 — Stablecoins excluded from the panel (ranking-inclusive)
**Date:** 2026-06-22
**Spec section affected:** 2.1, 2.3
**Asset(s)/period affected:** all stablecoins reaching top-250 (71 names)
**What the spec wanted:** a coin-vs-token universe; stablecoins are not addressed
directly by the functional cut.
**What was actually available:** stablecoins occupy real top-250 rank slots but have
~0 returns and degenerate λ, fitting neither H1a nor H1b.
**Decision made:** (human decision) exclude stablecoins entirely from the universe. They
are detected by the *exact* `stablecoin` CMC tag (substring matching wrongly catches
`stablecoin-protocol` governance tokens and `stablecoin-algorithmically-stabilized` =
LUNC, the Terra coin). Ranking is computed *inclusive* of stablecoins so the top-250
cutoff reflects true market structure; stablecoins are removed only from the output panel.
**Rationale:** keeps the cutoff economically meaningful while keeping degenerate assets
out of the tests. The functional cut is preserved: UST (stablecoin) excluded, LUNA/LUNC
(coin) retained including its collapse.
**Downstream impact:** the observed top-250 cross-section runs a few-to-low-tens below
250 in later years (stablecoins consume slots); reported in the coverage report.

### Entry 7 — Top-N threshold = 250; carry-forward for unobserved in-panel months
**Date:** 2026-06-22
**Spec section affected:** 2.1
**Asset(s)/period affected:** all
**What the spec wanted:** top-N entry (default 250), permanent retention, failures as
return realizations not missing data.
**What was actually available:** snapshots pulled to the top 1000, so an asset that drifts
below rank 250 but stays in the top 1000 is still observed; only below rank 1000 is price
visibility lost.
**Decision made:** N=250 (sensitivity at 200/250/300 reported). Once an asset enters it
stays in the panel; months where it is in-panel but absent from the top-1000 snapshot are
marked `status='carried_forward'` with the last observed price retained.
**Rationale:** satisfies the anti-survivorship rule while flagging (not hiding) the
visibility gap.
**Downstream impact:** Phase 3 must decide the death-return treatment for carried-forward
tails (final delisting return vs. constant carry). Flagged in coverage report §9.

### Entry 8 — Classification: tag-rules + DeFiLlama + curated native-coin override
**Date:** 2026-06-22
**Spec section affected:** 2.3
**Asset(s)/period affected:** all (esp. major L1 coins with thin/contaminated tags)
**What the spec wanted:** functional coin/token classification with evidence and flags.
**What was actually available:** CMC tags are inconsistent — some L1 coins (ATOM, AVAX,
DOT, FTM) carry `defi` ecosystem tags but no clean consensus tag; some governance tokens
(UNI) now carry `layer-1` (Unichain); LST governance tokens (LDO) carry LST ecosystem
tags. DeFiLlama category matching by symbol false-promotes some coins (DOT→Liquid Staking).
**Decision made:** rules engine with (a) exact consensus-tag set → coin; (b) `layer-1`/
`smart-contracts` → coin only when no `governance`/`dao` tag; (c) explicit `governance`/
`dao` → token (wins over ecosystem tags); (d) DeFiLlama promotion to token only on genuine
DeFi categories (Dexs/Lending/CDP/Yield/Derivatives…); (e) a curated `NATIVE_COIN_OVERRIDE`
(22 ids verified against the data as each symbol's highest-peak-mcap instance) forcing
major native coins (XRP, XLM, etc.) to `coin`. Every non-clean case carries
`ambiguous_flag=True`.
**Rationale:** no single tag rule is reliable given CMC's metadata; combining rules +
DeFiLlama + a small documented manual override correctly classifies all spot-checked
majors while flagging the long tail for review.
**Downstream impact:** the `other`/ambiguous bucket (large by raw name count, small by
observed asset-months) needs a manual confirmation pass for any asset that actually
enters the tests. LINK is left `other` (oracle token — neither a clean coin nor a
governance token).

### Entry 9 — Ranking recomputed by market cap among the returned set
**Date:** 2026-06-22
**Spec section affected:** 2.1
**Asset(s)/period affected:** all
**What the spec wanted:** "rank all tracked assets by market cap" each month.
**What was actually available:** CMC returns a stored `cmcRank` plus market caps.
**Decision made:** recompute rank by descending market cap among the returned set rather
than trusting `cmcRank`; drop rows with null/≤0 market cap.
**Rationale:** matches the spec wording exactly and is robust to any stored-rank quirks.
**Downstream impact:** ranks are internally consistent with the market-cap values used
for entry decisions.
