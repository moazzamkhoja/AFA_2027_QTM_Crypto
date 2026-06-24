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

### Entry 17 — Carry-forward split rule: subtype by last-observation, right-censoring flagged
**Date:** 2026-06-22
**Spec section affected:** 2.1 (retention); implements Entry 10
**Asset(s)/period affected:** all `status='carried_forward'` asset-months (89,535)
**What the spec wanted:** Entry 10 asked for a presumed_failed vs temporarily_out split
with counts, before any death-return formula is chosen.
**What was actually available:** the panel records each asset-month's status; whether a
carried_forward month is a closed visibility gap vs a terminal failure is recoverable
from the asset's own observed-month timeline.
**Decision made:** for asset *j* with last observed month L_j, a carried_forward month
at *t* is `temporarily_out` iff *t* < L_j (a later observation exists, so the gap
closes) and `presumed_failed` iff *t* >= L_j (trailing tail with no later observation).
Stored in a new column `carry_forward_subtype` (the `status` column is untouched). The
right-censoring risk is flagged explicitly: a presumed_failed asset whose *terminal* gap
(months from L_j+1 to the 2026-05-31 sample end) is no longer than the longest observed
temporarily_out gap could, in principle, still be a case that would have reappeared had
the sample run longer — so "never seen again so far" is NOT silently equated with
"permanently dead." Reported at several thresholds (terminal gap <= max/median
temporarily_out gap; <=3/6/12 months; and gaps that only started in the last 6/12/24
months). Script: `04_code/carry_forward_split.py`.
**Rationale:** the rule is exactly equivalent to a gap analysis but vectorisable and
unambiguous at the sample boundary, which is precisely where the death-vs-gap call is
hardest. Producing the right-censoring counts (rather than a single death/alive label)
keeps Entry 10's deferral honest.
**Downstream impact:** the death-return formula (Phase 3) should be chosen with these
counts in hand. Key numbers: 81,167 presumed_failed vs 8,368 temporarily_out
asset-months; 2,107 closed gaps (median 1 mo, max 47 mo); 1,399 presumed_failed assets
of which 98 have a trailing gap <=6 months (started after 2025-11-30) and 166 <=12
months — these are the right-censoring-exposed names a naive "dead = never seen again"
rule would misclassify.

### Entry 18 — Classification confirmation pass: 16 conservative reclassifications
**Date:** 2026-06-22
**Spec section affected:** 2.3; implements Entry 11
**Asset(s)/period affected:** `other`/ambiguous assets with >=12 observed asset-months
(630 candidates)
**What the spec wanted:** a manual confirmation pass proposing keep-other / coin / token
with a one-line rationale, not inventing classifications that can't be supported.
**What was actually available:** the 630 candidates are overwhelmingly genuine
utility/sector tokens (AI, gaming, payments, DePIN, storage, identity, exchange, meme).
A small set were mis-left as `other` by the first-pass tag rules: (a) native PoS/DPoS
chains whose CMC tags carried 'platform'/ecosystem labels or a non-standard consensus
tag (e.g. Symbol's 'posplus'), or whose DeFiLlama category mislabelled the base chain
(Kusama->"Liquid Staking", Kujira->"Liquidations", Polygon/Dymension->"Chain"); and
(b) one DeFi bridge governance token (STG, veSTG fee-share) in a bridge category the
first pass didn't promote.
**Decision made:** flip 16 names with individually verifiable mechanisms — 15 other->coin
(KSM, POL, DYM, KUJI, XYM, IOST, STEEM, ARDR, QKC, VLX, WICC, NEBL, UOS, CENNZ, WTC) and
1 other->token (STG) — applied to `classification_table.csv` (original label preserved in
new column `asset_class_original`; reason in `confirmation_basis`; `ambiguous_flag`
cleared on flips). A further 16 genuinely ambiguous names are left `other` WITH a note
(`confirmation_basis` "gray-zone"): L2 gas/governance tokens with no security-staking and
no vote-escrow lock (OP, MNT, MANTA, IMX), LST-protocol tokens kept out per Entry 8 (RPL,
ANKR, SSV, STRD), weak/edge native chains (EWT PoA, GBYTE DAG no-reward, FCT), NFT-market
governance tokens (BLUR, LOOKS, ME), a juror-staking work token (PNK), and a
symbol-collision case (PTS). The remaining 598 stay `other` with an auto-generated
sector rationale. Full per-asset proposals: `03_data/classification_confirmation_review.csv`.
Script: `04_code/classify_confirmation_pass.py`.
**Rationale:** the spec explicitly forbids inventing unsupportable labels and asks
ambiguous names to be left `other` with a note; flipping only mechanism-verifiable native
chains + one clear veToken, and documenting the gray zone, maximises correctness without
contaminating H1a/H1b with forced labels.
**Downstream impact:** in-universe class counts move coin 618->633, token 447->448,
other 874->858. Re-running `classify_assets.py` regenerates the table from scratch and
must be followed by `classify_confirmation_pass.py` to re-apply this layer. The gray-zone
16 (esp. OP/MNT/IMX/MANTA L2 tokens and the LST tokens) should be revisited in Phase 1
once staking/lock data is actually pulled.

### Entry 19 — Meme/NFT handling confirmed; meme over-promotions flagged (not changed)
**Date:** 2026-06-22
**Spec section affected:** 2.3; confirms Entry 12
**Asset(s)/period affected:** meme-tagged assets (84 in-universe) and NFT-tagged assets
**What the spec wanted:** confirm meme coins land in `other` and aren't mis-flagged as
coin/token, and confirm no actual NFT collection exists in the panel.
**What was actually available:** of 84 meme-tagged in-universe names, 58 are `other`, 21
`token`, 5 `coin`. The 5 coins (DOGE, MONA, MEME[1191], TRUMP[1185], M=MemeCore) are
genuinely mineable/PoS coins — `coin` is functionally CORRECT (they earn mining/staking
seigniorage), not a mis-flag. Of the 21 tokens, some are real DeFi protocols with
meme-style names (SUSHI) where `token` is correct, but others (SHIB, FLOKI, BabyDoge,
ELON, MEW, SNEK, …) are memes promoted to `token` via an *attached* DEX/farm DeFiLlama
category — arguably over-promoted under a strict Entry-12 reading. For NFTs: 112 names
carry 'collectibles-nfts'/NFT tags, but all are FUNGIBLE tokens of NFT-ecosystem projects
(MANA, SAND, APE, BLUR, IMX, …); none is a non-fungible collection. The CMC fungible
listings source does not list NFT collections (that is CMC's separate NFT product).
**Decision made:** per Entry 12, make NO meme reclassifications in this pass (memes among
the 630 `other`/ambiguous candidates correctly stay `other`; the mineable meme-coins
correctly stay `coin`). The meme tokens over-promoted via attached DEX/farm categories
are FLAGGED for human review but left as-is (demoting existing coin/token is out of this
deliverable's scope, which only reviews `other` candidates). Confirm explicitly: no
NFT collection (non-fungible) is present in the panel.
**Rationale:** the mineable meme-coins legitimately differ from pure ERC-20 memes; a
blanket "meme -> other" would wrongly strip DOGE/MONA of a real seigniorage mechanism.
The DEX-attached meme-token promotions are a genuine edge worth a human decision but not
a clear error to auto-correct here.
**Downstream impact:** if a strict "all memes -> other regardless of attached protocol"
rule is later preferred, the flagged token-promoted memes (SHIB, FLOKI, BabyDoge, ELON,
MEW, SNEK, PONKE, VOLT, …) are the names to revisit. NFT absence is now confirmed, closing
the Entry 12 Phase-1 verification item.

### Entry 20 — Sector field: DeFiLlama categories + curated CMC sector-tag whitelist
**Date:** 2026-06-22
**Spec section affected:** new 2.6; implements Entry 16
**Asset(s)/period affected:** all assets in `classification_table.csv`
**What the spec wanted:** a second, independent `sector` field from DeFiLlama categories
(primary) + CMC tags (fallback), both kept where both fire, blank where neither, with
coverage reported by asset_class.
**What was actually available:** `defillama_categories` already populated for 566/1939
in-universe assets; CMC tags carry sector-like signals (layer-1 134, layer-2 43, privacy
91, depin 62, meme 83, …) mixed with non-sector noise (ecosystem/portfolio/listing/
governance tags).
**Decision made:** `sector` = DeFiLlama categories carried in as-is (multi-value,
semicolon-separated) UNION a curated CMC-tag->label whitelist (`SECTOR_TAG_MAP` in
`04_code/build_sector_classification.py`), deduped. The whitelist deliberately EXCLUDES
governance-axis tags ('governance','dao','defi') and all ecosystem/portfolio/listing
tags — those are not sectors. Blank where neither source fires (no name-based guessing).
Coverage: 1113/1939 (57.4%) get a sector; by class coin 54.5% (leans on CMC L1/L2/
smart-contract tags — 184 CMC-only), token 89.7% (leans on DeFiLlama — 146 DL-only +
175 both), other 42.7% (282 CMC-only); residual 826 (42.6%) with no signal — exactly the
lean the spec anticipated.
**Rationale:** matches 2.6's intent (capture the field now, defer which comparisons get
tested); keeping both sources and excluding the governance axis preserves orthogonality
to the coin/token cut.
**Downstream impact / CAVEAT:** the DeFiLlama join is by ticker SYMBOL (inherited from
`classify_assets.py`), not a unique protocol id, so short/common tickers over-attribute
categories — e.g. BTC inherits "SoFi;Reserve Currency;Canonical Bridge" from unrelated
protocols sharing the symbol. This adds noise to a few coins' DeFiLlama-sourced sector
tags (the CMC-tag-sourced parts, e.g. BTC's Layer-1/Privacy, are clean). If sector tags
are used analytically in a later phase, de-noise the symbol-matched DeFiLlama categories
for base coins (or re-join DeFiLlama by protocol id/chain) before relying on them.

### Entry 21 — Phase 1 source verification: live free-access audit of all λ-channel sources
**Date:** 2026-06-23
**Spec section affected:** 3 (λ channels), 2.5 (per-asset data sources); spec Section 3
step 3 explicitly requires verifying current free access of every source *before*
building on it.
**Asset(s)/period affected:** n/a (source-availability audit gating the whole of Phase 1)
**What the spec wanted:** per-chain explorers (Etherscan/beaconcha.in, Solscan, …),
staking dashboards, DeFiLlama locked supply, and Snapshot/Tally/Boardroom for voting —
each verified live, not assumed.
**What was actually available (probed live 2026-06-23):**
- **CoinMarketCap historical listings** (Phase 0 backbone) — still serves month-end
  circulating/total supply per asset; this is the denominator source for the λ ratios.
- **DeFiLlama `/protocols` + `/protocol/{slug}`** — free, keyless, WORKS. Per-protocol
  payload carries token-denominated `*-staking` chainTvl buckets (e.g. `Ethereum-staking`
  → `{"CRV": 855M}`), a numeric `cmcId`, and a `governanceID` (Snapshot space). USED ONLY
  AS A REGISTRY/ADDRESS-BOOK (see Entry 22), not as the λ measurement.
- **Snapshot GraphQL** (`hub.snapshot.org/graphql`) — free, keyless, WORKS. Returns
  proposals with `created/start/end/state/votes/scores_total` per space. This IS the
  canonical source for off-chain DAO voting (gasless signed messages stored by Snapshot),
  not an aggregator — adopted for Channel 3.
- **Etherscan V2** (`api.etherscan.io/v2/api`) — V1 is fully DEPRECATED/dead ("switch to
  V2"). V2 REQUIRES AN API KEY. A free key (one key spans ~60 EVM chains via `chainid`)
  was obtained from the user ("AFA Paper" key) and stored gitignored at
  `04_code/.api_keys.json`. Verified working: `account/balance`, `block/getblocknobytime`,
  `proxy/eth_call`, `logs/getLogs` all return 200/OK.
- **beaconcha.in** (ETH staking dashboard) — now returns 401 "valid API key required";
  free no-key access GONE. **Boardroom** (`api.boardroom.info`) — 401 Unauthorized; needs
  a key. Both logged as paywalled; not used.
- **Free public RPCs** (cloudflare / publicnode / ankr / llamarpc / 1rpc) — serve only
  *latest* state; EVERY ONE blocks archive/historical queries ("Archive requests require a
  paid plan" / "must authenticate"). Confirms no keyless historical state path.
- **CRITICAL — Etherscan V2 free `eth_call` is silently latest-only:** historical
  `eth_call` at a past `tag` (block) returns the *current* value with no error (beacon
  deposit `get_deposit_count()` and a UNI `balanceOf` were byte-identical at the merge
  block, an early-2021 block, and latest). So historical *state reads* are unavailable on
  the free tier; only `getLogs` (immutable event history) gives genuine point-in-time data.
**Decision made:** (1) Channel 1 historical staked/locked supply must be reconstructed
from **event logs** (`getLogs`), never from historical `eth_call`/`balanceOf` state reads.
(2) Channel 3 voting from Snapshot GraphQL (canonical). (3) beaconcha.in/Boardroom/Tally
treated as paywalled — ETH staking comes from the deposit contract's on-chain Deposit
event logs instead of beaconcha.in. (4) DeFiLlama is a metadata registry only.
**Rationale:** satisfies the spec's "verify before building" rule and the user's
directive to source the λ numbers from the canonical chain/Snapshot data rather than an
aggregator, while honestly recording which originally-named sources are now paywalled.
**Downstream impact:** the no-archive constraint caps Channel 1 to assets reachable by
**event-log reconstruction on an EVM chain** (ETH native staking via the deposit contract;
EVM vote-escrow tokens via Transfer logs into a known escrow contract). Non-EVM native PoS
coins (Solana, Cosmos, Cardano, Tron, XRPL, …) are NOT reachable with this key and become a
documented coverage gap (Entry 24). If a paid archive-RPC/Etherscan-Pro tier is later
obtained, historical `eth_call`/`balancehistory` would allow direct point-in-time
balanceOf reads and broaden Channel 1 substantially.

### Entry 22 — Asset→on-chain-identity map: DeFiLlama used as a registry, not a data source
**Date:** 2026-06-23
**Spec section affected:** 2.5 (per-asset source identification); precursor to all λ channels
**Asset(s)/period affected:** all in-universe assets (1,939)
**What the spec wanted:** identify, per asset, the canonical chain explorer / token
contract / governance venue from which to pull the λ series.
**What was actually available:** to reconstruct on-chain numbers we first need each
`cmc_id`'s token contract address + chain (for Channel 1 log reconstruction) and its
Snapshot space (Channel 3). Two keyless registries provide this metadata: (a) DeFiLlama
`/protocols` carries a numeric `cmcId`, a token `address`+`chain`, and a `governanceID`
(snapshot space); (b) CMC's own `data-api/v3/cryptocurrency/detail?id=` returns
`platforms[]` with `contractAddress`+chain per asset.
**Decision made:** build `03_data/phase1/asset_onchain_identity.csv` joining the universe
to DeFiLlama `/protocols` on `cmcId` (script `phase1_build_identity_map.py`). DeFiLlama is
used STRICTLY as an address-book/registry — the λ NUMBERS come from the chain (Etherscan
logs) and Snapshot, never from DeFiLlama TVL. Raw registry cached at
`03_data/raw/defillama/protocols.json`.
**Rationale:** satisfies the user's directive to source λ from canonical chain data while
still using a keyless directory to discover *which* contracts/spaces to read.
**Downstream impact / coverage:** DeFiLlama's `cmcId` is sparse — only 241/1,939 in-universe
assets matched, of which 206 carry a token address and just 35 a Snapshot space (token-class
123/448 addressed, 29/448 with a space; coins lean to native chains DeFiLlama doesn't list as
protocols). The thin auto-mapping is WHY the Channel-3 space map is hand-extended (Entry 25)
and Channel-1 locks are a curated set (Entry 26). A future improvement is to enrich the map
from CMC `detail.platforms[]` (cleaner per-asset contract coverage) to widen Channel 1 to
more EVM tokens without per-protocol curation.

### Entry 23 — Channel 1 (ETH native staking): beacon deposit-contract event-log reconstruction
**Date:** 2026-06-23
**Spec section affected:** 3.1 (staking/locking ratio); 2.3/2.5 (ETH transition, explorers)
**Asset(s)/period affected:** ETH (cmc_id 1027), 2020-12 onward
**What the spec wanted:** ETH staked supply per month from a staking dashboard
(beaconcha.in-style), respecting `staking_start=2020-12-01`.
**What was actually available:** beaconcha.in now requires a paid key (Entry 21); free-tier
historical `eth_call` is latest-only. The canonical, free, historical-correct source is the
Beacon Chain deposit contract's on-chain `DepositEvent` logs.
**Decision made:** reconstruct month-end cumulative staked ETH from the deposit contract
(`0x0000…705Fa`) `DepositEvent` logs via Etherscan V2 `getLogs`, parsing the 8-byte
little-endian gwei `amount` from each event and cumulative-summing to each month-end block
(`block/getblocknobytime`). Pre-`staking_start` months are emitted as NaN (PoW, no channel),
NOT 0. Script `phase1_channel1_eth_staking.py` (resumable monthly checkpoints under
`03_data/raw/phase1_onchain/`). Validated against known levels: ~2.17M ETH staked at
2020-12-31 (67,906 deposits), ~5.2M at 2021-05-31 — both match public record.
**Rationale:** uses the chain itself; respects the dated transition; immutable logs sidestep
the no-archive constraint.
**Downstream impact / CAVEAT:** the deposit contract only RECEIVES ether — post-Shapella
(2023-04) validator exits/withdrawals are consensus-layer and do NOT debit it, so
cumulative-deposited OVERSTATES net active stake after 2023-04 (it is an upper envelope, a
monotone on-chain conviction proxy). For an exact net-staked series, a consensus-layer
(beacon) data source or a paid execution archive would be needed. Flagged in the coverage
report and in the output `note` column.

### Entry 24 — Channel 2 (holding duration / coin-age): NOT BUILT this phase (documented gap)
**Date:** 2026-06-23
**Spec section affected:** 3.2 (holding-duration channel)
**Asset(s)/period affected:** all assets, all months
**What the spec wanted:** an on-chain HODL-wave / coin-age proxy (share of supply unmoved
over a window, or average coin-age of moved supply) per asset-month.
**What was actually available:** computing coin-age requires the FULL transfer/UTXO history
of each chain (every address's last-active balance, or UTXO ages for BTC) reconstructed to
each month-end. For account chains that is the entire Transfer-log set of every token (orders
of magnitude beyond the targeted escrow-only logs used in Channel 1); for BTC it is the full
UTXO set age distribution. No free API serves ready HODL-wave series across the panel's chains
(Glassnode/CoinMetrics/Artemis are paid; the keyless explorers cap getLogs/archive as in
Entry 21).
**Decision made:** do NOT build Channel 2 this phase. Keep the `ch2_holding` column in the
λ schema (always NaN) so the structure is explicit, and flag it as the single largest λ-channel
gap. λ is therefore assembled from Channels 1 and 3 only in Phase 1.
**Rationale:** the spec (Operating Principle, §0) forbids silently substituting a weak proxy;
a credible coin-age series needs either a paid fundamentals API or a per-chain full-history
indexer, both out of scope for this pass. Better to flag the gap than ship an unsupportable
number — especially as §3.2 notes this would be the *only* channel for pre-2020 coins, so its
absence is exactly what gates early-sample coin λ.
**Downstream impact:** pre-2020 coins get NO λ at all in Phase 1 (no staking pre-PoS, no
voting, no coin-age). If a paid source (Glassnode/CoinMetrics) or a BTC/ETH full-node indexer
is later obtained, Channel 2 is the highest-value addition for early-sample coin coverage.

### Entry 25 — Channel 3 (voting): Snapshot GraphQL + curated space map + token-weight guard
**Date:** 2026-06-23
**Spec section affected:** 3.3 (voting engagement), 2.5 (governance venues)
**Asset(s)/period affected:** governance tokens with a Snapshot space (55 mapped)
**What the spec wanted:** monthly participation = voters / eligible supply, from
Snapshot/Tally/Boardroom for off-chain DAOs.
**What was actually available:** Snapshot GraphQL is free/keyless and IS the canonical store
of off-chain votes (Entry 21); Tally/Boardroom now need keys. DeFiLlama `governanceID` mapped
only 35 in-universe assets to spaces.
**Decision made:** (1) space map = DeFiLlama `governanceID` spaces (35) ∪ a curated,
name-verified set of 27 major DAOs keyed by EXPLICIT cmc_id (avoiding the symbol-collision
trap — e.g. Uniswap is 7083, not the symbol-matched 4113), written to
`03_data/phase1/snapshot_space_map.csv` (56 spaces). (2) Per space, page ALL closed proposals
(created-asc cursor) and aggregate by the month a proposal's voting ENDS. (3) Channel-3 value
= token-weighted turnout = mean(`scores_total`)/circulating supply (eligible base from the
Phase 0 panel). (4) **Token-weight validity guard:** spaces whose median voting-power-per-voter
(`scores_total/votes`) < 10 are 1-person-1-vote/ticket spaces where `scores_total` is NOT
token-denominated; their `vw_turnout` is nulled (flagged `token_weighted=False`). This caught
snxgov.eth, enzymefinance.eth, ilvgov.eth. Script `phase1_channel3_voting.py`; raw proposals
cached per space. Result: 55 distinct assets, 51 with a valid token-weighted turnout,
1,598 asset-months, 2020-07→2026-06.
**Rationale:** Snapshot is the real source, not an aggregator; explicit-cmc_id curation keeps
the join correct; the token-weight guard prevents a strategy artifact from contaminating the
z-scored channel.
**Downstream impact:** on-chain-only DAOs (Compound Governor beyond comp-vote, MakerDAO, and
tokens that vote purely on-chain: MKR, LQTY, PENDLE, RUNE, PERP, WLD, ONDO, ENA, …) are NOT on
Snapshot and are a documented gap — adding them needs on-chain Governor event reconstruction
(VoteCast logs), a later extension. Voting is absent pre-2020 and for pure coins, as the spec
anticipated.

### Entry 26 — Channel 1 (EVM vote-escrow/staking locks): curated escrow set, log-reconstructed
**Date:** 2026-06-23
**Spec section affected:** 3.1 (locking ratio for vote-escrow tokens)
**Asset(s)/period affected:** CRV, CVX, FXS, SUSHI, AAVE, YFI (6 EVM governance tokens)
**What the spec wanted:** locked supply for vote-escrow tokens (veCRV/veBAL-style) ÷ supply.
**What was actually available:** no free per-protocol "locked supply" time series (DeFiLlama
gives a `*-staking` USD bucket but that is the aggregator, not the chain; and historical
balanceOf is latest-only). Canonical method: locked supply at month-end = cumulative
(Transfer INTO the escrow) − (Transfer OUT of the escrow), from the base token's on-chain
Transfer logs (verified the Etherscan multi-topic filter `topic2`+`topic0_2_opr=and` isolates
escrow-directed transfers).
**Decision made:** reconstruct locked supply for a CURATED, high-confidence set of 6 escrows
where the contract holds the BASE token directly (so balanceOf(escrow)=locked): veCRV, vlCVX,
veFXS, xSUSHI, stkAAVE, veYFI (script `phase1_channel1_evm_locks.py`, addresses + mechanism in
the script header). EXCLUDED by design and documented (not silently proxied): **veBAL** (locks
an 80/20 BPT, not BAL) and **SNX** (collateral C-ratio system, not a simple lock). xSUSHI and
stkAAVE are reward-staking rather than pure vote-escrow but are a genuine locked/committed-supply
signal and are kept in Channel 1 flagged via `mechanism`.
**Rationale:** restricts the on-chain reconstruction to cases where the escrow-balance =
locked-supply identity holds cleanly, maximizing correctness over coverage; gives the
vote-escrow tokens BOTH a Channel-1 (locked) and a Channel-3 (voting) value, the only way any
asset gets a multi-channel λ in Phase 1.
**Downstream impact:** Channel 1 token coverage is intentionally small (6) this pass; widening
it requires per-protocol escrow curation (each lock contract verified individually) or a paid
archive tier for direct historical balanceOf. The veBAL/SNX exclusions should be revisited if
those assets matter to a result.

### Entry 27 — λ assembly: monthly z-score, equal-weight, ≥2-asset standardizability rule
**Date:** 2026-06-23
**Spec section affected:** 3 (λ construction), 3.4 (output)
**Asset(s)/period affected:** all observed asset-months with ≥1 standardizable channel
**What the spec wanted:** λ_t = equal-weighted average of the standardized (z-scored within
each monthly cross-section) values of whichever channels are observable; no imputation;
record how many/which channels contributed.
**What was actually available:** the three channel series built this phase — ch1_staking
(ETH + 6 EVM locks), ch2_holding (none — Entry 24), ch3_voting (51 tokens).
**Decision made:** `phase1_assemble_lambda.py` (1) z-scores each channel within each
(month, channel) cross-section, (2) averages the available z-scores per asset-month with
equal weight, (3) records `n_channels` + `channels`. **Standardizability rule:** a channel
enters a given month's λ only if **≥2 observed assets** have a finite value that month AND
the cross-sectional std > 0 — a single-asset channel cannot be z-scored (z would be 0/NaN)
and is dropped for that month, with the fact counted in
`_lambda_channel_diagnostics.csv`. Raw per-channel values are carried alongside `lambda_z`
for audit. λ is computed on `status='observed'` rows only.
**Rationale:** the spec's "standardize within the monthly cross-section" is only defined for
a cross-section of ≥2; making the rule explicit prevents a degenerate single-asset channel
(e.g. ETH alone on Channel 1 before the ve-tokens enter) from contributing a spurious z=0.
Equal-weighting and no-imputation follow the spec verbatim.
**Downstream impact:** result = 1,308 asset-months, 51 assets, 2020-08→2026-05; 253
asset-months are 2-channel (the 6 vote-escrow tokens), the rest 1-channel. λ is currently a
**standardized score (`lambda_z`), not a [0,1] locking fraction** — the SoV/MoE map
λ/(1−λ) in the theory needs a level, not a z-score, so Phase 4 must decide how to convert
(e.g. use the raw staking/locking ratio as the level where Channel 1 exists, and treat the
z-scored multi-channel index as the cross-sectional conviction *ranking* the hypotheses
actually test). Flagged for the Phase 2/4 kickoff.

### Entry 28 — Phase 1 close-out scope and Phase 2 kickoff direction (Cowork review, pre-build)
**Date:** 2026-06-23
**Spec section affected:** 3 (λ channels, finishing touches), 4 (NVT_GL), 7 (phasing)
**Asset(s)/period affected:** n/a (session-scoping decision, not a data change itself)
**What the spec wanted:** a written coverage report at the end of each phase before
scope is adjusted (§7) — Phase 1's own report (§7) left several open items needing a
human call before Phase 2 should start.
**What was actually available:** three open items from `PHASE1_COVERAGE_REPORT.md` §7
needed a decision: (1) whether to finish Phase 1 loose ends before or in parallel with
Phase 2 — NVT_GL doesn't depend on λ density, so it isn't a hard blocker either way;
(2) whether to procure a paid source (Glassnode/CoinMetrics/Artemis) for Channel 2
(coin-age) now; (3) how to handle ETH's post-Shapella cumulative-vs-net staking question
when resuming the staking series.
**Decision made:** (1) one combined Claude Code session does Phase 1 finishing touches
(finish ETH series, confirm N=250, revisit the 16 gray-zone names with real lock data,
reconcile the report's internal asset-month/asset-count inconsistency) followed
immediately by Phase 2 (NVT_GL) in the same session — see
`04_code/CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md`. (2) Channel 2: explore a free workaround
first (check live whether any BTC-chain explorer exposes a usable UTXO-age/"coins last
moved" metric) before considering any paid source; if nothing free and credible turns up,
the gap stays documented and the paid-source question stays open for a later call.
(3) ETH staking: keep the cumulative-deposit method as-is when resuming the series — do
NOT add post-Shapella withdrawal netting this pass, since that needs a new
consensus-layer data source (new scope, not a finishing touch); keep it documented as a
monotone upper-envelope proxy per Entry 23.
**Rationale:** NVT_GL's inputs (MC, PQ, g, r_e) are independent of λ, so gating Phase 2
on λ density would cost time without a real dependency. The Channel 2 paid-source
question is a real cost decision and shouldn't be made by inertia — checking a free
option first costs nothing and may partially close the gap. The ETH netting question
would expand this session's scope into a new data source for a one-line accuracy
improvement on an already-flagged, already-documented caveat — not worth doing before
the series is even fully resumed.
**Downstream impact:** if the free BTC coin-age check in Part A succeeds, it should be
generalized to other major pre-2020 coins before the paid-source question is revisited.
If ETH's post-Shapella overstatement turns out to matter materially to a result later,
the netting question returns as a Phase 3/4 item once a consensus-layer source is
identified.

### Entry 29 — Phase 1 close-out: ETH series finished, numbers reconciled, Channel 2 BTC re-checked, N=250 confirmed, gray-zone revisited
**Date:** 2026-06-24
**Spec section affected:** 3 (λ channels — finishing touches), 2.1 (universe size), 2.3 (classification), 7 (per-phase coverage report)
**Asset(s)/period affected:** ETH staking series; the λ index headline counts; the 16 gray-zone names; BTC (coin-age source audit)
**What the spec wanted:** Phase 1's coverage report (§7) left five open items requiring a human call before Phase 2; Entry 28 scoped them into this combined session. This entry records how each was resolved.
**What was actually available / what was done:**

1. **ETH staking series — FINISHED.** Re-ran `phase1_channel1_eth_staking.py` to completion
   via its monthly checkpoints (`03_data/raw/phase1_onchain/eth_staking_monthly.json`). Full
   series is now **66 month-ends, 2020-12 → 2026-05**, cumulative deposited ETH rising from
   2.17M (ratio 0.019) to 86.16M (ratio 0.714). The cumulative-deposit method was kept
   **as-is** — post-Shapella withdrawal netting was deliberately NOT added (it needs a
   consensus-layer/beacon source = new scope, not a finishing touch; Entry 28). Still
   documented as a **monotone upper-envelope conviction proxy, not a net-stake figure**
   (the >0.45 ratios in 2025–26 are the documented overstatement; `note` column carries it).

2. **Channel 2 (coin-age) — free BTC workaround checked live (2026-06-24), still a gap.**
   Before leaving Entry 24's conclusion in place, probed free Bitcoin explorers specifically:
   - **mempool.space / blockstream.info (Esplora):** no aggregate coin-age / HODL / CDD
     metric — only per-tx/address/UTXO data (reconstructing coin-age from them = the full
     UTXO-set indexing Entry 24 ruled out).
   - **blockchair `/stats`:** free/keyless and carries `cdd_24h` + `hodling_addresses`, but
     only as a **current 24h snapshot**; historical CDD chart data is not on a free/keyless
     endpoint (404 / 401 + bot-protection).
   - **bitcoin-data.com / bgeometrics (`/v1/cdd`, `/v1/ancient-supply`, dormancy, HODL
     waves):** a genuine free, keyless coin-age API — the closest usable thing found — BUT
     (i) free tier serves only a **trailing ~4 years** (2022-06→present; 1,458 daily records),
     so it cannot reach the **pre-2020 depth that is the whole point**; (ii) hard rate limit
     **10 requests/hour** (`RATE_LIMIT_HOUR_EXCEEDED`); (iii) full history is paywalled — i.e.
     the same paid-aggregator category Entry 24 flagged, with only a shallow free slice.
   Nothing free *and* credible *and* panel-usable turned up, so the breadth check on
   LTC/XRP/DOGE was not pursued (depth + rate caps disqualify the approach first; XRP/DOGE
   aren't UTXO-CDD chains anyway). **No paid source procured — decision deferred (Entry 28).**

3. **N=250 — confirmed, no change.** Per the report's own §7 point 5: λ density is
   governance-token-driven, and tightening (or widening) the universe would not close the
   coin-side gap, which is a **source problem (no free coin-age / non-EVM staking data), not
   a universe-size problem**. The N=250 rank screen stays as set in Phase 0 (Entries 7, 15).
   Stated explicitly on record per the directive; no code change.

4. **16 gray-zone names — revisited with real lock data, all stay `other`.** The only
   Channel-1 lock series built (Entry 26) are the 6 curated escrows (CRV/CVX/FXS/SUSHI/AAVE/
   YFI) — **none of the 16 gray-zone names is among them**, so no security-staking lock series
   exists for any of them. Checked each against the actual channel data:
   - **OP, MNT, RPL, SSV** — have a Snapshot **voting** space (so they DO appear in λ as
     `other`, voting-only: SSV 31, RPL 28, MNT 10, OP 7 asset-months) but **no security lock**.
     OP/MNT are L2 gas+governance (security leans on Ethereum); RPL is a node-operator
     *collateral* bond (like SNX's excluded C-ratio system, Entry 26), SSV an operator bond
     for distributed-validator infra — neither is chain-security staking. Governance ≠ a coin
     security lock and ≠ a clean vote-escrow token → stay `other`.
   - **MANTA, IMX** — L2; staking exists but security leans on Ethereum; no lock series, no
     voting → `other`.
   - **ANKR, STRD** — liquid-staking protocol/appchain tokens (Entry 8 keeps the LST sector
     out of the coin/token cut); STRD is non-EVM (Cosmos), unreachable with the EVM key
     (Entry 21); no lock series, no voting → `other`.
   - **EWT** (PoA, weak seigniorage), **GBYTE** (DAG, historically no staking reward),
     **FCT** (entry-credit, no security-staking reward) → `other`.
   - **BLUR, LOOKS, ME** (NFT-marketplace governance/incentive tokens) → `other`.
   - **PNK** (Kleros juror work/fee-share stake — not network security; no lock series) →
     `other`, still "pending review" as in Entry 18. **PTS** (obscure symbol-collision,
     likely the mineable ProtoShares but low-confidence) → `other`.
   **Net: zero reclassifications;** `classification_table.csv` is unchanged, so λ assembly was
   not re-run on account of this item. Evidence is unchanged from Entry 18, exactly as the
   report §7.4 anticipated.

5. **Report internal inconsistency — reconciled.** `PHASE1_COVERAGE_REPORT.md` §5 had
   previously shown **1,326 asset-months / 52 assets** while §8 and Entry 27 showed **1,308 /
   51**. After the ETH resume the *correct, final* figures are **1,374 asset-months / 52
   distinct assets** (2020-08 → 2026-05); the +66 over the 1,308 baseline is exactly ETH's
   now-complete 66-month series (up from 18 partial months). Every section of the report
   (headline, §4.1a, §5 with its n_channels table and by-year table, §6, §7, §8) was updated
   to these numbers. Final n_channels split: 1-channel 1,121 (voting-only 924, staking-only
   197 incl. ETH's 66) + 2-channel 253 (the 6 vote-escrow tokens) = 1,374.

6. **(Optional) CMC `detail.platforms[]` identity-map enrichment — deferred.** Explicitly
   lower-priority and "not required before Part B" per the kickoff prompt; left for a later
   session to widen Channel 1's EVM token coverage beyond the curated 6. Not done this session.

**Decision made:** resolve items 1/3/4/5 as above (finish ETH as upper-envelope; confirm
N=250; keep all 16 gray-zone names `other`; reconcile the report to 1,374/52); keep item 2
(Channel 2) a documented gap with the free-source audit on record and the paid-source question
deferred; defer item 6.
**Rationale:** these are finishing touches, not new scope — each either completes an
already-validated build (ETH), records a confirmation the report itself asked for (N=250),
re-examines labels against now-available evidence without inventing unsupportable ones
(gray-zone), fixes a bookkeeping inconsistency (report), or honestly reports a live source
audit that came up empty (Channel 2) per the spec's "flag, don't guess" principle.
**Downstream impact (what to re-check if this changes):** if a paid coin-age source or a
consensus-layer ETH source is later procured, items 1 (net-stake ETH) and 2 (Channel 2) both
reopen and λ must be re-assembled. If the CMC `platforms[]` enrichment (item 6) is later run,
re-run `phase1_build_identity_map.py` → any new curated escrows → `phase1_assemble_lambda.py`,
and the 1,374/52 headline will move. The gray-zone names should be revisited again only if a
security-staking lock series is actually built for one of them (e.g. RPL collateral, SSV
operator bond) — at which point the coin/token call changes, not before.
