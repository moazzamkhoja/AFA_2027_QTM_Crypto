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

### Entry 10 — Carry-forward death-return treatment: split before deciding
**Date:** 2026-06-22
**Spec section affected:** 2.1 (retention rule); Phase 3 (returns)
**Asset(s)/period affected:** all `status='carried_forward'` asset-months
**What the spec wanted:** Phase 0 flagged this as open (PHASE0_COVERAGE_REPORT.md §9.1)
rather than resolving it — Phase 3 needs a final death-return policy.
**What was actually available:** no breakdown yet of how many carried-forward
asset-months are presumed-failed (asset never reappears in the top-1000 through the end
of the sample) versus temporarily-out (asset reappears later — a visibility gap, not a
failure).
**Decision made:** before any return-treatment formula is chosen, produce the
presumed-failed vs. temporarily-out split with counts (and the longest temporarily-out
gap observed). Decide the formula only after seeing those counts. This is a precursor
task, run before Phase 1 channel work, not deferred all the way to Phase 3.
**Rationale:** choosing a death-return convention blind, before knowing whether
carried-forward months are mostly real failures or mostly short visibility gaps, risks
picking a treatment that's wrong for the dominant case.
**Downstream impact:** Phase 1 (λ channels) and later phases should not compute
return-dependent statistics over carried-forward months until this split is reviewed.

### Entry 11 — Manual classification review scoped by persistence, not market cap
**Date:** 2026-06-22
**Spec section affected:** 2.3 (classification)
**Asset(s)/period affected:** `other`/`ambiguous_flag=True` assets only
**What the spec wanted:** a manual confirmation pass for classifications that will
actually enter the tests.
**What was actually available:** 874 names are `other`; reviewing all of them by hand is
not tractable, and most are one-or-two-month pump-and-dump blips that already passed the
top-250 market-cap gate but contribute negligible weight to any regression.
**Decision made:** scope the manual review to `other`/ambiguous names with **≥12 observed
asset-months** (a persistence filter, separate from and applied after the existing
market-cap-based top-250 entry rule). Names below this persistence threshold are left
unreviewed.
**Rationale:** concentrates review effort on the names that could actually move a
result; the unreviewed short-lived tail is, by construction, too thin to matter
statistically.
**Downstream impact:** any `other`/ambiguous name below the 12-month threshold that later
turns out to matter (e.g., because of a methodology change) should be reviewed at that
point, not assumed correctly classified.

### Entry 12 — Meme coins: no change, current 'other' handling confirmed
**Date:** 2026-06-22
**Spec section affected:** 2.3 (classification), 2.1 (ranking)
**Asset(s)/period affected:** meme coins (DOGE, SHIB, PEPE, etc.) and similar
non-economic-output assets
**What the spec wanted:** a coin/token functional cut; meme coins/NFTs were raised as a
potential third category not addressed directly by that cut.
**What was actually available:** meme coins already land in `other` (no staking
mechanism, no governance mechanism) and are already excluded from H1a/H1b/H3 by that
classification; they still count toward the top-250 ranking, the same treatment already
applied to stablecoins. NFTs are presumed absent from the CMC fungible-token listings
source entirely (not the same product as CMC's NFT tracking) — to be explicitly
confirmed in Phase 1, not assumed.
**Decision made:** keep current handling — no Phase 0 changes. Confirm NFT absence as a
Phase 1 verification step.
**Rationale:** meme coins are already functionally excluded from the hypothesis tests by
the existing classification; stripping them from the panel entirely (vs. leaving them
visible as `other`) would have no effect on results and would reduce audit transparency.
**Downstream impact:** none expected. If NFT-like entries are found in Phase 1, log and
exclude them explicitly rather than assuming this entry covers it.

### Entry 13 — Quadrant median splits computed within asset class, not pooled
**Date:** 2026-06-22
**Spec section affected:** 4 (Growth-Levelized NVT), main.tex Section "The Quadrant
Portfolio" (H3); affects Phase 4 design, not Phase 1 build work directly
**Asset(s)/period affected:** all coin and token observations entering H3
**What the spec wanted:** H3 reports coins and governance tokens separately; the spec did
not specify whether the λ/(1-λ) and Growth-Levelized NVT median splits defining the
Star/Avoid quadrants should be computed pooled or within each class.
**What was actually available:** coins (security-staking norms) and governance tokens
(DeFi vote-escrow/governance-staking norms) plausibly have structurally different
λ/(1-λ) distributions for reasons unrelated to conviction, which could let one class
mechanically dominate "high λ" under a pooled median.
**Decision made:** compute the high/low median splits for both λ/(1-λ) and
Growth-Levelized NVT separately within coins and within tokens each month, not pooled.
**Rationale:** keeps the Star/Avoid sort meaningful as a within-class signal rather than
an artifact of cross-class composition differences.
**Downstream impact:** this is a Phase 4 (portfolio assembly) specification, recorded now
so it isn't decided ad hoc later; revisit if Phase 1's actual λ distributions show the
two classes don't differ enough to matter.

### Entry 14 — Artemis Analytics / paid CoinGecko access deferred
**Date:** 2026-06-22
**Spec section affected:** 2.4, 4 (PQ for tokens, Phase 2)
**Asset(s)/period affected:** n/a (source access)
**What the spec wanted:** a decision on whether to pursue paid access now.
**What was actually available:** no free API for either source (see Entry 2); not needed
until Phase 2 (PQ construction) or for the Section 2.4 two-source market-cap cross-check.
**Decision made:** defer; revisit only when Phase 2 actually needs it.
**Rationale:** no Phase 0/1 work depends on it; premature procurement.
**Downstream impact:** Phase 2 kickoff should re-raise this explicitly rather than
assuming it's been resolved.

### Entry 15 — Universe size N=250 confirmed, no change
**Date:** 2026-06-22
**Spec section affected:** 2.1
**Asset(s)/period affected:** all
**What the spec wanted:** confirmation of the default top-N threshold.
**What was actually available:** rank-sensitivity table (200/250/300) showing the live
cross-section is not drastically different across these thresholds.
**Decision made:** keep N=250.
**Rationale:** no evidence yet that a different threshold is needed; can revisit once
Phase 1 λ-channel coverage is known.
**Downstream impact:** none; flagged for revisit only if Phase 1 coverage suggests
otherwise.

### Entry 16 — Sector/economic-function classification added as a second, independent dimension
**Date:** 2026-06-22
**Spec section affected:** new 2.6 (added); clarifies that Entry 13's "class" (coin vs.
token) is a separate dimension from this one
**Asset(s)/period affected:** all assets
**What the spec wanted:** prior to this entry, the spec only defined one classification
axis — the binary, functional coin/token cut (2.3), which Entry 13 then used as "the"
class for the H3 quadrant median splits.
**What was actually available:** the user clarified that "class" should also mean
something narrower than coin/token — e.g., L1 vs. L2, DEX vs. Perpetuals/Derivatives,
Lending vs. CDP vs. Liquid Staking — a sector/economic-function tag, not a refinement
or replacement of the coin/token cut. A quick check of the existing Phase 0 output shows
the raw ingredients for this already exist as classification evidence: 574/2010 assets
in `classification_table.csv` carry a `defillama_categories` value (154 Dexs, 78 Yield,
59 Derivatives, 53 Lending, 34 Canonical Bridge, 20 Liquid Staking, 17 CDP, etc.), and
134/2010 carry a `layer-1` CMC tag with 43 carrying `layer-2` — i.e., DeFiLlama
categories give DEX/Lending/Derivatives/Staking-type resolution for protocol tokens,
and CMC tags give L1/L2 resolution mostly for base-layer coins that DeFiLlama doesn't
track. Neither source alone covers the whole universe; coverage is partial either way.
**Decision made:** add a second, independent classification field (`sector`/`category`)
populated from DeFiLlama categories + CMC tags, captured now as a coverage/data task
(new spec section 2.6). Explicitly defer deciding which sector-level comparisons (DEX
vs. Perp, Lending vs. Staking, L1 vs. L2, or others) will actually be tested in the
paper — that choice is a later judgment call once Phase 1-4 data exists, not a Phase 0/1
data-capture decision. Entry 13's coin/token median splits are unaffected by this entry;
"class" in Entry 13 refers only to the coin/token cut.
**Rationale:** the marginal cost of capturing this field now (it's mostly already
present in classification evidence pulled in Phase 0) is far lower than the cost of
re-deriving it later if a sector-level comparison turns out to matter; deferring the
analytical decision (which comparisons to run) avoids designing an analysis around a
taxonomy that hasn't been validated against real coverage yet.
**Downstream impact:** the Phase 0 follow-up session should add a sector/category field
and report coverage by `asset_class` (coin/token/other) per new spec section 2.6, before
Phase 1 (lambda channels) begins. Section 3 prose, once written, should describe both
classification dimensions as independent.
