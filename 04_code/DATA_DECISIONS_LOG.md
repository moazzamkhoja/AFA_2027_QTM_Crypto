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

### Entry 30 — PQ definition (NVT_GL): fees rejected on theoretical grounds, not just feasibility; corrected to sector-appropriate transacted value
**Date:** 2026-06-24
**Spec section affected:** 4, 4.1 (NVT_GL — PQ definition)
**Asset(s)/period affected:** n/a (methodological decision; applies to every coin and token going into Phase 2's PQ series)
**What the spec wanted:** §4.1 lists "on-chain transaction (transfer) volume" for coins and
"protocol throughput (DEX volume, total fees, or active-user counts)" for tokens — fees named
as one acceptable option among several, not a preferred one.
**What was actually available:** `PHASE2_PQ_DECISION_STATUS.md` (session 010) recommended
**fees** (DeFiLlama protocol/chain fees) as the working PQ proxy for both coins and tokens, on
feasibility grounds (free, keyless, deep history) — the human had proposed **TVL** as an
alternative for tokens. An initial Cowork-side literature check (Artemis Analytics, Token
Terminal, DeFiLlama definitions of "economic activity") read as support for fees over TVL,
since all three keep TVL as a metric separate from their "economic activity"/fees framing.
**Decision made:** Reject fees as PQ — not on feasibility grounds, on theoretical ones. PQ in
this paper's own M·V = P·Q identity is **nominal GDP**: the dollar value of goods/services
exchanged, a flow. Fees are the **cost** of facilitating that exchange (a discretionary,
governance-set rate — fee-switch votes, fee-tier choices), not the value of what was
exchanged — structurally identical to treating a government's tax revenue as a proxy for
GDP. (Re-read literally, even DeFiLlama's own description — fees "show how much the protocol
is *facilitating* in economic activity" — supports this correction: a toll booth facilitates
billions in freight without its toll revenue measuring that freight's value. The initial
literature check above read "facilitating" as "measuring"; that was an error, not a difference
of opinion.) TVL is also rejected as PQ, on the reasoning already on record (stock, not flow)
but reframed more precisely: TVL is the **capital stock** that enables activity — an AMM's
pooled inventory, a lending pool's loanable funds, a staking protocol's AUM — i.e. the K in a
production function, not the output Y. A high-TVL pool with zero trading produces zero
realized economic activity that period.

The corrected PQ definition is **transacted value**: the dollar value of what actually moved
through the contract — swap/DEX volume for AMMs, loan-origination/borrow flow for lending,
notional volume for derivatives — **sector-appropriate**, using the project's own `sector`
field (Entry 16) to route to the right flow per protocol type, rather than forcing one
universal proxy (this also resolves the "DEX volume doesn't generalize past DEX-type tokens"
objection). This is, not coincidentally, what the *original* NVT ratio (Willy Woo's Bitcoin
metric, this paper's direct namesake) used on the coin side: on-chain transaction *value*,
never fees. TVL and fees are both **retained as secondary diagnostic columns** (capital-stock
control; cost-of-intermediation/take-rate), plus a new **Volume/TVL turnover diagnostic** — a
protocol-level restatement of M·V=PQ with TVL standing in for M.

This correction is not yet fully implementable: whether true on-chain transfer/swap volume
can be built at panel scale on the free Etherscan key (vs. falling back to DeFiLlama's
reported volume series) is an open empirical question, addressed by the pilot in Entry 31 /
`04_code/CLAUDE_CODE_PHASE2_PQ_PILOT_PROMPT.md`.
**Rationale:** PQ is an accounting identity (P times Q), not a modeling choice — substituting
a cost/toll variable for it embeds the protocol's own discretionary pricing policy into the
paper's dependent variable, contaminating it for reasons unrelated to actual usage. The
tax-revenue/GDP disanalogy and the capital-stock/production-function framing of TVL both come
directly from re-deriving PQ from the paper's own theoretical namesake (the quantity theory of
money) rather than from how aggregators happen to label their dashboards. Full discussion in
`06_documentation/ai_conversations/session_011_2026-06-24_pq_theory.md`.
**Downstream impact:** Supersedes the "(A) fees `[RECOMMENDED]`" lines for both Decision 1 and
Decision 2 in `PHASE2_PQ_DECISION_STATUS.md` §3–4. `phase2_pq.py` should NOT be built on fees.
Whether it is built on true Etherscan-derived transfer/swap volume or on DeFiLlama's reported
volume series (with TVL/fees as side columns either way) depends on the pilot's findings
(Entry 31, once logged). If the pilot finds raw-Transfer-log volume infeasible at panel scale,
DeFiLlama's reported DEX/perps volume becomes the working source and the noise-multiplier
estimate from the pilot should be carried into the paper's methodology section as a documented
limitation (spec §6, the classic NVT wash-trading caveat).

### Entry 31 — PQ source decided: DeFiLlama reported volume (raw Etherscan Transfer-log PQ piloted and rejected — wrong quantity, not just cost)
**Date:** 2026-06-24
**Spec section affected:** 4, 4.1, 6 (NVT_GL — PQ source & methodology limitation)
**Asset(s)/period affected:** n/a (methodological; sets the PQ source for every Phase 2 asset).
Pilot evidence: UNI (cmc_id 7083) and AAVE (cmc_id 7278), May 2026 (31-day window).
**What the spec wanted:** §4.1 lists "on-chain transaction (transfer) volume" as the ideal coin/token
throughput measure; Entry 30 corrected PQ to sector-appropriate *transacted value* and left open
whether that is buildable from raw Etherscan logs vs DeFiLlama's reported volume (this Entry).
**What was actually available / what the pilot found** (full report `03_data/PHASE2_PQ_PILOT_REPORT.md`,
code `04_code/phase2_pq_pilot.py` + `phase2_pq_pilot_diag.py`, session 012):
- **Cost is cheap for a recent window, contra a naive read of Entry 24.** Reusing the Channel-1
  `getLogs` bisection with the counterparty filter dropped (ALL transfers): UNI = 133,350 transfers
  in **381 calls** (345.6 s); AAVE = 116,910 in **309 calls** (305.1 s) — ~345 calls/token-month,
  ~11 calls/day, ~0.9 s/call, far under the free 5 req/s & 100k/day caps. Entry 24's "orders of
  magnitude" wall is the full *multi-year* regime, not a recent window.
- **Extrapolation:** 1 token full history ~23.5k calls (~6 h); 1 recent month × 127 DeFi-slug tokens
  ~44k calls (~11 h) — both feasible. **Full history × 127 tokens ~1.75M calls (~17.5 days @ 100k/day);
  × 241 slugged assets ~3.3M (~33 days)** — infeasible as a routine/repeatable build.
- **Decisive: the governance token's own Transfer events are the WRONG quantity.** UNI token-transfer
  volume = **$0.79B** vs DeFiLlama Uniswap DEX swap volume = **$36.75B** (swap **46.6× larger**, daily
  corr only **0.30**). AAVE raw sum was **physically impossible** ($8.2×10¹⁹ vs 15.4M-token supply):
  **6** sentinel-value transfers, one of **10¹⁸ tokens = 6.5×10¹⁰× supply**; cleaned = **$2.75B**,
  still unrelated to Aave lending throughput. Correct on-chain swap volume would require enumerating
  each protocol's pool `Swap` events (= re-implementing DeFiLlama's adapters) — out of scope on a free key.
**Decision made:** **PQ source = DeFiLlama's reported, sector-appropriate protocol volume**
(DEX/swap for AMMs, perps notional for derivatives, borrow/origination for lending), routed by the
`sector` field (Entry 16). **TVL and fees stay as side diagnostic columns** + the Volume/TVL turnover
diagnostic, exactly as Entry 30 specified. Raw Etherscan Transfer logs are demoted to an **occasional
spot-check**, never the primary source. This resolves the Entry 30 open question (and confirms the
"if infeasible at panel scale → DeFiLlama" branch of Entry 30's downstream-impact note), and finalizes
both Decision 1 and Decision 2 of `PHASE2_PQ_DECISION_STATUS.md` on the DeFiLlama-volume basis.
**Rationale:** Two independent reasons, validity first. (1) **Validity:** a governance token's Transfer
events are not the protocol's transacted value — empirically 47× off and barely correlated for UNI,
and corrupted by non-economic sentinel transfers for AAVE (spec §6 wash/internal-churn caveat in
extreme form). (2) **Cost:** full-panel multi-year raw extraction is weeks of continuous runtime on
the free key. DeFiLlama already computes sector-correct volume from the right per-protocol pool events.
Option (A) [raw at panel scale] rejected on both grounds; pure Option (C) [flagship raw as a *source*]
rejected because it still measures the wrong object — flagship raw kept only as a spot-check.
**Downstream impact:** `phase2_pq.py` to be built on DeFiLlama reported volume (sector-routed), with
TVL/fees side columns — **after human review of the pilot**, not before. Carry into the paper's
methodology/limitations (spec §6): reported aggregator volume is itself subject to the NVT wash-trading
caveat; note that an independent raw-log reconstruction was piloted and found to measure a different
quantity, so the aggregator series is adopted deliberately. Coin-side PQ (ETH/BTC *native* transfers)
was NOT in this pilot and still faces the archive-state wall (Entries 21/24); DeFiLlama chain-level
data remains the coin fallback. Full discussion: `06_documentation/ai_conversations/session_012_2026-06-24_pq_pilot.md`.

### Entry 32 — PQ source waterfall finalized: token fee→volume backout rule + coin source ladder (Cowork decision, supersedes Entry 31's coin-fallback line and §4 of `PHASE2_PQ_DECISION_STATUS.md`)
**Date:** 2026-06-24
**Spec section affected:** 4, 4.1, 6 (NVT_GL — PQ source, both Decision 1 refinement and Decision 2 resolution)
**Asset(s)/period affected:** n/a (methodological; sets the PQ source-selection rule for every Phase 2 asset, tokens and coins).
**Context.** Entry 31 settled tokens on DeFiLlama reported volume but left two things unresolved: (a) what
to do when a protocol has *no* DeFiLlama volume series, and (b) Decision 2 (coins), which Entry 31's
closing line punted to "DeFiLlama chain-level data" — almost certainly meaning chain fees, which carries
the identical toll-vs-value flaw Entry 30 already rejected for token fees. The human pushed back on the
"archive access" framing for native-coin transfers (correct: that wall applies to historical *state*
queries — coin-age/HODL-wave, Entry 24 — not to summing the `value` field already in ordinary
block/transaction data, which any full node retains forever and Etherscan's free API already serves), and
asked specifically whether DeFiLlama has a coin-side "activity" metric before reaching for Artemis or raw
Etherscan. Both points are resolved below with live, keyless verification (Cowork web-fetch, not the
Cowork sandbox's bash egress, which remains blocked).
**What was checked and found:**
- **DeFiLlama chain-level volume exists but is chain-structure-dependent.** `/overview/dexs/{chain}`
  (verified live) returns a real, aggregator-cleaned chain-level DEX-volume series. For Ethereum this is
  substantial (consistent with its DeFi-heavy structure). For **Bitcoin**, fetched live just now: total24h
  = **$419,825**, total30d = **$18.9M**, totalAllTime (since DeFiLlama started tracking) = **$2.17B** —
  driven entirely by three niche bolted-on protocols (Bisq P2P exchange, Garden cross-chain bridge, LN
  Exchange Spot), not Bitcoin's base-layer settlement, which is orders of magnitude larger. **Conclusion:
  DeFiLlama chain-DEX-volume is valid only for chains where DeFi/DEX activity is a material share of real
  economic activity (Ethereum, Solana, Avalanche-style smart-contract platforms). For payment/P2P-dominant
  coins (BTC, LTC, DOGE, etc.) it is degenerate and would silently understate true activity by orders of
  magnitude if used uniformly across the panel.** This is the same lesson as Entry 31 (aggregators clean
  data, but you must check the aggregator is measuring the *right object* for that specific asset) applied
  to a new case.
- **Artemis Settlement Volume** (Entry 30/prior Cowork session): theoretically the right object for
  payment-dominant coins (P2P + DEX + NFT, explicitly includes native/token/stablecoin transfers, explicitly
  *not* a toll measure) but **access is unverified** — Phase 0 Entry 2 found Artemis's API dead
  (`api.artemisxyz.com` → HTTP 410); a fresh check found a relaunched API product and free "Lite" tier, but
  whether Settlement Volume is exposed standalone on the free tier, at what historical depth, and for how
  much of the ~250-asset coin panel, has **not** been live-tested from this sandbox.
- **blockchain.com Charts API**: confirmed (web search) to expose a free, keyless, long-history daily
  "Estimated Transaction Value (USD)" series for BTC specifically, which already excludes change outputs
  (pre-cleaned of the classic UTXO change-inflation problem). Real candidate, BTC-only — does not generalize
  to the rest of the coin panel without a per-chain equivalent.
**Decision made — two rules:**
1. **Token PQ fallback (refines Entry 31).** Primary source stays DeFiLlama sector-routed reported volume.
   Where a protocol has **no** DeFiLlama volume series, do **not** fall back to its fee as PQ directly
   (that reintroduces the Entry 30 toll-vs-value error). Instead, **only if** the protocol's fee is a
   confidently known, *stable, single-rate* function of notional volume over the window in question (e.g.
   a documented flat swap fee, so `notional = fee / rate`), back out volume algebraically from the fee and
   use that as PQ. **Do not** apply this when the rate is multi-tier (e.g. Uniswap V3's several fee-tier
   pools, where the blended rate is itself unknown without volume — circular), governance-adjustable/variable
   across the window, or not a simple function of notional (e.g. lending reserve factors, which are a % of
   *interest*, not of loan volume). If neither DeFiLlama volume nor a confident fee-rate backout exists for
   a protocol-month, **flag PQ as missing (NaN)** rather than substitute fees directly — per spec §0
   ("flag, don't guess").
2. **Coin PQ source ladder (resolves Decision 2), evaluated per coin/chain, not globally:**
   - **Rung 1 — DeFiLlama chain-level DEX volume** (`/overview/dexs/{chain}`), for chains where this is
     non-degenerate (material DeFi activity — confirm per-chain before using, not just for majors).
   - **Rung 2 — Artemis Settlement Volume**, for chains where Rung 1 is degenerate/unavailable (payment-
     dominant coins), *if and only if* live-verified as free-tier-accessible with adequate panel coverage
     and historical depth (not yet confirmed — next session's job).
   - **Rung 3 — coin-specific native fallback**: blockchain.com's Estimated Transaction Value series for
     BTC; for other chains without an equivalent ready-made series, raw native-`value` block iteration
     (now known to be a call-volume problem, not an access wall — feasible for a recent window, infeasible
     for full multi-year history per-chain, same shape as Entry 31's token finding).
   - **Rung 4 (last resort, explicitly flagged, not a default)** — DeFiLlama chain fees, used only if no
     asset on rungs 1–3 is available for that coin, and documented in the paper's limitations as a
     theoretically weaker, toll-based substitute, exactly parallel to how token fees were rejected.
   Aggregators (DeFiLlama, then Artemis) are preferred over raw reconstruction wherever they validly cover
   the asset, because they already absorb data-cleaning that raw logs require ad hoc (Entry 31's AAVE
   sentinel-value problem) — but which rung applies must be checked per asset, not assumed uniformly, per
   the Bitcoin DEX-volume finding above.
**Rationale:** Same first-principles standard as Entry 30 (transacted value, not toll) applied consistently
to both the token fallback case and the coin case; the Bitcoin live check is the empirical guardrail that
stops "DeFiLlama has *a* volume number for this chain" from being treated as automatically valid — exactly
the AAVE-sentinel-value lesson, generalized.
**Downstream impact:** Next Claude Code session should (a) live-verify Artemis Settlement Volume's free-tier
access, coverage, and historical depth; (b) live-check `/overview/dexs/{chain}` per coin in the panel to
sort each into Rung 1 vs. needs-Rung-2/3; (c) build `phase2_pq.py` (tokens, with the fee-backout rule coded
explicitly and rate-confidence judgment calls documented per protocol) and `phase2_nvt_gl.py` (coins, per the
ladder above), logging every per-asset rung decision and every fee-backout rate used as it goes. Supersedes
the "DeFiLlama chain-level data remains the coin fallback" line in Entry 31 and finalizes
`PHASE2_PQ_DECISION_STATUS.md` §4. Full discussion: this Cowork session (no transcript file written; captured
here and in chat).

### Entry 33 — Phase 2 NVT_GL built: token PQ (16 assets) + covered-coin PQ (50 assets) + full NVT_GL machinery; perps/derivatives volume found paywalled
**Date:** 2026-06-24
**Spec section affected:** 4, 4.1, 4.2 (NVT_GL build); 6 (landmines)
**Asset(s)/period affected:** all assets entering Phase 2; PQ series + g/r_e/PQ\*/NVT_GL per asset-month
**What the spec wanted:** NVT_GL = MC/PQ\* per asset-month, with PQ = transacted value (Entries 30–32),
g = trailing-3y CAGR of PQ, r_e = CAPM-style discount rate, g_inf/n robustness constants; emit all
intermediates so assumptions vary without rebuild (spec §4.2).
**What was actually built (session 013):**
- **Token PQ (Part A, `phase2_pq_tokens.py`)** — DeFiLlama sector-routed reported volume. Routed each of
  the 127 slugged tokens by its DeFiLlama category to the matching free volume dimension: `/summary/dexs`
  (11 tokens), `/summary/aggregators` (4, flagged as routed/double-counting), `/summary/options` (1).
  **16 tokens get a monthly volume PQ.** The other 111 are flagged NaN with explicit reasons — 93 have no
  transacted-value object (Yield/Farm/Lending/Gaming/Services/Bridge/Chain tokens have no swap/notional
  flow), 8 are slug-absent/ambiguous (SunSwap version-split, VELO/SXP symbol collisions — left NaN not
  guessed), and **10 are perps whose DeFiLlama volume dimension is now PAID-GATED (HTTP 402 at both
  `/overview/derivatives` and `/summary/derivatives/{slug}`)** — a new landmine; open-interest is free but
  is a stock not a flow, so not valid PQ. **Fee→volume backout (Entry 32) fired for 0 protocols** — no token
  protocol-month met the strict documented-single-stable-rate test (all candidates are multi-tier DEX fees,
  variable perps fees, or lending reserve factors, explicitly excluded), so none were filled with raw fee.
- **Coin PQ (Part B covered rungs, `phase2_pq_coins.py`)** — per the B1 rung table (Entry 34). **49 coins
  via Rung 1** (DeFiLlama `/overview/dexs/{chain}` daily→monthly, materiality ≥1% monthly DEX/mcap) +
  **BTC via Rung 3** (blockchain.com Estimated Transaction Value, change-excluded, 2010→present). **Rung 4
  (chain fees) auto-applied to ZERO coins** — it is a flagged toll proxy requiring explicit approval. The 81
  GAP-R2 coins carry PQ=NaN, deferred to Phase 2b (Entry 34).
- **NVT_GL (`phase2_nvt_gl.py`)** — PQ0 = trailing-12m sum of monthly PQ (annual throughput); g = trailing
  3y CAGR of PQ0 (≥1y fallback flagged in `g_window_years`; capped [−50%,+200%]); beta = trailing-36m vs
  **BTC** (the spec's simple market proxy — the cap-weighted index is numerically unusable, penny-token
  returns → inf); r_e = rf + beta·MRP with **rf=4%, MRP=30% as documented robustness parameters** (NOT the
  realized ~114%/yr BTC premium, which is not a forward required return), floored at 0.05; g_inf=3%, n=10.
  PQ\* = spec §4.1 levelized annuity; NVT_GL = MC/PQ\*. **Result: 1,821 asset-months, 59 assets (46 coins,
  13 tokens), 2016-08→2026-05.** No pathologies (0 inf, 0 non-positive PQ\*).
- **Diagnostics (`phase2_pq_diagnostics.py`)** — TVL (capital-stock control) + Volume/TVL turnover per
  Entry 30/31: 2,534 asset-months, median turnover 1.15×.
**Decision made:** build NVT_GL on exactly the assets with a defensible transacted-value PQ; flag every gap
(NaN with reason) rather than substitute a toll/proxy; keep MRP/rf/g_inf/n as emitted robustness parameters.
**Rationale:** faithful to Entries 30–32 (transacted value, not toll) and spec §0 (flag, don't guess) and
§4.2 (emit intermediates). Using BTC as the market index is the spec's named simple alternative and is forced
by the cap-weighted index's numerical fragility.
**Downstream impact (re-check if this changes):** **g-cap binds on 43.4% of NVT_GL rows**, and PQ\* scales
with (1+g)^n so NVT_GL spans many orders of magnitude driven by g — **NVT_GL is reliable as a cross-sectional
RANK/conditioning variable (how H2/H3 use it), not a cardinal level**; g_cap and n are the first sensitivity
knobs (spec §5). If perps volume access is later obtained, the 10 derivatives tokens reopen. If MRP/rf are
re-chosen, re-derive r_e from the emitted beta — no rebuild. Outputs: `03_data/phase2/{pq_tokens,pq_coins,
nvt_gl_panel,pq_diagnostics}.csv`. Full numbers: `03_data/PHASE2_COVERAGE_REPORT.md`. Session:
`06_documentation/ai_conversations/session_013_2026-06-24_phase2_build.md`.

### Entry 34 — Coin PQ Step-B1 verification: Artemis paid-only; 81 material coins deferred to Phase 2b (human decision)
**Date:** 2026-06-24
**Spec section affected:** 4.1 (coin PQ source, Decision 2 / Entry 32 ladder); 7 (phasing — new Phase 2b)
**Asset(s)/period affected:** the coin side of the panel; 81 material coins (peak mcap ≥ $1B) flagged GAP-R2
**What the spec wanted:** Entry 32 set a coin source ladder (R1 DeFiLlama chain DEX → R2 Artemis Settlement
Volume → R3 native → R4 chain fees) and required a live B1 verification of Artemis access + per-coin DeFiLlama
coverage before building, with an explicit instruction to STOP and report rather than guess if Artemis is
paid-only or coverage is ambiguous for any material coin.
**What was actually found (B1, live, session 013 — full report `03_data/PHASE2_COIN_PQ_VERIFICATION_B1.md`):**
- **Artemis REST API is PAID-ONLY.** Old hosts dead (`api.artemisxyz.com`→410, others DNS-fail, confirming
  Entry 2). Current product: `settlement_volume` *exists* as a standalone metric (right object), but the free
  "Lite" tier exposes only Terminal + a Google-Sheets plugin (100k ART calls/mo, not a scriptable REST path);
  Pro ($300/mo) does not list REST API access; no free self-serve REST tier. **Rung 2 is closed for a
  reproducible pipeline.**
- **DeFiLlama chain DEX coverage** (`/overview/dexs/{chain}`, 134 chains live): with an explicit materiality
  threshold (**30-day chain DEX volume ÷ market cap ≥ 0.01**; BTC 9×10⁻⁶ fails, ETH 0.143/SOL 1.04 pass),
  **only 49 coins (40 material) are Rung-1 valid.**
- **blockchain.com** Estimated Transaction Value (USD) for **BTC confirmed** (Rung 3, change-excluded,
  2010→present) — BTC-specific, does not generalize.
- **Net: 81 material coins** (XRP, DOGE, LTC, BCH, XMR, ZEC, DASH, ATOM, DOT, MATIC, …) are left with **no
  free transacted-value PQ source** — their only ladder option was the now-paywalled Artemis. The
  DeFiLlama/BTC combination does **not** cover the coin panel adequately.
**Decision made:** This is the B1 STOP-and-report condition. Reported to the human; the human's call (logged):
**proceed now with the covered panel (16 tokens + 49 R1 coins + BTC) and stand up a Phase 2b to source the 81
coins later** — rather than auto-dropping them to Rung 4 (toll proxy) or silently NaN-ing them. Phase 2b
kickoff written: `06_documentation/CLAUDE_CODE_PHASE2B_KICKOFF_PROMPT.md` (XRPL APIs for XRP; bitinfocharts/
blockchair "sent-in-USD" for the UTXO payment coins; Artemis-paid option if access procured; **XMR noted a
permanent gap — RingCT hides amounts**). Until Phase 2b, those 81 coins carry PQ=NaN in `pq_coins.csv` /
`nvt_gl_panel.csv`, flagged `GAP:artemis_paid_only`.
**Rationale:** Entry 32's ladder is decided, but the B1 instruction explicitly designates the Artemis-paid /
material-coverage-gap case as a human-review pause point — guessing a toll proxy for XRP/DOGE/LTC/etc. is
exactly what the rule forbids. Proceeding with the covered panel keeps the session productive while the gap is
honestly documented and scheduled, not papered over (spec §0).
**Downstream impact:** Phase 2b must fill these before any coins-only or full-panel H2/H3 result leans on
coin NVT_GL coverage; the rung table `03_data/phase2_coin_rung_table.csv` (rung=='GAP-R2') is the worklist.
If Artemis API access is procured, Rung 2 reopens for most of them at once (Settlement Volume only — never the
Total Economic Activity composite, which bundles toll measures).

### Entry 35 — Phase 2b: 8 GAP-R2 coins sourced via bitinfocharts native settlement value; XRP/XMR permanent gaps; 71 others NaN (all live-verified, no Artemis key)
**Date:** 2026-06-25
**Spec section affected:** 4.1 (coin PQ source, Entry 32 ladder Rung 3-native); 6 (landmines); 7 (phasing — Phase 2b)
**Asset(s)/period affected:** the 81 GAP-R2 coins (peak mcap ≥ $1B) deferred from Phase 2 (Entry 34)
**What the spec wanted:** Phase 2b (`06_documentation/CLAUDE_CODE_PHASE2B_KICKOFF_PROMPT.md`) — source
*native settlement value* (on-chain payment/transfer value in USD, the coin-side analogue of Bitcoin's NVT
denominator; NOT fees/DEX-volume/TVL) for the 81 coins, verifying free access live, flagging not guessing,
and never doing raw multi-year block iteration. Artemis only if a key was procured.
**What was actually available (live, keyless, 2026-06-25 — `04_code/.api_keys.json` has only `etherscan`,
so no Artemis; Rung 2 stayed closed):**
- **bitinfocharts "Sent in USD"** (`/comparison/sentinusd-{ticker}.html`) — free, keyless, daily, long
  history; summed daily→monthly (matching the BTC handling in `phase2_pq_coins.py`). **Critical landmine:
  unrecognised slugs silently serve BITCOIN's series** (verified: bch/bsv/btg/nano/peercoin/komodo/… via the
  `{coin-name}-sentinusd` alias all returned an identical BTC series), so the build is **ticker-keyed** and
  **BTC-default-guarded** (asserts each covered series' latest value ≠ BTC's). bitinfocharts exposes only 13
  tickers [btc eth xrp zec doge ltc xmr bch dash etc bsv vtc btg]; the GAP-R2 overlap is **DOGE, LTC, BCH,
  DASH, ETC, BTG** (current through 2026-06) plus **BSV** (stale, ends 2021-08) and **ZEC** (stale, ends
  2022-05). XRP's bitinfocharts page exists but is **empty** (not a UTXO chain; no "sent in USD" computed).
- **XRP (cmc_id 52, highest-value GAP coin):** no free keyless historical XRPL payment-volume series.
  Checked live — data.ripple.com (Ripple Data API v2, which served `payment_volume`) → **403/dead**;
  api.xrpscan.com → account endpoints work but **no** historical-volume endpoint (docs+live); xrplmeta
  (s1.xrplmeta.org) → token-metadata/clio node, not volume; api.xrpldata.com → XRPL **NFT** API; bithomp →
  403 (key); data.xrplf.org → nginx default / 404. Raw full-history ledger iteration (~21.6k ledgers/day) is
  the forbidden call-volume wall.
- **XMR (cmc_id 328):** RingCT cryptographically hides amounts → native transacted value unobservable on any
  source. Permanent gap, per the kickoff's explicit STOP.
- **Next tier (ATOM/Cosmos, KAS/Kaspa, DOT-KSM/Polkadot, FIL, THETA, XTZ, VET, IOTA, NEO, …):** probed live —
  Cosmos public LCD (`cosmos-rest.publicnode.com`) and `api.kaspa.org` return only **current state**
  (supply/network); Filfox returns **base-fee** (a toll, not value); Mintscan (`apis.mintscan.io`) and Subscan
  require **API keys**. No free, keyless, ready-made historical USD transacted-value series.
- **blockchair** has **no** free historical charts API (`/charts/...` → 404); only current `/stats`.
**Decision made:** Fill PQ for the **8 bitinfocharts-covered coins** (`pq_source=bitinfocharts_sentinusd`,
`rung=R3-bitinfo`), with explicit per-coin honesty flags in the `note` column: UTXO "Sent in USD" is total
*output* value and therefore **change-INFLATED** (opposite of BTC's change-excluded series); ETC is
account-model (no change); ZEC is **transparent-pool only** (shielded amounts hidden) and stale; BSV stale.
Leave the other **73 coins PQ=NaN** with refined, source-specific reasons (XRP `no_free_xrpl_volume_series`,
XMR `xmr_ringct_unobservable`, the rest `no_free_native_series_p2b`). No toll/fee proxy (Rung 4) applied to
any coin; nothing guessed. New script `04_code/phase2b_pq_coins.py` (idempotent post-process on
`pq_coins.csv`; raw HTML cached gitignored under `03_data/raw/bitinfocharts/`); must run AFTER
`phase2_pq_coins.py` and BEFORE `phase2_nvt_gl.py`.
**Result (re-ran `phase2_nvt_gl.py` + `phase2_pq_diagnostics.py`):** PQ asset-months **2,557 → 3,358** (73
assets); **NVT_GL 1,821 → 2,526 asset-months, 59 → 67 assets (54 coins, 13 tokens)**, 2016-08 → 2026-05; no
pathologies. g-cap still binds ~43% — the "rank, not cardinal level" caveat (§2a) is reinforced by the
change-inflated UTXO PQ (e.g. LTC median NVT_GL ≈ 5×10⁻⁴).
**Rationale:** native on-chain transfer/output value is exactly the coin-side object the original NVT used
(Entry 30) and is what bitinfocharts "Sent in USD" measures; aggregators are preferred over raw reconstruction
where they validly cover the asset (Entry 32). Every covered series is flagged for its known bias rather than
silently blended; every uncovered coin is flagged with a live-verified reason rather than dropped to a toll
proxy — per spec §0 ("flag, don't guess") and the kickoff's explicit rules.
**Downstream impact (re-check if this changes):** if Artemis Settlement Volume or a Subscan/Mintscan/Glassnode
key is procured, Rung 2 reopens for most of the 71 `no_free_native_series_p2b` coins at once (Settlement
Volume only, never the Total-Economic-Activity composite) and the panel widens further. The 8 change-inflated
UTXO series should be sensitivity-checked (or, for BTC-comparability, a change-excluded equivalent sought) if a
coins-only NVT_GL *level* — not rank — ever drives a result. Re-running `phase2_pq_coins.py` regenerates the
old GAP markers, so `phase2b_pq_coins.py` must be re-run after it. Outputs unchanged in schema:
`03_data/phase2/{pq_coins,nvt_gl_panel,pq_diagnostics}.csv`. Session: `06_documentation/ai_conversations/
session_014_2026-06-25_phase2b_coins.md`. **Do not start Phase 3 without review.**

### Entry 36 — Dune feasibility pilot: free tier cleanly solves all 3 token-side PQ gap categories (Lending/Liquid-Staking/Perps); recommend (A) gated on a free-tier panel-scale dry-run
**Date:** 2026-06-25
**Spec section affected:** 4, 4.1 (token PQ source — the Entry-32 "flag PQ missing" branch for categories with no DeFiLlama series); 6 (landmines)
**Asset(s)/period affected:** the token-side PQ gap — Lending, Liquid Staking, and the perps/derivatives 402-paywall (10 tokens incl. GNS). Pilot evidence: AAVE/LDO/GNS, trailing 30d (2026-05-27 → 2026-06-25).
**What the spec wanted:** test, *before* requesting university funds for a paid Dune subscription, whether Dune's decoded/Spellbook tables can supply the protocol-level transacted value DeFiLlama has no (or paywalled) volume dimension for — one token per NaN category. Diagnostic pilot only, **not** a Phase 2c build.
**What was actually available / what the pilot found** (full report `03_data/DUNE_PILOT_REPORT.md`, code `04_code/dune_pilot_{test,explore,aggregate,verify}.py`, raw JSON `03_data/raw/dune_pilot/`, session 015):
- The pre-written `dune_pilot_test.py` auto-picker stopped all 3 at `needs_manual_column_mapping` — it grabbed the **wrong** tables (Aave **Polygon** transfers, Lido submit w/o USD, a Gains per-trade table w/o `amount_usd`). The value was in the **manual mapping** to normalized abstractions, exactly as the prompt anticipated.
- **AAVE (Lending) → `lending.borrow`** (cross-protocol spell, pre-priced `amount_usd`): 30d Ethereum-v3 borrow origination = **$4.286 B** (25,452 borrows; repays/liquidations are negative `amount_usd`, excluded). Cross-check: ÷ DeFiLlama Aave-v3 Ethereum borrowed-outstanding $7.215 B = **0.59×/30d** (≈1.7-mo avg loan life) — order-of-magnitude sane (cf. Entry 31's 46.6× / 10¹⁰ misses). **PASS.**
- **LDO (Liquid Staking) → `lido_ethereum.steth_evt_submitted` + `…withdrawalqueueerc721_evt_withdrawalclaimed` × `prices.day`:** 30d stake+unstake flow = **$1.583 B** (stake $938 M + unstake $645 M). **The one trap, caught:** `prices.day` filtered by `symbol='WETH'` matched **3 contracts** ($0.0000008–$2,112, avg $795) → nonsensical **$767/ETH**; switching to the **canonical WETH contract** `0xc02a…756cc2` gave **$1,768/ETH** vwap, consistent with DeFiLlama spot **$1,560**. **PASS** — and the Entry-31 lesson recurred in a new form (clean-looking number, wrong; only the cross-check exposed it). Headline caveat for any hand-rolled price join at panel scale: filter by contract address, never ticker.
- **GNS (Derivatives) → `dune.gains.result_g_trade_stats_defi_llama`** (Gains' own table that *feeds* DeFiLlama, = the `dune.com/gains/gtrade_stats` dashboard data): 30d notional = **$1.178 B** ($39.3 M/day, 84,929 trades, all chains). DeFiLlama per-protocol derivatives endpoint **re-confirmed 402** — the exact paywall that created this gap; Dune retrieves the same series **for free**. Cross-check is internal+historical (component sum = `daily_volume` to 0.000%; $/day in gTrade's known $20–60 M band; per-trade $13,871 sane). A raw-table reconstruction (`result_gtrade_all_orders_daily_view.position_size_dai`) gave ~$44 M (~27× low) — **logged inconclusive (ambiguous column = margin/DAI-only, not notional)**, per "don't guess at ambiguous columns," **not** treated as a contradiction. **PASS (plausibility).**
- **Cost:** no Dune credit-balance endpoint/header exists. Precise counts: **14 catalog `/datasets/search` (not query-metered) + 9 `/sql/execute` (all `small`; free tier rejects `medium`; ~130 datapoints total); only 3 executes strictly necessary.** ⇒ on the order of **<100 of 2,500 free monthly credits (<4%); pool resets monthly.** Cost is a non-issue at this scale.
**Decision made:** **Dune cleanly solves all three token-side PQ gap categories on the free tier** → recommendation **(A)** (free tier sufficient to prototype all three at panel scale), with **one gate before any funding request.** Spell tables are cross-protocol, so the whole token panel's history is a handful of `GROUP BY project, block_month` queries (not one-per-token), keeping even multi-year backfill credit-cheap. **The single risk that could downgrade to (B):** free tier only exposes the **`small` query engine** (the LDO join already took 66 s); a multi-year full-panel scan with joins could hit per-query time/row limits and require the paid `medium`/`large` engine — for the *engine*, not for credits. Two coverage caveats: confirm each panel protocol is in Dune's spellbook (majors are; long-tail may not), and apply canonical-contract discipline to every price join.
**Rationale:** same Entry-30/31 standard — measure the right object (protocol transacted value, not a side token's transfers or a fee/toll) and verify every number against an independent reference before trusting it. The normalized spell tables already absorb the data-cleaning that raw Etherscan logs required ad hoc (Entry 31's AAVE sentinel problem), and DeFiLlama's own upstream Gains table fills the 402 gap directly.
**Downstream impact (do this before requesting funds / before Phase 2c):** run a **free-tier panel-scale dry-run** — one grouped `lending.borrow` / `perpetual.trades` (or `dex.trades`) / Lido-events query over full history across the real token list — and observe whether the `small` engine completes. Completes → free tier fully sufficient, **no subscription needed (A)**; times out on multi-year scans → modest paid plan justified **only** for the engine (B). This is the actual feasibility data point for the funding decision Moazzam is weighing. **Do not buy a Dune subscription, and do not start a Phase 2c build, before this dry-run and human review.** No panel outputs were written this session (`pq_tokens.csv` and all Phase 2/2b CSVs unchanged — diagnostic pilot only). Session: `06_documentation/ai_conversations/session_015_2026-06-25_dune_pilot.md`.

### Entry 37 — Dune free-tier full-panel dry-run: `small` engine survives full-history scans (engine risk DISPROVEN → (A)); 13 of 17 NaN tokens are not in Dune's spellbook (coverage gap, not engine gap → (C), unfixable by a paid plan)
**Date:** 2026-06-25
**Spec section affected:** 4, 4.1 (token PQ source — the Dune branch for DeFiLlama-absent/paywalled categories); 6 (landmines)
**Asset(s)/period affected:** the 17 token-side NaN tokens in the 3 pilot categories — Lending {AAVE, ANC, BZRX, OM, STRK, WXT}, Liquid Staking {LDO}, Derivatives {AVNT, DDX, GNS, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR}. Full history, panel 2015-08→2026-05 (130 months).
**What the spec/Entry-36 wanted:** Entry 36 made recommendation (A) conditional on a **free-tier panel-scale dry-run** answering two open caveats for the *real* token list (not the 3-token sample): (a) is each NaN token's protocol actually in Dune's normalized spellbook (majors confirmed; long-tail unknown), and (b) does a **full-history, full-panel** grouped query complete on the free **`small`** engine (the LDO join took 66 s on just 30 days — the one risk that could downgrade to (B), a paid engine). Diagnostic only — **not** a Phase 2c build.
**What was actually found** (full report `03_data/DUNE_DRYRUN_REPORT.md`, code `04_code/dune_dryrun_{coverage,coverage2,fullpanel}.py`, raw `03_data/raw/dune_dryrun/`, session 016):
- **Engine risk (b) — DISPROVEN; (A) holds.** All three full-history, monthly-grouped queries completed on `small` with no timeout / row cap / truncation / error: **Lending** (`lending.borrow` GROUP BY project, month, aave+strike) **2.0 s** wall / 0.4 s engine, 138 rows; **Derivatives** (`dune.gains.result_g_trade_stats_defi_llama` GROUP BY month) **1.9 s** / 0.2 s, 54 rows, Σ notional $122.8 B; **Liquid Staking** (Lido submit + withdrawalclaimed × canonical-WETH `prices.day`, GROUP BY month) — the join-heavy worst case — **48.8 s** wall / 43.1 s engine, 102 rows, Σ stake $61.1 B / unstake $44.0 B. The 66 s pilot figure (30 d) was variance, not a scan that grows dangerously with history (full history was *faster*). **`small` is sufficient for the full panel; no paid engine needed.**
- **Coverage (a) — most of the 17 are not on Dune; the gap is in the spellbook, not the engine.** Decisive test = does the protocol appear as a `project` in the normalized cross-protocol spells (`lending.borrow`, 25 projects; `perpetual.trades`, 28 projects), the layer that made AAVE/LDO/GNS usable — *not* mere catalog text-search, which returns only raw decoded ERC-20/vault contracts. **Only 4 of 17 covered:** AAVE (`project='aave'`), **STRK** (`project='strike'`, Strike Finance — a NET-NEW find beyond the pilot: $224.3 M lifetime borrow origination once filtered to `transaction_type='borrow'`; its unfiltered net was −$0.02 B because repays/liquidations carry negative `amount_usd`), LDO (Lido events + canonical-WETH join), GNS (Gains DeFiLlama-feed table + `gains_network` in `perpetual.trades`). **The other 13** (ANC, BZRX, OM, WXT; AVNT, DDX, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR) appear only as raw token/vault contracts with no pre-priced notional/volume (e.g. ANC = `anchor_ethereum.anchorvault_*` ETH bridge only; MIR's only EVM hits are the unrelated `mirror.xyz` NFT product — MIR = Mirror Protocol on **Terra**; MYX has decoded router/positionmanager calls but is absent from `perpetual.trades`).
- **Cost:** 6 `small` executes (~600 datapoints) + catalog searches (not query-metered) ≈ <1% of the 2,500 free monthly credits. Hit a transient **429 rate-limit** on `/datasets/search` after ~14 quick calls → added throttle+retry (landmine: the catalog search endpoint rate-limits at a few calls/sec).
**Decision made:** **No paid Dune plan is needed.** Recommendation per category: **(A)** Lending, Liquid Staking, Derivatives — for the **4 covered** NaN tokens (AAVE, STRK, LDO, GNS), the free `small` engine handles the full panel (worst case 48.8 s). **(C)** for the **13 uncovered** tokens — they are absent from Dune's normalized spells entirely, so **a paid plan would not recover them** (paid tiers buy a bigger engine, not more spellbook coverage); they stay **flagged-NaN** with their existing documented reasons. **No (B) outcome** — the engine never struggled. This converts Entry 36's *conditional* (A) into an *unconditional* (A) for the covered set and resolves Moazzam's funding question: don't buy.
**Rationale:** same Entry-30/31/36 standard — measure the right object (normalized protocol transacted value, not a side token's transfers, not a raw-event hand-reconstruction = the rejected AAVE-sentinel path) and verify before trusting (the STRK negative-net check; the canonical-WETH contract join, never `symbol='WETH'`). The key reframing: the residual limitation is a **coverage** (spellbook) gap, which money cannot close, not an **engine** gap, which money could — so the funding lever is pointed at the wrong constraint.
**Downstream impact:** After human review, a Phase-2c build may fill **AAVE, STRK, LDO, GNS** from Dune on the **free tier** (filter lending to `transaction_type='borrow'`; drive the Lido query off the submit table or filter to ≥ first Lido month; canonical-contract discipline on every price join), and leave the other 13 documented NaN — net +4 token PQ series (incl. the one bonus, STRK) at zero subscription cost. **Do not purchase any Dune plan; do not start the Phase 2c build before this report is reviewed.** No panel outputs were written this session (`pq_tokens.csv` and all Phase 2/2b CSVs unchanged — diagnostic only). Session: `06_documentation/ai_conversations/session_016_2026-06-25_dune_dryrun.md`.

### Entry 38 — TVL→PQ stock-to-flow conversion framework (AK-model turnover); scoping the full 111-token NaN universe (not just the 17 Dune-scoped tokens) as a diagnostic-only Phase 2c metadata audit
**Date:** 2026-06-25
**Spec section affected:** 4, 4.1 (token PQ source) — extends, does not reverse, Entry 30 (TVL ≠ PQ) and Entry 32 (the fee→volume inversion rule), generalizing both from the 17 Dune-pilot tokens to the full 111-token NaN universe.
**Asset(s)/period affected:** all 111 NaN tokens in `pq_tokens.csv` (the 17 Dune-scoped tokens resolved/documented per Entry 37, plus the other 94 never previously examined). Live-reverified category breakdown: Yield 16, Derivatives 10, Farm 8, Gaming 7, Dexs 7, Services 7, Bridge 6, Lending 6, Launchpad 6, Chain 6, Yield Aggregator 4, Canonical Bridge 3, Cross Chain Bridge 2, Developer Tools 3, Token Locker 2, plus 17 singleton categories (1 token each).
**What was discussed (Cowork session, not Claude Code):** Moazzam challenged the Dune dry-run's 4-of-17 result as too thin a cross-section for the paper to be useful, and asked whether TVL (a stock) can be converted into a PQ proxy (a flow) via some "rate," drawing an explicit analogy to nominal GDP = capital × an efficiency rate in a no-labor economy, and separately asked what "turnover" means and whether NVT's "T" is itself TVL.
**What was found:**
- Corrected a specific factual claim: NVT's "T" (Woo 2017) is on-chain transacted USD volume — a flow — never TVL; TVL is a separate, later concept (locked capital, a stock). The existing TVL-based ratio in practitioner use is Market-Cap/TVL (a price-to-book analog), structurally unrelated to NVT.
- The user's "capital → economic activity at some rate, no labor" intuition maps directly onto the **AK endogenous-growth model** (Y = A·K): PQ = A_protocol × TVL, where A ("turnover") is the same object as the corporate-finance asset/capital-turnover ratio (flow ÷ stock). This ties directly to the paper's own M·V = P·Q framing (M=TVL is structurally analogous).
- DeFiLlama tracks **Fees and Revenue as separate, directly observed flow series** (distinct from TVL and from the Dune-verified Volume/spell layer) across 7,000+ protocols. Where a fixed, known fee rate exists, Volume ≈ Fees ÷ fee_rate — this is **not a new idea**, it is Entry 32's already-decided rule ("back out volume from fee only when the fee is a confidently known single, stable rate, else flag missing"), now being extended from the 8 bitinfocharts coins to the broader 94-token set.
- Attempted live DeFiLlama verification (myx-finance, avantis, linear-finance, ooki, mantra-dao, nereus-finance, loopring, velo-finance, hakka-finance) from the Cowork sandbox; blocked — `api.llama.fi` returns `403 blocked-by-allowlist` from this sandbox's network proxy. Live verification must happen in a local Claude Code session (normal network access), same as the Dune work.
- The natural calibration cohort for a TVL×turnover rate is the **25 lending + 28 perpetual.trades** Dune `DISTINCT project` lists already pulled in Entry 37 — n=25/28 with real PQ, pairable against DeFiLlama TVL for the same protocols — not just the 4 directly-covered target tokens (n=4 is too thin to calibrate anything from).
**Decision made:** Scope the next session as a **diagnostic-only metadata audit** ("Phase 2c diagnostic"), not a build. Per token (not blanket per-category), check what DeFiLlama data exists (TVL, Fees, Revenue, direct Volume via the dexs/derivatives/bridges verticals, APY via yields) and judge which conversion path is plausible given that protocol's actual economic model: direct volume (no conversion needed) > fee inversion (Entry 32's rule) > TVL×APY (Farm/Yield/Yield-Aggregator, 28 tokens, APY is a directly observed protocol-specific rate) > TVL×calibrated-turnover (Lending/Derivatives/Liquid-Staking, gated on the dispersion check below) > none. **Gaming (7 tokens) is explicitly out of scope and stays NaN** — in-game activity isn't capital-driven and forcing this model there would be its weakest application. Before trusting any TVL×turnover number, compute the actual turnover distribution across the 25+28 comparable cohort and report its dispersion plainly — only recommend it if defensibly tight.
**Rationale:** Same Entry-30/31/32/36/37 standard — measure the right object, verify before trusting, don't force a match where the economic model doesn't support one. This is an extension of the existing framework (calibrated stock→flow conversion via turnover, fee-inversion generalized), not new methodology invented from nothing.
**Downstream impact:** No data pulled, no panel write, no PQ values computed — feasibility/coverage map only. Drafted `04_code/CLAUDE_CODE_PHASE2C_DIAGNOSTIC_PROMPT.md` for the next Claude Code session. **Do not start an actual Phase 2c panel build before this diagnostic report is reviewed.**

### Entry 39 — Phase 2c diagnostic executed: only 5 of 104 NaN tokens have a defensible free PQ path (4 known + SUN net-new); TVL×turnover statistically indefensible; bridges.llama.fi now 402-paywalled
**Date:** 2026-06-25
**Spec section affected:** 4, 4.1 (token PQ source — the Entry-38 metadata audit); 6 (landmines)
**Asset(s)/period affected:** all 104 non-Gaming NaN tokens in `pq_tokens.csv` (the 111 NaN minus the 7 Gaming, which stay NaN by Entry-38 design). Diagnostic only.
**What the spec/Entry-38 wanted:** a per-token feasibility map answering, for each NaN token, *what free DeFiLlama data exists and could any of it plausibly become a transacted-value PQ given the protocol's economic model?* — ranking paths direct-volume > fee-inversion > TVL×APY > TVL×calibrated-turnover > none — plus a turnover-dispersion test on the 25-lending + 28-perp Dune cohort to decide whether TVL×turnover is defensible. **No `pq_tokens.csv` write, no PQ value, no purchase.**
**What was actually found (live, local Claude Code, full report `03_data/PHASE2C_DIAGNOSTIC_REPORT.md`, code `04_code/phase2c_{defillama_metadata,turnover_cohort,turnover_refine,verdicts}.py`, session 017):**
- **Worklist re-derived live:** 127 tokens / 16 covered / 111 NaN / 104 audited — matches the kickoff exactly. All endpoint shapes were live-verified before use.
- **Only 5 tokens have a defensible free transacted-value path; 4 were already known.** The Entry-37 Dune-spell set (**AAVE, STRK, LDO, GNS**) plus **one net-new find: SUN.** SUN.io's AMM is SunSwap, whose DEX volume sits in DeFiLlama's `dexs` vertical under `sunswap-v1/v2/v3` (the stored slug `sun.io` is absent from the vertical, which is why Phase 2 missed it) — **direct volume, no proxy**, 2020-08→2026-06, identity-verified by cmcId.
- **TVL×calibrated turnover (path 4) is NOT defensible as a level.** Pulled the full Dune cohorts (`lending.borrow` borrow-filtered, 25 proj / 816 protocol-months; `perpetual.trades`, 28 proj / 436 protocol-months), matched each to a DeFiLlama slug **verified individually by cmcId/name** (lending 21/25, perps 16/28; unmatched = dead/Terra/non-EVM), summed TVL across *all* version slugs to remove scope artifact, and computed turnover = PQ/TVL. **Lending per-project median turnover spans 0.0008→1.24 (~1,455×; ~10× even in the core cluster; the venus low tail survives scope-matching = real); perps span 0.0000→108.8 with no central tendency.** A borrowed category turnover rate would fabricate a number whose error dwarfs the signal (spec §0). At most lending's pooled median (~0.28) is a coarse order-of-magnitude rank, never a level, never for perps.
- **TVL×APY (path 3) collapses on availability:** `yields.llama.fi/pools` is a *current* snapshot, so 25 of the 28 Farm/Yield tokens (dead/delisted) have no APY; only CVX/FARM/ZBU have a current rate and none has a free historical APY series → weak (constant-APY assumption required), not built.
- **Fee-inversion (path 2) fired for zero tokens** — 26 have a Fees series but none is a single fixed volume-linked rate (L2 gas, bridge per-transfer, lending reserve factors, variable perps) — consistent with Entry 33.
- **Two NEW landmines:** (1) **`bridges.llama.fi` is fully 402-paywalled** across all endpoint shapes (`/bridges`, `/bridge/{id}`, `/bridgevolume`, `/bridgedaystats`) — the kickoff assumed it was free; the 11 bridge tokens thus have a *valid* object (transfer volume) that is merely not free, distinct from "no object." (2) The `nerve`/NVT (cmcId 8755 ≠ 5906) and `velodrome`/VELO (different VELO) **symbol collisions are live traps**, both ruled out on cmcId mismatch — exactly the NVT-collision hazard the kickoff flagged.
- **Verdict tally (104):** ✓dune_spell 4, ✓direct_volume 1 (SUN), ~weak_tvl_apy 3 (CVX/FARM/ZBU), ✗turnover_undefensible 14, ✗no_apy 25, ✗bridge_vol_paywalled 11, ✗symbol_collision 2, ✗no_economic_model 44.
**Decision made (diagnostic recommendation, for human review — nothing built or written this session):** A real Phase-2c build is worth running **only for the 5 viable tokens** — AAVE/STRK/LDO/GNS via Dune free tier + SUN via DeFiLlama dexs (sum sunswap-v1/v2/v3), **+1 net-new (SUN) over Entry 37, zero subscription.** **Report TVL×turnover and TVL×APY in the paper as explored-and-rejected**, not built — the turnover-dispersion negative result is itself a §6 methodological finding. Leave ~96 tokens documented-NaN. The token-side PQ cross-section realistically grows from 16 covered to ≈21, not "most of 111."
**Rationale:** Same Entry-30/31/32/36/37 standard — measure the right object, verify identity before trusting (the SUN/NVT/VELO cmcId checks; the version-scope-matched turnover), and report a wide/unusable dispersion plainly rather than forcing a number (spec §0). The AK-model TVL-as-flow intuition (Entry 38) is theoretically clean but founders on empirical turnover dispersion.
**Downstream impact (re-check if this changes):** A future explicitly-authorized Phase-2c build may fill the 5 viable tokens (Dune free for 4; DeFiLlama dexs for SUN) and leave the rest documented-NaN. Two paid levers that *would* extend coverage — **DeFiLlama Pro** (reopens the derivatives vertical for the 9 remaining derivatives tokens + the bridges vertical for the 11 bridge tokens) and a **bridges-API tier** — are flagged for Moazzam's decision, **not acted on** (same standing rule as Dune/Artemis). If bridges access is obtained, the 11 `bridge_vol_paywalled` tokens reopen at once. No panel outputs written — `pq_tokens.csv` and all Phase 2/2b CSVs unchanged. Session: `06_documentation/ai_conversations/session_017_2026-06-25_phase2c_diagnostic.md`. **Do not start the Phase 2c build before this report is reviewed.**

---

### Entry 40 — Sequencing decision: scale λ + build a real TVL panel before sourcing coin PQ; local repo-sync incident found and fixed
**Date:** 2026-06-26
**Spec section affected:** 3 (λ channels), 4 (TVL as a valuation-multiple denominator, distinct from PQ); process/documentation integrity (this log + `time_log.md` themselves).
**Asset(s)/period affected:** n/a (scoping decision + a repo-hygiene fix, not a data build).
**What happened:** Moazzam asked for a coverage audit of λ/TVL/PQ/NV across the full universe (delivered in chat, Cowork, 2026-06-26), then said: build λ and TVL first, decide how to source coin PQ afterward. Before drafting the next Claude Code kickoff prompt, re-verified the real ceilings this would have to work within: **127/448 tokens** have a confirmed DeFiLlama `dl_slug` match (`03_data/phase1/asset_onchain_identity.csv`) — the TVL build ceiling; **123/448 tokens** have an identified staking/lock contract address and **29/448** an auto-matched Snapshot space (vs. 55 assets actually built in `channel3_voting.csv` via the broader 56/57-space curated map, Entry 25) — the Channel-1/3 token ceilings; for coins, only **ETH** has any λ-channel data today (1/633) — staking/voting data for other PoS coins is a live-verification gap, not yet audited per-chain the way EVM sources were in Entry 21.
**Repo-sync incident found while grounding this (logged here per the open item from the prior Cowork session):** `git status` showed every tracked file as simultaneously staged-deleted and untracked, and a stale `.git/index.lock` (dated 2026-06-25 17:56, i.e. mid/post session 017) could not be removed from the Cowork sandbox (permission denied on the mounted path — consistent with a process on Moazzam's actual machine still holding it, invisible to the sandbox). Byte-level comparison of working-tree files against the already-pushed `HEAD` (`a7058f2`) showed this was **not data loss**: code and data CSVs (`phase1_assemble_lambda.py`, `lambda_panel.csv`, `pq_tokens.csv`, `PHASE2C_DIAGNOSTIC_REPORT.md`) were byte-identical to HEAD once CRLF line endings were normalized out (a Windows-checkout artifact, not content drift). Two files were genuinely stale, missing real content present in HEAD: `04_code/DATA_DECISIONS_LOG.md` (working copy stopped at Entry 32; HEAD has Entries 33–39) and `06_documentation/time_log.md` (working copy was missing the last ~6 rows, sessions 013–017). Both were restored verbatim from `git show HEAD:<path>` (plain file overwrite, not a git operation, so the held index lock was irrelevant) and verified byte-identical to HEAD afterward.
**Decision made:** (1) Scope the next Claude Code session to λ-coverage scale-up (tokens: widen Channel 1's curated EVM escrow set and Channel 3's voting-space map past their current ceilings; coins: a live source-verification pass for PoS coins beyond ETH, Entry-21-style) and a **real, persistent TVL panel for the 127 dl_slug-matched tokens** (converting `phase2c_defillama_metadata.py`'s existing `check_tvl()` presence-check, which already fetches the full series and discards it, into an actual panel write) — drafted as `04_code/CLAUDE_CODE_PHASE1_SCALE_LAMBDA_AND_TVL_PANEL_PROMPT.md`. Coin PQ sourcing is explicitly deferred to a separate, later prompt, per Moazzam's own sequencing. (2) The new prompt opens with a mandatory git-hygiene check (confirm no live git process before touching `.git/index.lock`; re-verify `DATA_DECISIONS_LOG.md`/`time_log.md` against `HEAD` before appending) so a future session doesn't silently build on, or re-corrupt, a stale local copy of either log.
**Rationale:** Matches the project's own "verify before building" discipline (spec §0, Entry 21) applied to the repo's own bookkeeping, not just external data sources — an append-only audit log that silently lost entries would defeat its own purpose. TVL is being built as a **valuation-multiple denominator (NV/TVL)**, not a PQ proxy — Entry 30's stock-vs-flow rejection of TVL-as-PQ stands unchanged.
**Downstream impact (what should be re-checked if this decision changes):** If the index.lock turns out to reflect a genuinely still-running process on Moazzam's machine, the next session's `git add -A`/commit will fail loudly (safe) rather than corrupt anything further. Coin PQ sourcing remains fully open and unscoped — to be addressed in a dedicated future prompt once λ/TVL are in hand.

### Entry 41 — Session 019 executed: λ scaled to 1,688 asset-months / 58 assets (coin staking ETH→ETH+ADA+XTZ; +4 token λ assets); real TVL panel built (99 tokens / 4,999 asset-months)
**Date:** 2026-06-26
**Spec section affected:** 3 (λ Channels 1 & 3), 4.1–4.2 (TVL as a valuation-multiple denominator, not PQ).
**Asset(s)/period affected:** λ panel (`lambda_panel.csv`) and a new TVL panel (`tvl_panel.csv`), 2018–2026 monthly, observed asset-months.
**What happened:** Ran the Entry-40 kickoff (`CLAUDE_CODE_PHASE1_SCALE_LAMBDA_AND_TVL_PANEL_PROMPT.md`). Step 0 hygiene: no git process, no `index.lock`, clean tree — the Entry-40 stale-index incident did **not** recur locally; live-re-derived next-numbers (Entry 41, session 019, both confirmed not trusted). **λ assembly logic was not touched** — only channel input files were widened; `phase1_assemble_lambda.py` auto-globbed them.
**(A.1 — token Channel 1, individual Entry-26 verification, live `balanceOf` + `getLogs` reconstruction).** Each candidate accepted only if a single contract holds the BASE token directly (balanceOf == locked supply). **VERIFIED + built** (`phase1_channel1_evm_locks_ext.py`, 4 assets / 214 asset-months; reconstructed latest-locked matched live balanceOf to rounding): PENDLE (vePENDLE, 22.9%), LQTY (LQTYStaking, 57.8%), 1INCH (St1inch, 15.8%), RPL (RocketVault, 47.3% — FLAGGED shared-vault, kept under the same standard as xSUSHI/stkAAVE). **VERIFIED mechanism but series DEFERRED:** GMX (StakedGmxTracker ~65%, Arbitrum) — full-history `getLogs` over Arbitrum's millions-of-blocks/month is impractically slow on the free tier (>60 s/month); row left commented with rationale, to be built later via `account/tokentx` pagination. **REJECTED (documented, not silently proxied — the veBAL/SNX standard):** MKR (DSChief holds 0.5% post-Sky migration), BAL (veBAL locks an 80/20 BPT, not BAL), COMP (in-wallet delegation, no lock), RUNE (native THORChain L1, placeholder address), ANGLE (not in universe).
**(A.2 — token Channel 3).** governanceID cross-check: 0 new (all 29 auto-matched spaces already in the curated map). Probed the Entry-25 "not on Snapshot" gap list live (id_in + `ranking(search:)`): **two were actually on Snapshot and were missed** — **ENA → `ethenagovernance.eth`** and **PERP → `vote-perp.eth`**, both official, active, token-weighted (erc20-balance-of on the canonical token); added to the curated map (now 57 spaces / 53 vw_turnout assets). ONDO/WLD = impostor/spam spaces only; PENDLE's top hit `sdpendle.eth` is StakeDAO's third-party locker, not Pendle's own governance (and PENDLE is now C1-covered); MKR/LQTY/RUNE expose no verifiable clean Governor → no `VoteCast` reconstruction (no-guess rule).
**(A.3 — coin Channel 1, Entry-21-style LIVE audit).** Only two PoS chains publish a free, keyless, historical staked-supply series: **ADA** via Koios `epoch_info.active_stake` (built, 70 months, 49→74%, Shelley-gated to 2020-08) and **XTZ** via TzKT `cycles.totalBakingPower` (built, 95 months, FLAGGED for the 2024 Paris baking-power redefinition, analogous to ETH's Shapella caveat). New `phase1_channel1_pos_coins.py` (2 assets / 165 asset-months; no value guessed or interpolated). **Live-verified gaps:** Cosmos `/staking/pool` current-only (ATOM/INJ/SEI/KAVA/CELO — confirms Entry 24), SOL/HBAR current-only, ICP ic-api 404, DOT/KSM keyed (Subscan), AVAX/NEAR/ALGO/TRX/EOS/SUI/APT no free historical.
**(B — real TVL panel).** New `phase2_build_tvl_panel.py` converts Phase-2c's discard-everything `check_tvl()` into a full monthly-grain panel for all 127 dl_slug-matched tokens → `03_data/phase2/tvl_panel.csv`: 97 non-empty, 4,895 asset-months, 0 fetch failures, 30 expected empties (aggregators/DAOs/chains with no protocol TVL). Stretch goal (low yield, as anticipated): of 321 unmatched tokens, only 9 exact symbol+name matches; verified-and-added **AXL** (axelar, $135M, cmcId null — clean join miss) and **PERP** (perpetual-protocol, $0.4M, DeFiLlama cmcId stale=1301 but slug unambiguously PERP) → **99 tokens / 4,999 asset-months, 2019-12→2026-05**; rejected CVP/POLS (cmcId-mismatch collision risk, the Entry-39 landmine) and METIS/HONEY/PUMP/PYTH/WLFI (zero TVL).
**Decision made:** Accept the four mainnet C1 tokens, the two C3 spaces, and the two PoS coins into λ; accept the TVL panel as the NV/TVL denominator. Defer GMX's series and all other PoS coins as documented free-tier gaps. **λ before→after: 1,374→1,688 observed asset-months; 52→58 distinct assets (coin 5→7, token 43→47, other 4).** Full account in `03_data/PHASE1_LAMBDA_SCALE_AND_TVL_PANEL_REPORT.md`.
**Rationale:** Every addition cleared the project's existing standards — Entry-26 single-contract base-token-lock verification for A.1 (with explicit rejections, not silent proxies), live Snapshot strategy verification + the token-weight guard for A.2, Entry-21 live free-access auditing for A.3, and `cmcId`-only joins throughout (the AXL/PERP loose matches were each verified individually before acceptance, guarding the VELO/velodrome collision mode). TVL is a stock used only as a valuation-multiple denominator (Entry 30 unchanged).
**Downstream impact (what to re-check if this changes):** GMX's C1 series is the one accepted-but-unbuilt item — build via `tokentx` pagination next. Coin staking beyond ADA/XTZ and coin PQ both remain open and need either a keyed indexer (a Moazzam purchase decision) or native block iteration. The TVL panel inherits the identity map's one-slug-per-cmcId choice (AAVE→aave-v2 only) — flag for whoever builds the NV/TVL ratio. Channel 2 (holding duration) still 0, still a gap (Entry 24). Coin PQ untouched — next session, separately authorized.

### Entry 42 — "Bucket 2" verification (17 non-EVM PoS coins): SOL/DOT/KSM/TRX upgraded to free-verified, no purchase needed; HBAR/SUI reframed as free-data-but-needs-engineering; CELO flagged as a possible EVM-reclassification; ATOM/INJ/SEI/KAVA/AVAX/NEAR/EOS/ICP/APT remain open gaps; ALGO confirmed a structural (not a money) gap. Refines/corrects Entry 41's A.3 quick-pass line for SOL, TRX, HBAR, SUI.
**Date:** 2026-06-26
**Spec section affected:** 3.1 (staking/locking ratio) — extends Entry 21/41's "verify live before building" discipline from chain-native RPC checks to third-party/official indexer products, for the non-EVM coins Entry 41's A.3 pass flagged as "no free historical" or "current-only" after checking only each chain's own RPC/LCD.
**Asset(s)/period affected:** the 17 named coins behind Entry 41's A.3 gap list — ATOM, INJ, SEI, KAVA, CELO, SOL, HBAR, ICP, DOT, KSM, AVAX, NEAR, ALGO, TRX, EOS, SUI, APT — representative of the ~170-coin non-EVM PoS portion of the universe still missing a λ Channel-1 series. Diagnostic only; nothing built, no key obtained, no purchase made.
**Context:** Moazzam asked, after the λ/TVL coverage audit, to verify this specific gap before any purchase decision — i.e. check live whether the paid chain-indexers Entry 41 gestured at actually contain the needed historical bonded-stake series at all, and whether a free path was missed.
**What was found, live, this session (WebSearch + targeted doc fetches; no API keys used or obtained):**
- **SOL — free, verified, upgrade.** validators.app (Solana, operated by Block Logic LLC) requires only a free signup + API token (`Token` header); no paid tier found anywhere in its docs. Its `/api/v1/epochs/:network.json` endpoint returns one record per epoch with `total_active_stake` and `total_rewards`, depth 169+ epochs in the documented example — a genuine historical total-active-stake series. Corrects Entry 41's "SOL current-only," which checked only Solana's own RPC, not this third-party indexer.
- **DOT / KSM — free, verified (medium confidence), upgrade.** Subscan's documented endpoint list tags certain endpoints with a literal `[PRO]` prefix (e.g. "[PRO] List multichain account assets"); the entire Staking section, including "List validator era statistics" (per-era stake), carries no such tag — i.e. it reads as free-tier. Could not confirm the exact JSON schema directly (docs are JS-rendered; raw fetch only returns sidebar nav), so this is an inference from the tagging convention, not a pixel-verified response body. Recommend a 5-minute live key-signup-and-call check before relying on it in a build.
- **TRX — free, verified, upgrade.** TronScan's public `freezeresource` endpoint (`start_day`/`end_day` params) explicitly returns historical frozen-TRX/freeze-ratio for a date range. TronScan's API-key tiers (mandatory since 2024) are Free (60 req/hr, all read endpoints, auto-approved signup, no payment) / Developer (600 req/hr) / Partner (unlimited) — the Free tier covers this endpoint. Corrects Entry 41's "TRX no free historical," which had not found this endpoint.
- **HBAR — free data exists, but assembling the network series is an engineering task, not a purchase.** Hedera's own official, free, public Mirror Node REST API has `/api/v1/network/stake` (current aggregate) and the balances endpoint accepts a `timestamp` param that falls back to 15-minute balance-file snapshots — i.e. point-in-time historical account state is natively free. There is no single endpoint that already sums "total staked across all accounts" per past snapshot; building that series means iterating accounts' `staked_node_id`/`staked_account_id` at each snapshot. Corrects Entry 41's "HBAR current-only" only insofar as the underlying data is historical; the *aggregation* is unbuilt.
- **SUI — free data exists on-chain, same engineering caveat as HBAR.** Sui's `staking_pool` module maintains an on-chain exchange-rate-history table keyed by epoch (since each pool's activation epoch), queryable via the standard free public RPC/GraphQL — no third-party vendor needed. Total-network stake-per-epoch requires summing across all validator pools, an engineering task, not a payment gate.
- **ALGO — structural gap, confirmed not a "buy a vendor" problem.** A Nodely (Algorand infra provider) blog post states plainly that no Algorand ledger dataset, public or commercial, contains precomputed/sampled participation data; a historical online-stake series has to be computed by replaying the chain's full transaction history from scratch. This is qualitatively different from the other gaps here: paying for *any* indexer would not solve it — the indexer itself would have to build the same from-scratch replay.
- **CELO — possible reclassification candidate, not yet built.** Celo migrated its mainnet to an Ethereum L2 (OP Stack rollup) on 2025-03-26. Confirmed staking/validator-election mechanics (CELO locking + voting for validators) continue post-migration, just decoupled from consensus (validators now run community RPC nodes; sequencer fees are separate from staker rewards). Because Celo is now EVM-compatible with its own Etherscan-family explorer (Celoscan), its locked-CELO contract may be reconstructable via the same `getLogs` method already used for ETH/EVM tokens (Entry 21/26) instead of needing a non-EVM chain indexer at all — i.e. CELO may not belong in this bucket going forward. Not verified: whether the legacy LockedGold/Election contract is still the live locking mechanism post-migration, or whether Celoscan exposes its logs the way Etherscan does. Flagged for a follow-up identity-map check (Entry 22-style), not acted on.
- **ATOM, INJ, SEI, KAVA (Cosmos-SDK appchains) — no change, still an open gap.** Mintscan/Cosmostation's official API is contact-based (`api@cosmostation.io`), pricing undisclosed — an Artemis-Enterprise-style sales process, not a self-serve purchase decision. Bitquery has a disclosed free-dev-tier + usage-based paid tier and confirmed general "Cosmos" coverage, but per-appchain coverage of Injective/Sei/Kava specifically, and whether its Cosmos staking data is a ready pool-level historical bonded-total vs. raw per-tx delegation events needing aggregation, is unconfirmed. Per-chain dashboards (injscan.com, Seistream, kava.mintscan.io) show only current-state snapshots.
- **AVAX — promising official first-party candidate, pricing tier unconfirmed.** Ava Labs' own AvaCloud Metrics API has a dedicated "Staking Information" feature (validator/delegator counts, staking weights) explicitly described as historical and as powering the official Avalanche Explorer's own graphs — the strongest *type* of source in this whole list (official, first-party, purpose-built). AvaCloud's disclosed pricing structure found in search (Starter/Pro/Enterprise, a "$999/mo Builder" plan) reads as being for its L1-deployment/infrastructure product line, not necessarily gating pure read access to the Metrics API — genuinely unclear without checking the API-key signup flow directly.
- **NEAR — two unconfirmed candidates.** Pikespeak (registration/API-key gated, explicitly advertised as supporting historical validator/delegator data, pricing undisclosed) and NearBlocks (official-style explorer API; current `/v1/stats` confirmed; historical-staking-specific endpoint and pricing not confirmed).
- **EOS, ICP — no source found.** No historical staked/vote-weight (EOS) or neuron-stake (ICP) API located, free or paid, in this pass.
- **APT — free official API exists but looks current-state-only.** Aptos Labs' public Indexer GraphQL API (`api.mainnet.aptoslabs.com/v1/graphql`) is free and historical for transactions/assets generally, but the one staking-specific table found, `current_delegated_staking_pool_balances`, is named (and appears to behave) as current-state-only, the same limitation Entry 21 found for free-tier `eth_call`. A historical-staking-balances table was not located.
**Decision made:** No purchase made or recommended yet. Reclassify the working picture of this gap from a flat "170 coins need a paid indexer, unverified" into four groups: (1) **free and verified, no purchase needed** — SOL, TRX, plus DOT/KSM at medium confidence (schema not pixel-confirmed); (2) **free data exists but needs engineering, not money** — HBAR, SUI, and ALGO (ALGO is the hardest of the three: full transaction replay, not just multi-pool summation); (3) **a paid/contact-based path may exist but is unconfirmed** — ATOM/INJ/SEI/KAVA (Mintscan contact-sales or unconfirmed Bitquery coverage), AVAX (AvaCloud, pricing-page ambiguity), NEAR (Pikespeak/NearBlocks); (4) **no source found yet, free or paid** — EOS, ICP, APT (APT has a free official API but it looks current-state-only for staking specifically). CELO is provisionally pulled out of this bucket pending confirmation that its post-L2-migration locking contract is EVM-`getLogs`-reconstructable the way ETH/EVM tokens already are.
**Rationale:** Matches the project's standing rule (spec §0, Entry 21) to verify access live before treating a gap as "needs a purchase" — several of these chains turned out to have a free path Entry 41's shallower native-RPC-only check missed, while ALGO turned out to be a case where money would not even help. Keeping the four-way split (free-done / free-but-engineering / paid-unconfirmed / no-source) instead of a single verdict avoids either overstating progress or sending Moazzam toward a purchase that wouldn't solve the actual problem (ALGO) or duplicating a path that's actually free (SOL/TRX/DOT/KSM).
**Downstream impact (what to re-check if this decision changes):** Before any Phase-1-style build: (a) live key-signup-and-call test for Subscan's era-statistics endpoint and validators.app's epochs endpoint, to move DOT/KSM/SOL from "verified via docs" to "verified via response body," matching the A.1/A.2/A.3 standard in Entry 41; (b) the HBAR/SUI aggregation jobs are real (if modest) engineering work, not zero-cost — scope before committing; (c) CELO's EVM-reconstructability needs a direct identity-map check (does Celoscan expose the legacy LockedGold/Election contract's logs) before it can be moved out of this bucket for real; (d) AvaCloud/Pikespeak/NearBlocks/Mintscan/Bitquery pricing-page ambiguities all need a direct signup-flow check (not just search results) before Moazzam is asked to make any purchase call; (e) EOS/ICP/APT-historical remain genuinely unresolved — no recommendation to make here yet. No purchase has been made; nothing in this entry authorizes one.

### Entry 43 — Bucket 2 Tier 1: TRX + SOL coin staking BUILT, keyless (no signup); corrects Entry 42's "free with signup"
**Date:** 2026-06-26
**Spec section affected:** 3.1 (staking/locking ratio, coins).
**Asset(s)/period affected:** TRX (cmc 1958) 2019-12→2026-06; SOL (cmc 5426) 2023-02→2026-06.
**What the spec wanted:** staked-or-locked / circulating supply at month-end, from each chain's canonical free source.
**What was actually available (live, response-body verified this session):**
- **TRX — keyless.** TronScan `apilist.tronscanapi.com/api/freezeresource?start_day=YYYY-MM-DD&end_day=YYYY-MM-DD` returns full **daily** history with **NO API key** (field `total_freeze_weight` = total frozen TRX, already in TRX not sun). History starts ~2020-05 (2019 returns `total:0`). This **corrects Entry 42**, which said TRX needed a free TronScan signup — the read endpoint answers unauthenticated. Built 78 months, ratio 26%→56% (latest 49%).
- **SOL — keyless, ~2023-01+ depth.** validators.app `/api/v1/epochs/mainnet.json?per=200&page=N` returns `total_active_stake` (lamports /1e9 = SOL) **without an API token** for every epoch validators.app recorded stake for — which begins ~epoch 414 (~2023-01); earlier epochs return `total_active_stake=null` on the free/keyless tier. The null pattern is **time-based, not all-or-nothing**, i.e. a data-vintage limit (validators.app did not collect the figure pre-2023), not a key paywall — so a token would not retroactively add it. This **corrects/refines Entry 42's** "free, verified" to "free **and keyless**, but only ~2023-01+ depth." Built 40 months, ratio ~74%.
**Decision made:** Accept both into λ Channel 1. New script `phase1_channel1_pos_coins_bucket2.py` → `03_data/phase1/channel1_pos_coins_bucket2.csv` (118 asset-months, 2 assets; picked up by the `channel1_*.csv` glob). No value guessed/interpolated; denominator = panel circulating supply (cmc_id+month), same convention as ADA/XTZ (Entry 41).
**Rationale:** Both cleared the project's "verify access live, response body not docs" rule (spec §0, Entry 21/42) — and turned out **more** open than Entry 42 inferred (keyless, no signup), so no purchase or even signup is needed.
**Downstream impact (re-check if this changes):** SOL pre-2023 months stay NaN (no free source has them); a few early SOL months have staking_ratio>1 (active stake includes CMC-non-circulating tokens) — kept un-capped and flagged, since λ z-scores on relative rank, not level. If validators.app ever gates `total_active_stake` behind a token, this build breaks and needs the key.

### Entry 44 — Bucket 2 Tier 2: DOT/KSM Subscan era-stat is key-gated (HTTP 403 unauth); corrects Entry 42's docs-level "free-tier"
**Date:** 2026-06-26
**Spec section affected:** 3.1 (staking ratio, coins); access-verification discipline (spec §0, Entry 21/42).
**Asset(s)/period affected:** DOT (cmc 6636), KSM (cmc 5034) — not built this session.
**What the spec wanted (kickoff Tier 2):** sign up for a free Subscan key, call the validator era-statistics endpoint live, confirm per-era bonded totals in the response body; build only if confirmed; do not pay for Pro.
**What was actually found (live):** `polkadot.api.subscan.io/api/scan/staking/era_stat` (POST) returns **HTTP 403** `{"code":403,"message":"Subscan API strictly requires an API key. Unauthenticated access is disabled."}`. Subscan's support/pricing confirms a **Free Plan** exists and is self-serve (register at pro.subscan.io to generate a key), and **all** API requests require a key. So Entry 42's inference — that era_stat reads as free-tier because it carries no `[PRO]` tag — could **not** be response-body confirmed: the endpoint is unreachable without *any* key, and the free key requires an interactive, email-verified web signup that could not be completed in this non-interactive session.
**Decision made:** Do **not** mark DOT/KSM built. Record this as a correction to Entry 42 (from "free, medium-confidence via docs" to "key-gated; a free self-serve key likely covers era_stat but is unconfirmed and was not obtainable headless"). The build path is otherwise ready: a free Subscan key dropped into `04_code/.api_keys.json` would let `phase1_channel1_pos_coins_bucket2.py` be extended to call era_stat and reconstruct per-era bonded totals. **No Subscan Pro purchase, per the rule.**
**Rationale:** The project's standing rule is response-body verification, not docs inference (the very gap this session was created to close). A 403 is a response body that says "key required" — honest to report as a gate, dishonest to treat as built.
**Downstream impact:** Flagged for Moazzam to obtain the **free** (not Pro) Subscan key via the self-serve signup; once present, DOT/KSM become a ~5-minute extension. No purchase is authorized by this entry.

### Entry 45 — Bucket 2 Tier 3: HBAR + SUI free data exists but the network-series aggregation is keyless-intractable (documented gaps, scoped)
**Date:** 2026-06-26
**Spec section affected:** 3.1 (staking ratio, coins).
**Asset(s)/period affected:** HBAR (cmc 4642), SUI (cmc 20947) — not built.
**What the spec wanted (kickoff Tier 3):** build the aggregation if tractable; if genuinely intractable, log a documented gap rather than ship a partial series.
**What was found (live):**
- **HBAR.** Hedera Mirror Node `/api/v1/network/stake` is free/keyless but returns only the **current** aggregate (`stake_total` = 1.461e18 tinybars ≈ 14.6B HBAR) and takes **no** timestamp param. A historical network-staked series would require iterating `/api/v1/accounts` (and the balances endpoint's 15-min snapshot files) to sum `staked_node_id`/`staked_account_id`-linked balances at each past snapshot — millions of accounts × hundreds of snapshots, intractable keyless. Confirms Entry 42's engineering framing.
- **SUI.** `suix_getLatestSuiSystemState` is free/keyless and gives the **current** total stake (sum of `stakingPoolSuiBalance` across 129 active validators = 7.23B SUI), but RPC exposes **only the current** system state. A historical per-epoch total needs reading every validator pool's on-chain `exchange_rates` table object across all epochs since each pool's activation — engineering work, keyless-intractable.
**Decision made:** Leave both as **documented open gaps** (scoped, not partial-shipped). No interpolation, no current-value-carried-backward.
**Rationale:** Shipping a one-point current snapshot as if it were a time series, or back-filling it, would violate the no-guess rule and the "don't ship a partial series" instruction.
**Downstream impact:** Both are recoverable with real (if modest) engineering — an account-snapshot batch job (HBAR) or a multi-pool exchange-rate crawl (SUI) — or a keyed indexer; neither is a free, ready-made series today.

### Entry 46 — Bucket 2 Tier 4: CELO EVM-reclassification CONFIRMED, but free getLogs reconstruction fails the Entry-26 cross-check (3x undercount) → documented gap, not shipped
**Date:** 2026-06-26
**Spec section affected:** 3.1 (locking ratio); Entry-26 single-clean-escrow standard + its balanceOf==locked cross-check.
**Asset(s)/period affected:** CELO (cmc 5567) — checked, not built.
**What the spec wanted (kickoff Tier 4):** confirm the legacy LockedGold/Election contract is still live post-2025-03 L2 migration and whether Celoscan exposes its logs; if yes, build with the SAME getLogs method as Entry 26; if no, leave as an open Bucket-2 gap.
**What was found (live):** Reclassification **confirmed** — Celo is on Etherscan V2 (chainid 42220, covered by the existing free multichain key; confirmed in `/v2/chainlist`), and the legacy LockedGold `0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E` is still the live custody: live `balanceOf` 85.65M CELO, on-chain `getTotalLockedGold()` 82.43M CELO (the ~3.2M gap is pending-withdrawal CELO still in the contract). **BUT** the free getLogs reconstruction does **not** reproduce that on-chain total, failing the Entry-26 cross-check by ~3×:
  - GoldToken (`0x471E…438`) Transfer in/out of LockedGold → only **2.0M** CELO. Celo's **native** CELO locking (`lock()` sends native value) does not emit a standard ERC-20 Transfer on GoldToken, so Transfer logs miss almost all of it.
  - LockedGold's own native events `cumsum(GoldLocked)+cumsum(GoldRelocked)−cumsum(GoldUnlocked)` → only **25.8M** CELO (lock 676M / unlock 662M churn nets tiny) vs the 82.43M target. The ~57M shortfall is locked CELO carried over as **state** in the 2025-03 L2 migration with no re-emitted lock event on the indexed chain.
The only clean number is historical `getTotalLockedGold()`/`balanceOf`, i.e. archive `eth_call` / Etherscan `balancehistory` — a PRO endpoint, not free.
**Decision made:** Do **not** ship CELO (it fails its own cross-check). Record the reclassification as confirmed (CELO is an EVM chain on the existing key, not a non-EVM-indexer problem) but the **free-tier log reconstruction as inadequate**. Documented open gap. Check code preserved in `phase1_channel1_pos_coins_bucket2.py` (`celo_series`) and `04_code/_celo_event_check.py`.
**Rationale:** Spec §0 / the flag-don't-ship rule: a 3× undercount that misses the migration-carried state is not a defensible locking ratio; better an honest gap than a wrong number entering λ.
**Downstream impact:** CELO becomes buildable only with historical `getTotalLockedGold()` (archive/PRO `eth_call`) or a Celo indexer that exposes it. The Tier-4 instruction's premise ("same getLogs method as Entry 26") does not hold for a native-asset L2-migrated lock.

### Entry 47 — Bucket 2 Tier 5/6: live access-gate check for ATOM/INJ/SEI/KAVA/AVAX/NEAR/EOS/ICP/APT — no self-serve free path, no purchase
**Date:** 2026-06-26
**Spec section affected:** 3.1 (coins); access-verification discipline.
**Asset(s)/period affected:** ATOM (3794), INJ (7226), SEI (23149), KAVA (4846), AVAX (5805), NEAR (6535), EOS (1765), ICP (8916), APT (21794) — none built.
**What the spec wanted (kickoff Tier 5/6):** visit the actual signup/pricing flow, attempt a free self-serve signup only where genuinely free, report the gate type per chain, **do not purchase**.
**What was found (live pricing/signup pages, this session):**
- **ATOM/INJ/SEI/KAVA (Cosmos):** Mintscan/Cosmostation API is **contact-sales**, pricing undisclosed (not self-serve). Bitquery's Developer tier is a **trial only** — 10K points for the first month, then upgrade/contact — not a sustained free tier; per-appchain historical bonded-total coverage and points cost remain unconfirmed. No self-serve free path.
- **AVAX:** AvaCloud Metrics API has a historical "Staking Information" feature, but the free-read vs paid gate is **not determinable** from the public pricing pages (ambiguous, as Entry 42 found) — needs a direct API-key signup-flow check.
- **NEAR:** Pikespeak (key-gated, pricing undisclosed) and NearBlocks (current `/v1/stats` only; historical-staking endpoint + pricing unconfirmed). No confirmed free historical path.
- **EOS/ICP/APT:** no free, keyless, historical staked/neuron-stake/delegation series found (APT's free Indexer GraphQL `current_delegated_staking_pool_balances` is current-state-only).
**Decision made:** No signup completed (none was genuinely self-serve **and** free **and** confirmed to carry the historical series), **no purchase made or recommended**. All nine stay open gaps with their gate type recorded.
**Rationale:** The rule is verify-live-then-report, purchase is Moazzam's alone. None of these cleared the "self-serve + free + has the series" bar; the honest output is the gate map, not a build.
**Downstream impact:** Any of these advancing requires a Moazzam-side signup/purchase decision against the recorded gate (contact-sales for Cosmos, ambiguous pricing page for AVAX, key-gated for NEAR). Nothing here authorizes a purchase.

### Entry 48 — Bucket 3 BUILT: GMX + AERO + CAKE via a validated Dune curated-transfers reconstruction; corrects the kickoff's Dune table premise; AXS rejected, VELO deferred
**Date:** 2026-06-26
**Spec section affected:** 3.1 (token locking ratio); Entry-26 single-clean-escrow standard.
**Asset(s)/period affected:** GMX (11857, Arbitrum), AERO (29270, Base), CAKE (7186, BNB) — built; AXS (6783) rejected; VELO (7127) deferred.
**Candidate derivation:** from `classification_table.csv`, `asset_class='token'` rows not already in any channel (61 live-recomputed covered cmc_ids), not one of the 5 final rejects (MKR/BAL/COMP/RUNE/ANGLE), with a governance/staking tag or `defillama_categories` value → **290 candidates** (`03_data/phase1/_bucket3_candidates.csv`) — logged, not forced to the ~73 estimate. The Entry-26 clean-single-escrow test is the real filter: the vast majority are DEX/lending/RWA/meme/chain tokens whose governance is delegation, MasterChef farming, or off-chain Snapshot — not base-token custody.
**Dune method correction (response-body verified):** the kickoff's named table **`balances_<chain>.daily_updates` DOES NOT EXIST** on the Dune free tier (query FAILED: "does not exist or it is private"). The correct free curated tables are **`tokens_<chain>.transfers`** (cumulate inflow−outflow of the escrow per month) and `tokens_<chain>.balances` (historical snapshots). BSC's schema is **`tokens_bnb`**, not `tokens_bsc`. Also: the free **Etherscan V2** key does **not** cover Base/BSC ("Free API access is not supported for this chain. Please upgrade your api plan") — it does cover Ethereum, Arbitrum, Celo — so AERO/CAKE escrows were verified via **keyless public RPC** `balanceOf` and built entirely through Dune.
**What was built (each cross-checked: reconstructed final cumulative vs live on-chain balanceOf — the Entry-26 balanceOf==locked identity):**
- **GMX** — StakedGmxTracker `0x908C…9dD4` (Arbitrum), the Entry-41 deferral, built **first** as the method confidence-check: recon 6,162,450 vs balanceOf 6,160,000 = **0.04%**. 44 λ months, ratio 57%→84%. This retires the Entry-41 "series DEFERRED for Arbitrum getLogs perf" — Dune's pre-indexed transfers table makes the full-history scan trivial.
- **AERO** — veAERO VotingEscrow `0xeBf4…e6B4` (Base): recon 968,405,575 vs balanceOf 968,403,885 = **0.00%**. 50.3% of total AERO supply locked. 26 λ months. **FLAG:** staking_ratio>1 vs CMC circulating (CMC excludes veAERO-locked AERO); ~50% vs total supply — kept un-capped & flagged.
- **CAKE** — veCAKE `0x5692…1bAB` (BNB): recon 5,896,692 vs balanceOf 5,896,692 = **0.00%**. **FLAG:** veCAKE adoption fell post-2024 → small ~1.5% lock share; clean single-contract lock kept flagged (the RPL/xSUSHI standard). 31 λ months. Built with a `block_time > 2023-10-01` floor so Dune prunes pre-escrow CAKE history and the query finishes inside the free-tier 2-min limit (the escrow held ~0 before deployment, so no locked supply is dropped).
**Rejected/deferred (documented, not silently dropped):** **AXS** REJECT — AXS staking lives on the **Ronin** appchain, not indexed by any free EVM tool (no Etherscan-V2 free coverage, no Dune curated schema); legacy Ethereum staking contract abandoned. **VELO** DEFER — v1→v2 migration split: the in-universe cmc 7127 maps to the **v1** token `0x9560e827…`, while the live veVELO locks the **v2** token `0x3c8B6502…` (a different contract); joining a v1 cmc_id to a v2-token lock is the exact cmcId/symbol collision the project forbids (Entry 39 landmine), so it is deferred pending an identity-map resolution.
**Decision made:** Accept GMX/AERO/CAKE into λ Channel 1. New script `phase1_channel1_evm_locks_bucket3.py` → `03_data/phase1/channel1_evm_locks_bucket3.csv` (101 asset-months, 3 assets; picked up by the `channel1_*.csv` glob). Free Dune key only; query budget cost is negligible (a handful of `small` executes).
**Rationale:** Each cleared the Entry-26 standard (single contract holding the base token directly, cross-checked to live balanceOf at <0.1%) on `cmc_id` joins. The Dune transfers-cumsum is the historically-correct, free, fast successor to block-range getLogs for chains the Etherscan free key can't reach or where getLogs is too slow.
**Downstream impact:** VELO is the one accepted-pending item (needs the v1/v2 identity call). The 287 non-clean-escrow candidates are not Channel-1 locks by construction (many already have a Channel-3 voting value). The `tokens_<chain>.transfers`/`block_time`-floor method generalizes to any future escrow on a Dune-covered EVM chain.

### Entry 49 — Session 020 λ assembly: 1,688 → 1,880 observed asset-months, 58 → 62 distinct assets
**Date:** 2026-06-26
**Spec section affected:** 3 (λ index assembly — counts only; assembly logic untouched).
**Asset(s)/period affected:** `03_data/phase1/lambda_panel.csv`, observed asset-months.
**What happened:** Re-ran `phase1_assemble_lambda.py` (unchanged) after dropping the four new `channel1_*.csv` series (TRX/SOL from Bucket 2; GMX/AERO/CAKE from Bucket 3) into its auto-glob. **λ before→after: 1,688 → 1,880 observed asset-months; 58 → 62 distinct assets.** Coin 7→9 (+TRX, +SOL), token 47→49 (+AERO, +CAKE; **GMX** was already in λ via its Channel-3 Snapshot space, so its new Channel-1 lock **upgraded it to 2-channel** rather than adding an asset — which is why Channel-1 gained 3 token entrants but the distinct-asset total rose by 2 on the token side). 2-channel asset-months 322→354 (+32). Ch1 standardizable months 73→78.
**Decision made:** Accept the assembled panel. Stop at Bucket 2 + Bucket 3 as instructed; do not start Bucket 1 or Phase 3 without review.
**Rationale:** Only channel input files were widened; the z-scoring/standardizability/equal-weight/no-imputation logic was not touched (it auto-globs `channel1_*.csv` + `channel3_voting.csv`).
**Downstream impact (re-check if this changes):** the AERO/SOL staking_ratio>1 flag (CMC-circulating denominator artifact) and the CAKE small-share / GMX-Arbitrum-via-Dune notes ride along in the per-series `flag` columns; λ uses z-scored relative rank, not the level, so a >1 ratio ranks correctly but should not be read as a literal locked fraction. Full account: `03_data/SESSION020_BUCKET2_BUCKET3_COVERAGE_ADDENDUM.md`.

### Entry 50 — Session 021: Token Bucket-1 exhaustive re-audit, the funnel & method (398 confirmed exact, cmcId-only DL triage, DL token-quantity discovery)
**Date:** 2026-06-29
**Spec section affected:** 3.1 (Channel-1 token locking ratio); spec Section 0 (flag, don't guess) + Section 7 (exhaust free avenues before excluding).
**Asset(s)/period affected:** the 398 token-side "unrecoverable" cmc_ids from session 020, re-audited individually.
**Context:** A Cowork review challenged session 020's "398 unrecoverable" as resting on three different rigor levels (6 individually verified, ~287 rejected at the CATEGORY level via `_bucket3_candidates.csv`, ~111 never opened) rather than one uniform per-token check. Kickoff: `CLAUDE_CODE_TOKEN_BUCKET1_EXHAUSTIVE_REAUDIT_PROMPT.md`.
**What was actually available / done:**
- **Stage 0 (worklist rebuilt live, not from cache):** in-universe `asset_class='token'` cmc_ids NOT in `lambda_panel.csv`, minus VELO = **exactly 398** (448 - 49 in lambda - 1 VELO; reconciles to the penny). The cached 290-candidate file was not trusted. Of the 6 already-rejected, only **AXS/RUNE/MKR** are inside the 398; **BAL/COMP** are already in lambda via Channel-3 voting (outside the 398); **ANGLE** is out-of-universe entirely.
- **Stage 1 (bulk DeFiLlama triage, ALL 398, by `cmcId` NEVER symbol):** live `api.llama.fi/protocols` (7,742 protocols; 1,706 carry a cmcId). **92** of 398 have a clean cmcId-matched DL protocol; **306** have no cmcId DL protocol AND no contract address on file, logged explicitly as "no on-chain identity available to check" (the honest specific reason, per kickoff). The symbol-matched `defillama_categories` in `classification_table.csv` were deliberately NOT used for promotion -- they are the Entry-20 collision landmine (DOT-cmc814, HONEY, DRIFT, VOLT, LAYER all carried spurious "Liquid Staking" from unrelated same-symbol protocols; a naive union produced 10 false HIGH + 15 false MEDIUM that strict cmcId matching collapsed to 1+1).
- **Stage 2a (DeFiLlama `/protocol/{slug}` chainTvls, all 92):** **36** expose a `staking` chainTvls bucket -- and crucially that bucket carries a raw **staked-TOKEN-QUANTITY** series (`chainTvls['staking']['tokens']`), not just the USD value the kickoff anticipated. Computed DL-staked-qty / panel circulating for all 36 (`_stage2_ratios.csv`).
**Decision made:** Treat the DL token-quantity series as a *locator* (to find the escrow), not as the shipped numerator. Route every one of the 36 staking-bucket tokens into a Stage-2b on-chain single-escrow test (no sampling). Log every one of the 398 with a token-specific reason -- no category verdicts. Staging artifacts: `_token_bucket1_worklist.csv`, `_stage1_triage.csv`, `_stage2a_dl_tvl.csv`, `_stage2_ratios.csv`.
**Rationale:** Matches the kickoff's funnel and the project's cmcId-only rule; concentrates effort on the 36 where a base-token lock is even plausible while still giving the other 362 an individual line.
**Downstream impact:** Stage-2b verdicts in Entry 51 (builds) and Entry 52 (rejections). The cmcId-only-vs-symbol distinction is the reason the HIGH/MEDIUM set is small but clean.

### Entry 51 — Session 021: five Bucket-1 BUILDs (API3, ORBS, IQ, VVV) + VELO deferral RESOLVED; lambda 1,880->2,080 / 62->67
**Date:** 2026-06-29
**Spec section affected:** 3.1 (Channel-1 locking ratio); Entry-26 single-clean-escrow standard; Entry-48 Dune curated-transfers method.
**Asset(s)/period affected:** API3 (7737), ORBS (3835), IQ (2930), VVV (35509), VELO (7127) -- all built into lambda Channel 1.
**What was available (Stage 2b, live, response-body verified):** For each of the 36 staking-bucket tokens, a Dune `tokens_<chain>.balances`/net-transfers top-holder query tested the Entry-26 identity: does ONE contract hold the base token in the DL-reported staked amount? **Five pass cleanly** (top holder == DL staked qty -> single-contract base-token custody), then the full series was reconstructed by cumulating `tokens_<chain>.transfers` in/out of that escrow and cross-checked to live `balanceOf` (the Bucket-3 method):
- **API3** -- Api3Pool `0x6dd655...c76d76` (Ethereum), recon 64,354,124 == balanceOf, 0.00%. ~74%. Reward-staking (xSUSHI/stkAAVE-style).
- **ORBS** -- StakingContract `0x01d59a...656c3` (Ethereum), recon 1,841,060,162 == balanceOf, 0.00%. ~42%. (Top holder was a treasury; the 3rd holder matched DL exactly -- the escrow.)
- **IQ** -- HiIQ veIQ `0x1bf545...e16ba` (Ethereum), recon 2,416,000,459 == balanceOf, 0.00%. ~9%. Curve-style vote-escrow of IQ.
- **VVV** -- Venice staking `0x321b7f...f340ff` (Base), recon 33,279,865 == balanceOf, 0.00%. ~73%. (Base balances table times out on free tier -> escrow located via net-transfers.)
- **VELO** -- veVELO VotingEscrow `0xfaf8fd...06787d` (Optimism), recon 1,295,615,052 == balanceOf, 0.00%. ~7.4%. **This resolves the Entry-48 deferral.** Entry 48 deferred VELO believing cmc 7127's token `0x9560e827...` was a defunct "v1" token distinct from the v2 lock. DeFiLlama's OWN Velodrome **V2 and V3** entries BOTH carry `address=optimism:0x9560e827...` -- i.e. it is the CURRENT canonical token; CMC (7127->`0x9560e827`) and DeFiLlama (V2/V3->`0x9560e827`) agree. That is the documented, non-guessed mapping the kickoff required; no collision remains.
**Decision made:** Accept all five into lambda. New script `phase1_channel1_evm_locks_bucket1.py` -> `03_data/phase1/channel1_evm_locks_bucket1.csv` (200 asset-months, 5 assets; picked up by the `channel1_*.csv` glob). Re-ran `phase1_assemble_lambda.py` (logic untouched). **lambda before->after: 1,880 -> 2,080 observed asset-months; 62 -> 67 distinct assets (token 49->54).** 2-channel asset-months unchanged at 354 (none of the five had a prior Channel-3 value).
**Rationale:** Each cleared the Entry-26 standard (single contract holding the base token directly, cross-checked to live balanceOf at 0.00%) on cmcId joins -- the exact xSUSHI/stkAAVE/GMX bar. The DL token-quantity series only located the escrow; the shipped numerator is the on-chain reconstruction.
**Downstream impact (re-check if this changes):** **FLAG** -- API3 and ORBS show `staking_ratio>1` in some months (CMC `circulating_supply` excludes the pooled/staked tokens, the AERO/SOL artifact, Entry 49) -- kept un-capped and flagged; lambda uses z-scored rank not level. VELO has 37 months of lock data but only 11 observed lambda months (panel visibility). The VELO resolution overrides Entry 48's DEFER; if a future identity-map pass disputes the `0x9560e827` canonical-token finding, re-open it.

### Entry 52 — Session 021: the 393 rejections (clustered), Artemis re-test, 6-reconfirm, Dune budget, follow-ups
**Date:** 2026-06-29
**Spec section affected:** 3.1; Section 0 (flag-don't-ship); access-verification discipline.
**Asset(s)/period affected:** the 393 of 398 that did NOT build, + the 6 reconfirm + ANGLE.
**What was found / decided (every token has its own row + reason in `03_data/phase1/token_bucket1_full_audit.csv`, 402 rows):**
- **REJECT-mechanism (367):** specific protocol-design reasons no single-contract base-token lock exists. The Stage-2b multi-contract/native cases (the CELO lesson -- an honest gap beats a wrong number): **EIGEN** (EigenLayer restaking spread across strategy contracts; top holder 184M vs DL 296M), **ILV** (multi-pool core staking), **KEEP** (staking migrated to the T token), **HEX** (staking internal to the HEX contract, no separate escrow; DL bucket reads 0). Plus the 362 non-staking-bucket / no-identity tokens, each given a sector-specific line (DEX/lending/derivatives/gaming/L1-L2/DePIN/meme/wrapped-LST/governance-only/no-identity) rather than a category verdict.
- **REJECT-no-data (29):** plausible mechanism, no free source. No single contract reproduces the DL staked figure (**BTCST, ZBU, PEAK, KAITO, MBOX, TIME, ATH, AKRO, SUPER, EPS, AUCTION, MVL, MAGIC, BAKE, RFOX, MYX, SFI**; treasury/LP holders dominate balances); DL staking bucket reads 0 (**SFUND, ADF, FLEX, CASINO**); non-EVM staking outside the free EVM Dune curated-transfers method (**HXRO** Solana, **SUN** Tron, **ORN** TON, **TLM** WAX, **C98** TomoChain, **BRISE** Bitgert); cmcId-collision artifact (**WARP** -- DL maps slug `polkastarter` to cmcId 1166 -> impossible 1764% ratio, the Entry-39 landmine).
- **Artemis (Stage 2c), re-tested live:** `app.artemis.xyz` 308-redirects to `classic.artemis.ai`, which serves a JS-rendered SPA with no server-side per-asset staking data retrievable without login. No free per-asset staking-ratio surface -- reconfirms Entry 2/14. **Not signed up, not paid.**
- **The 6 reconfirmed unchanged:** MKR (DSChief in-wallet voting), BAL (veBAL locks an 80/20 BPT not BAL), COMP (in-wallet delegation), RUNE (native THORChain L1 bonding), AXS (Ronin appchain, no free EVM index); none exposes a cmcId-matched DL staking bucket live. ANGLE confirmed out-of-universe.
**Decision made:** Accept all 393 rejections as individually documented, plus the reconfirms. **GATED = 0**: no priced self-serve option surfaced that would let a purchase recover any of the 398 -- the rejections are mechanism- or non-EVM-data-bound, not paywalled.
**Rationale:** Every avenue named in the kickoff (DeFiLlama, Etherscan-equivalent via Dune top-holder, Dune, Artemis) was checked per token before acceptance; the honest output is a specific reason per row, not a category write-off.
**Downstream impact / resource accounting:** **Dune free tier ~36 `small` executes this session (~350-400 of the 2,500 monthly credits, ~15%)** -- within headroom, flagged here per the kickoff rather than assumed. No Etherscan PRO, no paid tier, no purchase. **Open follow-up:** the 456-coin Bucket-1 has NOT had this individual re-audit and may warrant the same treatment in a future session -- do not start without review. Full account: `03_data/SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md`.

### Entry 53 — Session 022: Etherscan/non-EVM contract-read feasibility map for lambda Channels 1/2/3 (universe-wide, identification only)
**Date:** 2026-06-29
**Spec section affected:** 3 (lambda channels), 2.5 (per-asset sources); feasibility/identification, NOT a build.
**Asset(s)/period affected:** the full token+other universe (1,306) on the EVM side + the 405 off-Etherscan tokens (non-EVM). NO lambda panel modified; Entries 21-26 still govern.
**What was done (real reads, not metadata reasoning):** For every token+other asset: (1) resolved an on-chain contract via CMC `data-api detail.platforms[]` (cached `03_data/raw/cmc_detail/`) + the identity map; (2) **read the verified contract** via Etherscan-V2 `getsourcecode` (cached `03_data/raw/etherscan_src/`, proxy->implementation followed); (3) classified the lambda mechanism from the ABI (Ch1 holder-lock events {StakeStart,Staked,Locked,BalanceLocked} excluding admin/vesting; Ch3 {DelegateVotesChanged,VotingPowerChanged}); (4) **computed each candidate event's keccak-256 `topic0` and ran `logs/getLogs`** over full history -- ABI presence was NOT accepted, only emitted logs. Pipeline: `04_code/universe_lambda_pipeline.py` (resumable).
**What was found:**
- **901/1,306 EVM-reachable** (793 on free-`getLogs` chains, 108 paid-only). **Ch1 genuine getLogs-CONFIRMED = 6** (HEX,NMR,stkAAVE,XAN amount-bearing; AKRO,VSL bare `Locked()` need balance reads). **Ch3 ACTIVE getLogs-CONFIRMED = 34** (UNI,ENS,SUSHI,COMP,GTC,KP3R,BTRST,EIGEN,ONDO,STRK,MNT,BLUR,... all emit `DelegateVotesChanged`). **Ch3 ABI-present-but-needs-paid = 15** + Ch1 paid = 1 (TNC). **Ch3 infra-but-DORMANT/negligible = 15** (CORE,SUPER,ILV,FLOKI,PENDLE,...). **Ch2 = all 901**.
- **MEASURED Etherscan free-tier chain gate:** `getsourcecode` free on all chains; **`getLogs`/`tokentx` FREE only on Ethereum/Polygon/Arbitrum/Blast, PAID-only on BSC/Base/Avalanche** ("Free API access is not supported for this chain"). This is the concrete paid-API trigger: 16 BSC/Base/Avax candidates + panel-scale Ch2 throughput.
- **Non-EVM (405):** 284 have NO chain/contract identity (dead, unrecoverable); 92 on free-indexer non-EVM chains (Solana 59 dominant, Tron 8, Cosmos/Osmosis/Kava 7, +tail) -> Ch2 recoverable per chain indexer, Ch1/Ch3 need per-project Anchor/CosmWasm/Realms reads (chain-native staking/gov = gas-coin, out of token-scope) with low expected yield; 22 EVM-but-not-Etherscan (KAIA/HyperEVM/...) recoverable by the SAME method on chain-specific explorers. Live-verified free APIs: Cosmos LCD (`bonded_tokens`,`gov/proposals`), Tron TronGrid, Solana RPC, Cardano Koios.
**Decision made:** This is an identification map, not a source decision -- no panel changed. Recorded as feasibility. The corrected finding vs the earlier same-day meta-analysis (`ETHERSCAN_LAMBDA_CHANNEL_FEASIBILITY.md`, written before any read): the bucket is NOT uniformly mechanism-dead -- 24 bucket-1 tokens (and 40 universe-wide) carry getLogs-retrievable Ch1/Ch3 data the Snapshot+DeFiLlama audit never looked for. Overlap caveat: many of the 34 Ch3-active (UNI/ENS/SUSHI/COMP) likely already have a Snapshot Ch3 series (Entry 25) -> on-chain `DelegateVotesChanged` is a cross-check there, net-new only where no Snapshot turnout exists.
**Rationale:** Satisfies the spec "verify before building" + the user directive to source lambda from canonical chain data; every verdict is backed by an actual contract read and an on-chain log query, with free/paid status measured live per chain.
**Downstream impact (re-check if this changes):** Artifacts: `03_data/phase1/universe_lambda_channel_map.csv` (1,306), `etherscan_lambda_channel_map.csv` (402), `non_evm_lambda_recoverability.csv` (405), `03_data/ETHERSCAN_LAMBDA_CHANNEL_EMPIRICAL.md`, `NON_EVM_LAMBDA_CHANNEL_ASSESSMENT.md`. Next steps + next-session prompt in `06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md`. NOTHING built -- before building any series, dedupe Ch3 vs Snapshot panel and decide the Etherscan-Pro purchase for the 16 paid-chain candidates.

### Entry 54 — Session 023: HEX Channel-1 BUILT (supersedes the session-021 HEX rejection) via session-022's contract-read + getLogs event-replay method
**Date:** 2026-06-29
**Spec section affected:** 3.1 (locking ratio for staking tokens), 2.5 (per-asset sources).
**Asset(s)/period affected:** HEX (cmc_id 5015), 50 observed asset-months 2020-03..2024-05. `03_data/phase1/channel1_hex_stake.csv` (new), `03_data/phase1/lambda_panel.csv` (re-assembled).
**What the spec wanted:** locked/staked supply ÷ supply for a staking token, reconstructed from canonical chain data, cross-checked to on-chain state (the Entry-26 standard).
**What was actually available — and how this supersedes session 021:** Session 021 (SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md, logged under Entry 50/52) **rejected HEX** at "Stage 2b" with the reason *"staking internal to the HEX contract"* + *"DL staking bucket reads 0"* — i.e. its Dune-top-holder single-escrow probe found no escrow contract whose `balanceOf` reproduced a DeFiLlama staked figure (and DeFiLlama reported 0). **That rejection is superseded by this entry.** Using session 022's higher-fidelity method — read the verified HEX source (cached `03_data/raw/etherscan_src/1_0x2b591e99…json`) and confirm via `getLogs` — the actual mechanism is now resolved directly: HEX staking is **non-custodial**. `stakeStart()` calls `_burn(msg.sender, newStakedHearts)`, so staked HEX is **burned out of the ERC20 `totalSupply`** (no escrow contract holds it — which is exactly *why* session 021's single-escrow `balanceOf` probe and DeFiLlama both saw nothing), and the staked quantity lives only in the contract's internal `lockedHeartsTotal` global. This is a **genuinely different construction path than Entry 26's transfer-into-escrow reconstruction**, logged here explicitly as a new method, not silently treated as equivalent.
**Decision made (BUILD):** Reconstruct the monthly staked series exactly from the contract's own accounting: only `StakeStart` (`+stakedHearts`) and `StakeEnd` (`-`original `stakedHearts`) move `lockedHeartsTotal` (verified: a single `_lockedHeartsTotal -=` site; `StakeGoodAccounting` does not touch it). So `lockedHeartsTotal(t) = Σ StakeStart.stakedHearts≤t − Σ StakeEnd.(orig)stakedHearts≤t`, decoded on Dune (`hex_ethereum.HEX_evt_StakeStart/_StakeEnd`; `stakedHearts=(data0>>40)&(2^72−1)` via exact UINT256 integer arithmetic, verified == Python decode; StakeEnd amount recovered by joining `stakeId` back to the StakeStart decode). **Cross-check: reconstructed final = 61,900,823,759,862,091,712 hearts == live `globalInfo()[0]` read (2026-06-29) at drift 0.000000%** — the same 0.00% bar the five session-021 BUILDs (API3/ORBS/IQ/VVV/VELO) cleared. Script: `04_code/phase1_channel1_hex_stake.py` (its own builder, parallel to `eth_staking`/`pos_coins`, because there is no escrow to feed the `evm_locks_*` transfer scripts). Output picked up by the `channel1_*.csv` glob.
**Denominator (resolved explicitly, not assumed):** The HEX contract's own NatSpec states *"ERC20 `totalSupply()` is the circulating supply and does not include any staked Hearts. `allocatedSupply()` includes both"* (`allocatedSupply = totalSupply + lockedHeartsTotal`). CMC's `circulating_supply` mirrors the on-chain ERC20 `totalSupply` and therefore **excludes staked HEX** — the SAME denominator artifact as the Entry-49 AERO/SOL/API3/ORBS series, NOT a new double-count. We ship `staking_ratio = locked/circulating` (panel basis) for cross-sectional comparability with the other Channel-1 token series (λ z-scores within month — rank, not level — Entry 27/49); within HEX's observed window (2020-03..2024-05) `locked < circulating` every month so the ratio is well-behaved (14.3%→43.5%, latest 33.6%, never >1). The theoretically-clean fraction `locked/(locked+circ)` (12.5%→30.3%) is written alongside as `locked_fraction_alloc` for audit.
**Rationale:** Per the session directive, where session 022's contract-code-read + getLogs method conflicts with session 021's Dune-substitute method, the former governs. Here it does not merely "find an event" — it reconstructs a full monthly locked-quantity series that reconciles to live on-chain state at 0.0000%, clearing the same bar as the shipped BUILDs.
**Downstream impact (re-check if this changes):** λ: **2,080 → 2,130 observed asset-months, 67 → 68 distinct assets** (+HEX, single-channel Ch1). If CMC ever revises HEX circulating to an allocated-supply basis, switch the denominator to `locked_fraction_alloc` (already in the CSV). Full account: `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md`.

### Entry 55 — Session 023: AKRO Channel-1 REJECT reconfirmed (session-022's `Locked()` flag is a false positive; session-021 rejection stands, now with the contract reason)
**Date:** 2026-06-29
**Spec section affected:** 3.1 (locking ratio), 2.5 (per-asset sources).
**Asset(s)/period affected:** AKRO (cmc_id 4134). No panel changed; AKRO remains absent from λ.
**What the spec wanted:** a single staking/lock contract holding a reproducible share of AKRO supply (the Entry-26 single-escrow test).
**What was actually available — 021 vs 022 reconciled:** Session 021 rejected AKRO in the *"no single contract reproduces the DL staked figure"* cluster (with KAITO/ATH/SUPER/etc. — the "treasury dominates balances" suspicion). Session 022's universe map flagged AKRO as **"Ch1 GENUINE, `Locked()`, needs contract-balance reads"** — an apparent contradiction. Running session 022's *own* higher-fidelity method to completion (read the verified implementation, not just the ABI event name) **resolves it in favour of REJECT, and explains 022's flag as a false positive:** AKRO's address `0x8ab7404063ec…` is the **AKRO token contract itself** (`TokenProxy` → impl `AkropolisToken`), and its `Locked()` event comes from an OpenZeppelin-style `Lockable` base contract — `function lock() public onlyOwner { setLock(true); emit Locked(); }`. It is an **owner-only admin pause switch** (disables restricted methods), carries **no amount** (`event Locked()` has no parameters), and escrows **no tokens**. Live `getLogs` over full history confirms it fired **exactly once** (block 8099298, `data=0x`) — the one-time owner `lock()` call, not a staking series. Session 022's Ch1 classifier matched on the event *name* `Locked()`; the full contract read shows the event is not a holder lock/stake at all.
**Decision made (REJECT, reconfirmed):** AKRO has no staking/escrow mechanism to reconstruct. Session 021's rejection **stands**, now upgraded from "no single contract matches the DL figure" to the precise contract-level reason: *the only `Locked()` event is an admin pause flag on the token contract, not a stake.* There is no 021-vs-022 contradiction once the contract is read — both reject; 022's map row was an over-eager name-match the full Entry-26 test overturns.
**Rationale:** The session's standard is to trust 022's method where it conflicts with 021 — applied here, 022's method (read to completion) agrees with 021's verdict and supplies the better reason. A mechanism merely *named* "Locked" is not a lock; ABI-event presence was explicitly never the bar (Entry 53).
**Downstream impact (re-check if this changes):** None to λ. If AKRO's broader ecosystem (Akropolis had separate Sparta/Delphi staking pools) is ever brought in scope, those are *different contracts* (not cmc 4134's token address) and would need their own identification + single-escrow cross-check. Full account: `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md`.

### Entry 56 — Session 023: the 284 no-on-chain-identity listings documented as an acknowledged survivorship-bias limitation (not a pending data gap)
**Date:** 2026-06-29
**Spec section affected:** 2 (universe/coverage), 7 (limitations); paper data/methodology section.
**Asset(s)/period affected:** 284 token+other assets with no recoverable chain/contract identity. No panel changed.
**What the spec wanted:** a clear, reconciled account of which universe assets carry no λ data and why, distinguishing permanent unrecoverability from pending effort.
**What was actually available (re-derived live, reconciled to the penny):** From `03_data/phase1/non_evm_lambda_recoverability.csv` (405 rows): **class `NO-IDENTITY` = 284** (chain and tx_repository both null; ch1=ch2=ch3=`no` by construction). Universe reconciliation against `03_data/phase1/universe_lambda_channel_map.csv`: **1,306** token+other assets = **901** Etherscan-reachable + **405** off-Etherscan; the 405 off-Etherscan = exactly the 405 `etherscan_reachable≠yes` rows (overlap 405/405, 0 outside the map, 0 duplicate cmc_ids); the 405 = **284 NO-IDENTITY + 92 non-EVM-indexed + 22 EVM-non-Etherscan + 7 obscure**. Criteria for "dead": no contract address resolvable via CMC `detail.platforms[]` + the identity map, and no chain/explorer (EVM or non-EVM) on which any λ channel can be queried, checked across sessions 021–022. Cohort character: **83% are asset_class "other"** (non-DeFi/non-governance), **89% (252/284) are pre-2020 listings** (191 with cmc_id<2000, the earliest 2013-2017 era), with a ~32-asset tail of newer non-standard-chain assets (BRC-20/ordinals, BCH-ABC fork, etc.) whose identity the pipeline can't resolve.
**Decision made:** Classify the 284 as a **permanent, acknowledged survivorship-bias limitation, not a pending data gap** — no further recovery effort is planned (no contract, no chain identity, on any free or paid source). Paper-ready write-up saved to `03_data/SURVIVORSHIP_BIAS_NOTE.md` and mirrored in `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md` §3.
**Rationale:** These were live CMC listings in (predominantly) 2014-2018 that are now delisted/abandoned/rug-pulled with no on-chain identity to query. Folding them silently into the broad "no-data" rejection bucket would understate a genuine survivorship bias a referee will ask about. Naming it explicitly — and noting its likely *direction* (the dead cohort is disproportionately low-conviction, no-governance, no-staking "other" assets that would sit at the bottom of the λ distribution even had they survived, so their exclusion truncates the low-λ tail and makes survivors conditionally higher-λ) — is the honest treatment.
**Downstream impact (re-check if this changes):** None to the built panel. Feeds the paper's limitations/robustness discussion. If a paid multi-chain identity source is ever adopted, re-run the identity resolution before treating any of the 284 as recoverable.

### Entry 57 — Session 024 (Task A): Channel-3 on-chain governance DELEGATION sub-channel built from DelegateVotesChanged replay (21 net-new assets)
**Date:** 2026-06-30
**Spec section affected:** 3.3 (voting/governance engagement), 2.5 (governance venues).
**Asset(s)/period affected:** 21 net-new ERC20Votes-ACTIVE tokens (no Snapshot turnout series). New file `03_data/phase1/channel3_onchain_delegation.csv`; `phase1_assemble_lambda.py` extended to read it as channel `ch3_delegation`.
**What the spec wanted:** governance participation per asset-month for the 34 getLogs-CONFIRMED ERC20Votes-ACTIVE tokens (session-022 map), deduped against the existing Snapshot Channel-3 panel (Entry 25).
**What was actually available / done:** Joined the 34 on cmc_id vs `snapshot_space_map.csv`+`channel3_voting.csv`: **10 already have a Snapshot turnout series** (GTC/ENS/MNT/COMP/SUSHI/UNI/RGT/KP3R/STRK/HFT) -> cross-check only; **24 are NET-NEW**. Built a monthly series for the net-new from on-chain `DelegateVotesChanged` event replay (`phase1_channel3_onchain_delegation.py`): replay all logs in (block,logIndex) order tracking each delegate's latest `newBalance`; at each month-end block, delegated voting weight outstanding = sum of latest newBalance over all delegates; / circulating supply. Decimals read once via immutable `decimals()`; free getLogs chains only (ETH/Arbitrum/Blast). Topics: uint256 variant `0xdec2bacd...` (22 tokens), uint96 variant `0x664ef4a2...` (DDX). **Result: 21 of 24 net-new produce a ratio (560 asset-months); 3 do not** -- TOMI/UXLINK (delegation events all post-date their observed panel window -> 0 in-window, verified by block comparison) and CYBER (2 events, 0 delegated). One of the 24, **ETHDYDX, was excluded on mechanism** (`DelegatedPowerChanged`/Aave-power model where every holder auto-carries voting power -> ratio~1, NOT opt-in delegation; flagged, not shipped -- the AKRO/Entry-55 "verify the mechanism" discipline).
**Decision made (CONSTRUCT -- stated explicitly, not silently merged):** On-chain delegated voting weight is a **DISTINCT sub-channel** from Snapshot voter-turnout, NOT the same measure sourced differently. Snapshot `vw_turnout` is a per-proposal participation FLOW; delegated-weight-outstanding is a STOCK of governance-ACTIVATED supply (tokens only count as votes once delegated, incl. self-delegation). So it is written to its own file and enters lambda as a separate channel `ch3_delegation`, z-scored in its own monthly cross-section. **Governance-channel waterfall (no double-count):** only `role=='primary'` rows (the net-new tokens) enter lambda; the 10 overlap tokens are computed as `role=='crosscheck'` (validation only, excluded from lambda -- a token already represented in governance-lambda via Snapshot turnout is not also counted via delegation). Verified in the assembled panel: ch3_delegation never co-occurs with ch3_voting (2-channel asset-months unchanged at 354).
**Rationale:** Sources lambda from canonical chain data (Entry 21 "logs not eth_call"); the construct distinction + primary-only rule prevent conflating two different governance measures or double-weighting governance.
**Downstream impact (re-check if this changes):** **FLAG** -- DDX shows `delegation_ratio>1` (204%: CMC circulating excludes delegated locked/treasury supply, the Entry-49 pattern) -- kept un-capped & flagged, lambda z-scores rank not level. The empirical per-token cross-check of the 10 overlap tokens was DEFERRED (their full `DelegateVotesChanged` histories -- GTC/ENS/UNI/COMP/SUSHI/STRK -- are getLogs-heavy and did not complete in the session's budget; the construct-level distinction stands and their lambda is unchanged, still Snapshot turnout). A `CROSSCHECK=light/all` env gate is wired in the builder for a future pass. lambda contribution folded into Entry 60.

### Entry 58 — Session 024 (Task B): Channel-1 free-build — XAN BUILT; VSL/NMR/stkAAVE rejected/deferred with contract reasons
**Date:** 2026-06-30
**Spec section affected:** 3.1 (locking ratio for staking/locking tokens), 2.5 (per-asset sources).
**Asset(s)/period affected:** XAN (cmc 38481) BUILT -> `03_data/phase1/channel1_freebuild.csv` (`phase1_channel1_freebuild.py`, picked up by the channel1_*.csv glob). VSL/NMR/stkAAVE not built (documented).
**What the spec wanted:** locked/staked supply / supply for the session-022 map's "Ch1 GENUINE" set (HEX/AKRO done in 023; NMR/stkAAVE/XAN/VSL remaining), each cross-checked to live on-chain state at ~0.00% (Entry-26 bar).
**What was actually available — verified-source reads (cached `03_data/raw/etherscan_src/`, proxy->impl followed):**
- **XAN — BUILD.** XanV1 (Anoma, 2025; proxy 0xcedbea37->impl 0x03997b56). `lock(value)`->`_lock` does `lockedSupply += value; emit Locked(account,value)`; NatSpec "Permanently locks ... until upgraded"; `lockedSupply` is only ever incremented (no unlock/decrement). So locked series = cumulative sum of `Locked.value` (the HEX-style internal-accounting path, Entry 54), and **cross-check: reconstructed final 7,500,000,010 == live `lockedSupply()` (0xca5c7b91) at drift 0.000000%** -- the Entry-26 bar. **DENOMINATOR (Entry-49):** locked (7.5B) EXCEEDS CMC circulating (2.5B) -> CMC circulating excludes the locked foundation/ecosystem allocation (the HEX/AERO/API3 artifact), so `staking_ratio>1` (300%); kept un-capped & flagged, lambda z-scores rank; `locked_fraction_alloc = locked/(locked+circ)` = 75% written alongside for audit (HEX precedent). 9 observed asset-months.
- **VSL — REJECT (the AKRO pattern, exactly as the kickoff anticipated).** Direct contract `Token`/`Lockable`; `Locked()` is a BARE parameterless event fired by the `checkLock` modifier as a CYCLIC transfer-pause (each 30-day epoch: 25 days unlocked / 5 days locked; `Locked()`/`Unlocked()` on the flip). No amount, no escrow -- a contract-wide transfer freeze, not a holder conviction lock. (39 logs = the periodic flips.) Same lesson as AKRO (Entry 55).
- **NMR — DEFER to Phase 2.** NumeraireBackend (proxy->UpgradeDelegate) tournament staking; `Staked(staker,tag,totalAmountStaked,...)` amount is a per-(staker,tag) CUMULATIVE running total, decremented elsewhere by StakeDestroyed/StakeReleased, and the modern Erasure flow BURNS NMR on stake. No aggregate staked global and no escrow balance -> NO Entry-26 cross-check anchor. Flagged for a proper Phase-2 Erasure treatment rather than shipped unanchored.
- **stkAAVE (cmc 36246) — EXCLUDE.** cmc 36246 is the Staked-AAVE wrapper token; its supply already represents AAVE locked in the Safety Module, ALREADY captured in lambda via AAVE (cmc 7278, Entry 26). Building it separately double-counts the same escrowed AAVE, and as its own asset locked/circulating~1 (degenerate).
**Decision made:** Accept XAN into lambda Channel 1; reject VSL, defer NMR, exclude stkAAVE — each with the contract-level reason.
**Rationale:** Where session-022's name-level "Ch1 GENUINE" flag conflicts with the full verified-source read, the read governs (the session standard) -- here it overturns VSL (admin/cyclic pause), confirms XAN (real monotone lock with a live global cross-check), and finds NMR/stkAAVE structurally unfit for a clean single-anchor reconstruction.
**Downstream impact:** lambda contribution folded into Entry 60. If CMC ever revises XAN circulating to an allocated-supply basis, switch its denominator to `locked_fraction_alloc` (already in the CSV).

### Entry 59 — Session 024 (Task C): Channel-2 (coin-age/HODL) PROTOTYPE built + free-tier call-budget MEASURED -> confirmed Phase-2 trigger
**Date:** 2026-06-30
**Spec section affected:** 3.2 (holding-duration channel) — the Entry-24 gap.
**Asset(s)/period affected:** Prototype only (MET, cmc 2873) -> `03_data/phase1/channel2_holding.csv`; budget probe -> `03_data/phase1/_channel2_budget_probe.json`. **lambda panel UNCHANGED by Channel 2 (still NaN -- the gap persists, now measured).**
**What the spec wanted (Entry 24):** an on-chain HODL-wave / coin-age series (share of supply unmoved > a window) per asset-month — flagged as "the single highest-value addition" but requiring each token's FULL Transfer history.
**What was actually built / measured:**
- **Engine (`phase1_channel2_holding.py`):** a FIFO per-address coin-age engine — replay all `Transfer` logs (each log carries its own `timeStamp`, no extra calls) maintaining per-address acquisition lots; mint=push, burn=FIFO-pop, transfer=FIFO-pop sender + push one time-stamped lot to receiver; at each month-end, HODL share = supply in lots older than a window / circulating (6m and 12m reported). Validated end-to-end on MET (small enough to fetch completely).
- **ADDRESS-CLASS HYGIENE finding (Entry-24 caveat, empirically demonstrated):** on MET's last month, raw HODL-6m = **90.8%** but after screening out the CONTRACT addresses among the top >6m holders (eth_getCode non-empty; 5 of top 40) it COLLAPSES to **1.3%** -- i.e. nearly all apparent "long-held" supply is contract-held (LP/treasury/staking), not EOA conviction. This is decisive: a raw coin-age channel without contract/CEX screening is dominated by non-holder addresses, and free Etherscan labels don't cover CEX EOAs -> a residual bias that itself is a Phase-2 paid-label task.
- **CALL BUDGET (`phase1_channel2_budget_probe.py`), the Phase-2 decision input:** MET (small) = 24,636 transfers, **79 getLogs calls**, full history, ~80s. RAD (mid-size) = **204,428+ transfers, 700+ getLogs calls, DID NOT COMPLETE** (capped, ~12 min). Extrapolation: free-chain EVM population = 793 tokens (Entry 53); even at RAD's mid-size cost 793x700 ~ 555k calls ~ 5.6 free-days, and the high-volume tail (UNI/USDC-class, 100-1000x RAD's transfer count) dominates -> **panel-scale Channel-2 blows the free ~100k getLogs/day cap.**
**Decision made:** Build & validate the engine but DO NOT scale Channel 2 this session and DO NOT wire the single-token prototype into lambda (one asset can't be z-scored anyway). **Per Task C2, the free-cap breach IS the documented Phase-2 (paid) trigger** -- Channel 2 remains the lambda schema's NaN column (Entry 24 unchanged in lambda terms) but is now backed by a working engine + a measured budget, not an open question.
**Rationale:** Spec section 0 forbids silently stalling or shipping a weak proxy; the honest output is "method proven, free budget insufficient at panel scale, here are the numbers."
**Downstream impact:** MET's mid-history token migration (v2 contract) makes its 12m window read 0 (window-length artifact) -- a clean single-deployment token should be chosen for the eventual paid build. Phase 2 needs either a paid archive/indexer or a paid getLogs throughput tier for the high-volume tail, plus a paid address-label feed for CEX-EOA screening.

### Entry 60 — Session 024 close-out: lambda 2,130 -> 2,699 asset-months / 68 -> 90 assets; Tasks D/E time-boxed triage (no free clean builds)
**Date:** 2026-06-30
**Spec section affected:** 3 (lambda assembly — counts only; z-score/standardizability/equal-weight logic untouched), plus Tasks D/E feasibility.
**Asset(s)/period affected:** `03_data/phase1/lambda_panel.csv` re-assembled.
**lambda DELTA (this session):** **2,130 -> 2,699 observed asset-months (+569); 68 -> 90 distinct assets (+22).** Sources: `ch3_delegation` 560 asset-months / 21 net-new governance assets (Entry 57) + XAN Channel-1 9 asset-months / 1 asset (Entry 58). New channel `ch3_delegation` standardizable in 69 months; no change to 2-channel count (354) -- confirming no governance double-count. Panel now spans 2019-12->2026-05 (earlier reach via DMG-era delegation). By class: token 73, coin 9, other 8. The assembler's cosmetic `->` UnicodeEncodeError print was fixed (one char).
**Tasks D & E — TIME-BOXED TRIAGE (the kickoff's instructed treatment for low-yield channels; no free clean builds shipped):**
- **D (22 EVM-non-Etherscan):** ~19 are WRAPPED/native-gas tokens (WCHZ/WEOS/WVLX/wIOTA/OKB/WFLR/WHYPE/WPLS/KHYPE/BBTC/MANTA/MTL/REEF/MEGA/SAROS/A/ATMOS/AMO/WE) whose conviction belongs to the underlying gas coin, NOT the token -> out of token-scope (the Entry-53 logic). Only ~2-3 are genuine DEX/governance tokens (KSP/KlaySwap, BORA — both on KAIA) that might carry a token-level lock/vote; building them needs per-chain KAIA Klaytnscope/Blockscout getLogs verification -> flagged as Phase-2 candidates. Net free clean builds this session: 0.
- **E (92 non-EVM-indexed; Solana 53, Neo 9, Tron 6, Osmosis 4, ...):** free indexers (Solana RPC `getProgramAccounts`, TronGrid, Cosmos LCD, Koios) serve CURRENT state, not historical month-end snapshots — the SAME archive wall as Entry 21, now on non-EVM. So a historical Channel-2 coin-age series (the realistic target) is effectively paid on these chains; Channel-1/3 need per-project Anchor/Realms/CosmWasm reads (gas-coin staking/gov, out of token-scope) with low yield. Flagged for Phase 2. The 284 NO-IDENTITY listings were NOT chased (Entry 56, survivorship bias). Net free clean builds this session: 0.
**Decision made:** Accept the re-assembled panel. Tasks A/B/C delivered the session's lambda gain and the Channel-2 method+budget; D/E are honestly triaged as no-free-clean-build, contributing specific Phase-2 worklists rather than category write-offs.
**Rationale:** Matches the kickoff's two-phase framing (every FREE source this phase; paid = Phase 2) and the project standard (a documented per-bucket reason beats a chased low-yield build).
**Downstream impact:** Full account: `03_data/SESSION024_FREE_BUILD_REPORT.md`. Phase-2 worklist + kickoff: `06_documentation/SESSION024_STATUS_AND_NEXT_SESSION.md`.

### Entry 61 — Session 025: Etherscan API Pro purchased (the Phase-2 data-sourcing decision) — unlocks BSC/Base/Optimism/Linea getLogs + panel-scale Channel-2
**Date:** 2026-06-30
**Spec section affected:** 2.5 (per-asset sources), 3 (λ channels) — a paid data-sourcing decision, the documented Phase-2 trigger from Entries 24/53/59.
**Asset(s)/period affected:** Sourcing capability only; enables the P2-2 (Entry 62) and Channel-2 (Entry 63) builds.
**What the spec wanted:** the two measured paid triggers — (a) getLogs on BSC/Base/Avalanche for the 16 paid-gated Channel-1/3 candidates (Entry 53), and (b) panel-scale getLogs throughput for Channel-2 coin-age, where the free ~100k/day cap binds (Entry 59).
**What was actually done:** Moazzam purchased **Etherscan API Pro — Standard Plan, $199/month, 200,000 calls/day, 10 calls/sec, all chains** (activated 2026-06-30). Key stored in gitignored `04_code/.api_keys.json` under `"etherscan"`. **VERIFIED Pro-grade before any build** (`phase1_p2p2_probe.py` + direct probes): `eth_blockNumber` returns on Ethereum (chainid 1); **`getLogs` returns real log data on BSC (chainid 56), Base (8453), Optimism (10), Linea (59144), Avalanche (43114)** — the free tier returned "Free API access is not supported for this chain" on these. The upgrade is confirmed, not assumed.
**Decision made:** Accept the purchase as the Phase-2 paid-source for λ. NO other paid subscription (no Nansen/Glassnode/CoinMetrics/Alchemy) — the kickoff's standing constraint. Budget is actively tracked per run; builds checkpoint and stop before the 200k/day quota.
**Rationale:** Both paid triggers were measured, not assumed (Entries 53, 59); a single $199/mo Etherscan tier covers both, vs a per-metric data vendor. cmc_id joins and the Entry-26 cross-check bar continue to govern any build done on the Pro key.
**Downstream impact (re-check if this changes):** The 200k/day cap and ~10/s rate are the active budget constraints for every Pro-key build; the high-volume **wall-clock** per token (not just daily quota) turns out to bind hardest (Entries 62 OP, 63 RAD/AAVE/CRV) — see those entries.

### Entry 62 — Session 025 (Task A / P2-2): the 16 paid-gated Channel-1/3 candidates run on the Pro key — 5 BUILT, 1 deferred, 9 rejected/dormant
**Date:** 2026-06-30
**Spec section affected:** 3.3 (governance/delegation), 3.1 (locking), 2.5 (sources).
**Asset(s)/period affected:** the 16 session-022 paid-gated tokens (15 Channel-3 ERC20Votes candidates on BSC/Base/Optimism/Linea + TNC Channel-1 on BSC). Builds folded into `03_data/phase1/channel3_onchain_delegation.csv` via `phase1_channel3_onchain_delegation.py` (P2-2 block appended to TOKENS).
**What the spec wanted:** for each, confirm the mechanism actually fires on-chain (the AKRO/Entry-55 discipline) before building, then build the passers to the same standard as session 024.
**What was actually done / found (mechanism VERIFIED first, `phase1_p2p2_probe.py`):**
- **5 BUILT (net-new `ch3_delegation` primary, DelegateVotesChanged replay):** **AWE** (cmc 4006, Base; 208,687 events; final delegated/circ = **15.25%** — a substantial, real governance-activation signal), and **CHEEL** (23054, BSC), **FORM** (23635, BSC), **LINEA** (27657, Linea), **ZORA** (35931, Base) — all fire with non-zero delegated weight but at **~0% ratio** (governance technically active, almost no supply delegated; included as genuine low-activation rows, consistent with the existing BLAST/BLUR/EIGEN ~0% precedent, z-scored on rank).
- **1 EXCLUDED on degeneracy:** **ALT** (10897, BSC) — 2 DelegateVotesChanged events netting to 0 delegated weight → no ratio (the CYBER/session-024 pattern). Not shipped.
- **1 DEFERRED on throughput:** **OP** (11840, Optimism) — mechanism VERIFIED FIRING (46,974+ events in the first 60 capped calls) but the full DelegateVotesChanged history is pathologically large (the native OP-airdrop self-delegation count); a full-history getLogs replay did not complete in >80 min / 400 MB+ and was killed. A PARTIAL replay would be a wrong delegated-weight stock, so OP is NOT built (same "no partial series" discipline as Channel-2). Commented out in the builder with a note; re-run alone with a block-windowed incremental fetch. A per-token `DELEG_CAP` guard (default 6000 calls) was added so a future giant defers gracefully instead of hanging.
- **8 DORMANT Channel-3 (NOT built):** BAKE (7064), BNX (9891), EDG (5274), ESPORTS (37414), MCT (16946), MDX (8335), PONKE (29150), TKO (9020) — all carry the ERC20Votes ABI but **DelegateVotesChanged has never fired** (0 logs on both the uint256 and uint96 topics over full history). No governance-activation signal exists to measure; not forced.
- **1 REJECT Channel-1 (TNC, cmc 5524, BSC):** its cached verified source declares **`event Locked(address indexed account)` — bare, no amount**, exactly the AKRO/VSL false-positive the kickoff anticipated. With no amount word there is no escrow quantity and nothing to cross-check to a balance (fails the Entry-26 bar). The amount-bearing `Locked(address,uint256)` topic returns 0 logs. Rejected, same lesson as AKRO (Entry 55) / VSL (Entry 58).
**Decision made:** Build the 5 firing net-new delegation tokens; exclude ALT (degenerate), defer OP (throughput), reject TNC (no amount), skip the 8 dormant. P2-2 net λ contribution: the `ch3_delegation` primary set grows **560 asset-months / 21 assets → 627 / 26** (+67 / +5).
**Rationale:** Mechanism-verify-before-build (Entry 55) plus "don't ship a partial or degenerate series" — every verdict is backed by an actual on-chain log query on the Pro key, not ABI presence.
**Downstream impact (re-check if this changes):** OP is the one carried-forward P2-2 item (verified, deferred on volume — not a rejection). The 8 dormant tokens are settled (no signal), not pending. CHEEL/FORM/LINEA/ZORA enter λ at ~0% (low-rank governance activation); AWE is the only economically material P2-2 add. Builder env gate `DELEG_CAP` documents the giant-delegation deferral path.

### Entry 63 — Session 025 (Task B): Channel-2 (coin-age / HODL) BUILT at panel scale — engine denominator FIX + metadata-driven build (197 assets)
**Date:** 2026-07-01
**Spec section affected:** 3.2 (holding-duration channel) — the Entry-24 "single highest-value addition", NaN since inception.
**Asset(s)/period affected:** 197 free-chain EVM tokens → `03_data/phase1/channel2_holding.csv` (3,413 asset-months with a screened value); builders `phase1_channel2_panel.py` (+ `phase1_channel2_sizeprobe.py`, `phase1_channel2_validate.py`), reusing the session-024 FIFO engine.
**What the spec wanted (Entry 24):** an on-chain HODL-wave / coin-age series (share of supply unmoved > a window) per asset-month — needs each token's FULL Transfer history; the free getLogs cap blocked it (Entry 59), now unblocked by the Pro key (Entry 61).
**What was actually built / the two methodology corrections:**
- **DENOMINATOR FIX (decisive):** the session-024 prototype divided the coin-age numerator by **CMC circulating supply**, producing shares **>100%** (RAD raw 148–398%) because CMC circulating EXCLUDES locked/treasury/vested tokens (the Entry-49 pattern) while the numerator counts all on-chain tokens. Corrected to divide by **on-chain supply** (sum of all live FIFO lots at the month-end block) — the supply whose age the channel measures — so the share is a proper fraction in [0,1]. Re-validated on RAD (clean single-deployment governance token; AAVE/CRV were swapped out — their 1M+ transfer histories are the same throughput wall as OP and did not complete): post-fix RAD screened HODL-6m 11–27% (latest 22%), bounded and economically sensible → gate PASSED.
- **ALL-MONTH contract screen:** eth_getCode is time-invariant (an address is a contract in every month), so one classification pass over the union of each month's top >6m holders cleans the WHOLE series (fixing the prototype's last-month-only screen). Raw share (incl. contracts) vs screened (EOA-only) both written; the screened share is the λ input. **CEX custodial EOAs are NOT screened** (no free label feed) → named residual limitation, `cex_screened=False` flag.
- **METADATA-driven sizing (replaced hit-and-trial):** the first cut fetched each token until a per-token call cap, then deferred — wasting ~cap calls per giant just to discover it was too big. Replaced with a pre-pass (`phase1_channel2_sizeprobe.py`): Etherscan Pro `tokenholdercount` = 1 call/token, a monotone proxy for Transfer volume (MET 748 holders/79 calls; RAD 7,785/1,357; XAN 12,963/giant). All 793 sized (`_channel2_sizes.csv`): 113 <=1k holders, 165 <=2k, 215 <=3k, 295 <=5k, 404 <=10k. The builder now processes SMALLEST-FIRST, DEFERS BY METADATA any token > HOLDER_MAX (skipped without fetching), and caches month-end blocks once per chain. Deterministic and budget-predictable.
- **Built:** with HOLDER_MAX=3000, **207 tokens completed** (197 with a screened HODL series; the rest 0-transfer / pre-history-only), 5,064 asset-month rows. Data quality: **median screened HODL-6m = 40.6%**, 80.6% of token-months < 95%, only **2 of 197 assets degenerate** (~100% every month = dead/illiquid). The illiquidity caveat (a non-trading token shows HODL~100% = inactivity, not conviction) is real but token-specific, not systemic; handled by the assembler's cross-sectional z-score (std>0, n>=2 guard drops degenerate all-~100% months). The ~586 tokens > 3,000 holders (incl. major DeFi/governance) were DEFERRED BY METADATA — the documented resumable worklist (a dedicated higher-cap run gives them ch2).
**DATA-INTEGRITY bug found & fixed (the overnight-outage incident):** during an unattended overnight run the machine's network dropped intermittently; the engine's `api()` swallowed the DNS failure into an EMPTY result, and `fetch_capped` treated the empty getLogs range as "0 transfers here" → **silently dropping a block range = a corrupted coin-age series**. Fixed: a panel-local `_robust_getlogs` that RAISES `NetworkError` on connection failure (vs returning empty), so a dropped connection ABORTS+retries the token instead of checkpointing a partial history; `month_block` no longer caches a failed (None) lookup (which would poison every later token for that month); `main()` has a network-failure backoff + circuit-breaker. All 65 possibly-affected overnight checkpoints were DELETED and re-fetched with the robust code; the clean re-run logged **0 network failures** for all 207 tokens. RAD (validated during a stable session) was kept.
**Decision made:** Wire the screened HODL-6m series into λ as channel `ch2_holding` (assembler z-score/equal-weight logic untouched — only a channel input added). Ship the 197-asset panel with the illiquidity caveat documented; do NOT silently apply a liquidity filter (flag it for downstream analysis instead). Defer the >3,000-holder tail as the resumable next-session worklist.
**Rationale:** Numerators from real Transfer events (no guessing); the denominator fix makes the share interpretable; metadata sizing spends the Pro budget deterministically; the network-failure fix guarantees no token is ever checkpointed with a partial history. The honest output is "channel built and validated for the small/mid cross-section; the high-volume tail is measured-and-deferred, not open."
**Downstream impact (re-check if this changes):** `ch2_holding` uses on-chain supply as denominator (NOT CMC circulating — do not "reconcile" the two). The illiquidity caveat means a downstream liquidity screen is advisable before treating small-token ch2 as conviction. The >3,000-holder tokens (incl. the large in-λ governance/staking assets) lack ch2 → that's why 3-channel asset-months are ~0; a dedicated tail run would lift depth. λ counts folded into Entry 64.

### Entry 64 — Session 025 close-out: λ 2,699 → 6,097 asset-months / 90 → 288 assets (Channel-2 panel + P2-2 delegation)
**Date:** 2026-07-01
**Spec section affected:** 3 (λ assembly — counts only; z-score/standardizability/equal-weight logic untouched).
**Asset(s)/period affected:** `03_data/phase1/lambda_panel.csv` re-assembled with `ch2_holding` added and the P2-2 `ch3_delegation` additions.
**λ DELTA (this session):** **2,699 → 6,097 observed asset-months (+3,398); 90 → 288 distinct assets (+198).** Sources: `ch2_holding` 3,413 asset-months / 197 assets (Entry 63) + P2-2 `ch3_delegation` +67 asset-months / +5 assets (Entry 62, AWE/CHEEL/FORM/LINEA/ZORA). Month range now 2016-12 → 2026-05 (older tokens' Transfer histories reach further back). Channel coverage (asset-months): ch2_holding 3,331 single + 937 ch1_staking + 834 ch3_voting + 560 ch3_delegation + 354 (ch1+ch3_voting) + 67 (ch2+ch3_delegation) + 14 (ch2+ch3_voting). ch2_holding is standardizable in 114 monthly cross-sections (the most of any channel). By class: token 128, other 151, coin 9.
**Depth (the kickoff's headline metric):** 2-channel asset-months **354 → 435 (+81)**; but the 2-channel SHARE FELL 13.1% → 7.1% because breadth tripled with single-channel ch2 assets. This is an honest tradeoff: Channel 2 massively WIDENED the panel (mostly new small/mid tokens) but added a 2nd channel to only 4 already-in-λ assets — because the large in-λ governance/staking tokens are >3,000 holders and were metadata-deferred. 3-channel asset-months remain ~0 (no token yet has ch1+ch2+ch3). Lifting depth is exactly what the deferred >3,000-holder tail run would do.
**Decision made:** Accept the re-assembled panel. Channel 2 is no longer the λ NaN column (Entry 24 CLOSED for the <=3,000-holder cross-section, measured-and-deferred for the tail).
**Rationale:** Matches the kickoff (build ch2 for ALL free-chain tokens where Transfer history exists; report breadth + depth). Every number from real events; assembler logic unchanged.
**Downstream impact:** Full account `03_data/SESSION025_PRO_BUILD_REPORT.md`. Budget: sizeprobe 793 calls + build ~15-20k getLogs/getCode + P2-2 delegation — all well under the 200k/day Pro quota; the binding constraint was per-token WALL-CLOCK (full Transfer history), not the daily quota. Resumable worklist: the ~586 tokens > 3,000 holders (`_channel2_sizes.csv` + per-token checkpoints store raw events for `--recompute`). No additional paid subscriptions.

### Entry 65 — Session 026 (Task A): OP on-chain delegation COMPLETED — block-windowed streaming + concurrent pooled-Session fetch resolves the session-025 deferral
**Date:** 2026-07-02
**Spec section affected:** 3.3 (governance) — the one carried-forward P2-2 item (Entry 62).
**Asset(s)/period affected:** OP (cmc 11840, Optimism chain 10, ERC20Votes 0x4200..0042), role=**crosscheck** -> `03_data/phase1/channel3_onchain_delegation.csv` (47 months); builder `phase1_op_delegation.py` (NEW). NOT in lambda.
**What the spec wanted:** complete OP's DelegateVotesChanged replay (verified firing in session 025 but killed at >80 min).
**Root causes + fixes (two, layered):** (1) the session-025 hang was over-large getLogs ranges (block 0->153M) timing out on Optimism -> **block-windowing** (never span a timeout-inducing range) + **streaming replay** (fold each event into a per-delegate running balance, snapshot at month-ends, discard the raw log -> memory bounded by delegate count, not the 11.7M-event volume). (2) the serial resume from 68% then STALLED on an Optimism `ConnectionReset 10054` storm — opening a fresh TCP/TLS connection per call, while hammering the very active recent-blocks region (810k events in the first 2M blocks), made the server drop connections (CPU burned ~4,000 s on reconnect churn). Fixed by reusing the ch2 engine's **pooled keep-alive Session + 8-way concurrency + raise-not-swallow retry** (a genuinely failed call RAISES so no block window is silently skipped): CPU fell to near-idle and the last 32% finished cleanly in ~59 min at ~7.6 calls/s.
**Result:** **11,722,683 DelegateVotesChanged events / 245,439 delegates** (the "46,974" in Entry 62 was only the first 60 capped calls; the true history is ~250x larger). **Delegated/circulating: median 7.98%, range 3.54–13.05%** (final 76.2M OP delegated = 3.54%) — a substantial, REAL governance-activation signal, far above the ~0% low-activation P2-2 tokens.
**Decision made:** role=**crosscheck** per the governance waterfall (Entry 57) — OP already has a Snapshot ch3_voting turnout series, so on-chain delegation is recorded for comparison but the assembler folds ONLY role=='primary' delegation into lambda. Verified: lambda unchanged at 6,021/282, OP n_channels=1 (its lambda membership is via ch3_voting alone).
**Rationale:** mechanism verified (Entry 62); the windowed+streaming+concurrent fetch computes the exact stock series without a partial (wrong) replay or a silent-gap corruption.
**Downstream impact:** the pooled-Session + concurrent + raise-not-swallow template is now the canonical fetch for any pathologically-large or flaky-RPC on-chain replay (ch2 or ch3).

### Entry 66 — Session 026 (Task B): Channel-2 tail BUILT via a validated STREAMING + CONCURRENT engine → first 3-channel lambda assets; address-poisoning contamination caught & fixed
**Date:** 2026-07-02
**Spec section affected:** 3.2 (holding-duration channel); 3 (lambda depth).
**Asset(s)/period affected:** the deferred >3,000-holder tokens that already have ch1/ch3 -> `03_data/phase1/channel2_holding.csv`; new engine `phase1_channel2_stream.py`, panel builder `phase1_channel2_panel.py` extended (WORKLIST env, per-token value cap, contamination exclusion).
**What the spec wanted (session-025 worklist):** add ch2 to the large in-lambda governance/staking tokens (the ch1+ch3 set), creating the panel's first 3-channel assets — the depth the session-025 breadth expansion lacked.
**Efficiency discipline (user-steered):** classified each candidate FIRST by which channels it already has, and built ch2 ONLY for the 3-channel creators (tokens with ch1 AND ch3). An initial interleaved run hit ORBS (9k holders but a hidden giant, >2M transfers — holder_count under-counts transfer volume) for zero 3-channel value -> restricted to 3-channel creators, smallest-first, with a memory heartbeat to catch hidden giants.
**The engine (the giant-token unlock):** the session-025 panel engine loads a token's ENTIRE Transfer history into RAM before replaying — fine to ~2M transfers but OOMs on the 100k+-holder giants (AAVE/CRV/SUSHI/GMX at 4–60M transfers) and is serial. `phase1_channel2_stream.py` fixes both, **validated BYTE-IDENTICAL to the panel engine before use**: (1) STREAMING FIFO replay (fold events into per-address lots as they arrive, snapshot at month-ends, discard raw events; empty-deque pruning bounds churn/dust giants — CVX's 2.8M transfers held in ~96k lots, not 2.8M events); (2) CONCURRENT windowed fetch (8 workers, global ~8 calls/s token bucket, block-ordered batches -> monotonic stream -> identical to batch replay; pooled thread-local Session eliminates the per-call TLS-handshake CPU that otherwise burned ~6 cores). Validation gates (0 diffs): `--validate 2943` (streaming replay == panel._replay on RPL, incl. with pruning + value cap) and `--checkfetch 7228` (full concurrent pipeline re-fetch of DDX == its serial checkpoint, transfers identical).
**Built (10 tokens):** RPL, DDX (2-channel), FRAX, CVX, YFI, CRV, 1INCH, SUSHI, AAVE, GMX. Screened HODL-6m medians 10.7–54.5% — all economically bounded (governance/liquid tokens 10–17% match the RAD precedent; YFI/SUSHI ~53% higher but legitimate for their long-term holder bases; none degenerate).
**DATA-INTEGRITY (address-poisoning phantom lots) — a two-layer fix (B2 finding).** A full-panel scan (reconstructed on-chain supply vs circulating) caught 11 tokens contaminated by fake huge-value Transfer logs that, replayed through FIFO, become phantom lots dominating the coin-age denominator (AAVE read up to 1.16e60 tokens vs real 16M; 10 small/dead tokens at 50–42,000x circ). A universal threshold cannot separate spam from legit high-supply meme tokens, and a per-event cap alone misses accumulated sub-cap spam, so the fix is two layers: (1) PER-EVENT value cap (skip Transfers > VAL_CAP_MULT=100 x max circulating — a real transfer cannot exceed supply; 100x spares heavily-locked tokens whose on-chain supply exceeds CMC circulating, the Entry-49 pattern); (2) PER-MONTH exclusion (null months where on-chain supply > CONTAM_MULT=100 x circulating — 100x not 50x so legit early heavy-lock months like CRV's launch month, on-chain 1.3B/circ 26M/total 3B, are RETAINED). Both re-validated byte-identical on RPL. 10 event-storing tokens fixed by `--recompute` (no re-fetch); AAVE re-fetched clean. Result: 0 residual contaminated rows; 6 spam-only dead tokens correctly dropped from lambda.
**lambda DELTA:** 6,097 -> 6,021 asset-months / 288 -> 282 assets (the COUNT dips because the contamination fix nulled 6 spam-only dead tokens whose sole channel it was — this session's value is DEPTH + INTEGRITY, not breadth). n_channels 1/2/3 = 5,356 / 333 / **332** (was 5,662 / 435 / **0**). **First 3-channel assets (9):** CVX(56), FRAX(52), 1INCH(41), AAVE(38, recent spam-months excluded), SUSHI(35), GMX(32), YFI(29), RPL(28), CRV(21) = **332 three-channel asset-months**, all ch1_staking+ch2_holding+ch3_voting. **2+ channel share 7.1% -> 11.0%.**
**Decision made:** wire the streamed screened HODL-6m into lambda (assembler untouched — channel input only); the streaming engine is the canonical path for the high-volume tail; the value cap + contamination exclusion make the coin-age channel spam-robust.
**Rationale:** every number from real Transfer events; the streaming engine is proven byte-identical to the validated engine, so the giants are built to the same standard as the small/mid cross-section; depth is created exactly where the session-025 report predicted (the ch1+ch3 tokens).
**Downstream impact (re-check if this changes):** `phase1_channel2_stream.py` makes the entire remaining >3,000-holder tail tractable. Streamed checkpoints store rows but not raw events (`streamed:True`) -> `--recompute` unavailable for them (rows are final). AAVE's spam-contaminated 2024-08->2026-05 ch2 window is EXCLUDED (the one coverage gap); a per-token totalSupply value cap (vs the circ-multiple heuristic) would recover it — noted refinement.

### Entry 67 — Session 026 close-out: lambda 6,097 → 6,021 asset-months / 288 → 282 assets; first 3-channel depth (0 → 332)
**Date:** 2026-07-02
**Spec section affected:** 3 (lambda assembly — counts/depth only; z-score/equal-weight logic untouched).
**lambda DELTA (this session):** 6,097 -> 6,021 observed asset-months (-76); 288 -> 282 assets (-6) — the COUNT dips because the address-poisoning contamination fix (Entry 66) nulled the ch2 of 6 spam-only dead tokens whose sole channel it was; the contribution is DEPTH + INTEGRITY, not breadth. n_channels 1/2/3 = 5,356 / 333 / **332** (was 5,662 / 435 / **0**). **3-channel asset-months 0 -> 332** across **9 assets** (CVX/FRAX/1INCH/AAVE/SUSHI/GMX/YFI/RPL/CRV, all ch1_staking+ch2_holding+ch3_voting) — the panel's FIRST 3-channel observations, exactly the tokens the session-025 report predicted the >3,000-holder tail would lift. **2+ channel share 7.1% -> 11.0%.**
**Budget:** Channel-2 tail + AAVE re-fetches ~200k getLogs via the streaming+concurrent engine (~8 calls/s under the 10/s Pro ceiling, DAILY_CAP-gated, crossing the 00:00 UTC quota reset); OP delegation ~26k getLogs this session (full history 11.7M events). The binding constraint remained per-token wall-clock, now cut ~6x by concurrency; the streaming engine removed the memory wall (giants held in bounded lot state, not full event lists). No additional paid subscriptions.
**Decision made:** accept the re-assembled panel. Channel-2 depth built for all 9 three-channel creators + DDX; OP delegation completed as a cross-check; the value-cap + contamination exclusion make coin-age spam-robust.
**Rationale:** every number from real on-chain events; assembler z-score/equal-weight logic untouched (only channel inputs added); the governance waterfall (OP crosscheck) prevents double-counting.
**Downstream impact:** Full account `03_data/SESSION026_TAIL_BUILD_REPORT.md`; session log `06_documentation/ai_conversations/session_026_channel2_tail_and_op.md`. Resumable worklist for the next Cowork data-collection plan: (a) the ~506 >3,000-holder 2-channel-only / breadth tokens; (b) the 62 tail tokens that already have ch1/ch3 (would add depth); (c) a per-token totalSupply value cap to RECOVER AAVE's spam-excluded 2024-08->2026-05 ch2 window. All buildable via `phase1_channel2_stream.py`.

### Entry 68 — Session 027 (Task A): TVL denominator expansion — 23 new verified DeFiLlama slugs (incl. all four missing 3-channel tokens) + reviewed other-class adds + chain-level TVL for L2 governance tokens
**Date:** 2026-07-03
**Spec section affected:** Phase 2 valuation-multiple denominator (NV/TVL; Entry 30/40 semantics UNCHANGED — TVL is a STOCK denominator, not a PQ substitute, not a lambda channel).
**Asset(s)/period affected:** `03_data/phase2/tvl_panel.csv` rebuilt 4,999 -> 6,620 asset-months / 99 -> 130 distinct tokens (2018-09 -> 2026-05); `asset_onchain_identity.csv` +23 dl_slug entries; builder `phase2_build_tvl_panel.py` extended (OTHER_ADDS, CHAIN_LEVEL).
**What was needed:** the five 3-channel assets (CRV/YFI/FRAX/GMX/RPL) had full lambda but no TVL -> could not enter the NV/TVL regression; 76 more 1-2-channel lambda tokens likewise. Four of the five had NO dl_slug.
**Slug discovery method + the PARENT-protocol finding:** DeFiLlama /protocols cmcId lookup found ZERO of the four (and zero of the 207 no-slug non-coin lambda assets) — every cmcId-matchable asset was already harvested in earlier sessions; DL's cmcId field covers only 1,709/7,770 protocols. Fallback = exact symbol+name match (the session-019 LOOSE_ADDS precedent), individually verified. The decisive pattern: all four priority tokens live under DL PARENT protocols with per-version children (curve-dex/llamalend/crvusd under parent curve-finance, etc.). Since the token governs the WHOLE family, the parent slug is the correct denominator; verified `/protocol/{parent}` serves the aggregated tvl[] series with correct launch dates (curve-finance 2020-02, yearn 2020-02, frax-finance 2020-12, gmx 2021-09). **CRV -> curve-finance, YFI -> yearn, FRAX -> frax-finance, GMX -> gmx.**
**19 more name-verified slugs (same bar):** AERO->aerodrome, ALCX->alchemix, BAL->balancer, BLUR->blur, BNT->bancor, BONE->shibaswap, CAKE->pancakeswap, COMP->compound-finance, ENA->ethena, EUL->euler, FLUID->fluid, LQTY->liquity, ONDO->ondo-finance, STG->stargate-finance, T->threshold-network, UNI(7083 ONLY — cmc 4113 \"UNI COIN\" is a symbol collision, NOT Uniswap)->uniswap, VVS->vvs-finance, XVS->venus (parent slug; \"venus-finance\" 400s), and RPL already had rocket-pool.
**Builder extensions (two, both cmc_id-keyed):** (1) OTHER_ADDS — the token-class filter excluded asset_class=='other' lambda assets; 5 reviewed adds: RPL/rocket-pool, SSV/ssv-network, BLUR/blur, RAIN/rain, MV/gensokishi. (2) CHAIN_LEVEL — canonical L2 governance tokens whose DL protocol entry is a Foundation/treasury or an empty parent get CHAIN DeFi TVL via /v2/historicalChainTvl/{chain}, recorded as dl_slug='chain:{name}' so downstream can distinguish: ARB->Arbitrum, OP->'OP Mainnet' (DL renamed; 'Optimism' is a dead $0 alias), MNT->Mantle, APE->ApeChain, BLAST->Blast. COINS deliberately excluded from TVL (they use NVT per the framework).
**Rejected (logged so they are not re-tried):** ZORA (parent 'zora' 400s; only child with TVL is a canonical bridge — bridged custody is not protocol TVL for the token claim; identity slug REVERTED); GBYTE (oswap-amm is a third-party DEX on Obyte, not GBYTE's protocol); PENGU (not Abstract's fee token — no defensible TVL); CYBER (Cyber chain TVL ~$0); NEST (two conflicting DL parents — ambiguous); POWER cmc 39042 (DL 'm0' symbol matches but identity unconfirmable); CVP (session-019 rejection re-affirmed: DL cmcId 7368 mismatch); WLFI (name-exact but no TVL series); MNT/OP Foundation slugs NOT fetched as protocol TVL (treasury holdings != protocol TVL). Genuinely-no-TVL protocols left NaN: ENS, GTC, COW, FORTH, ZRX, CHEEL, APE-protocol (apecoin), CYBER-protocol (cyberconnect).
**Result / plausibility gate (A5):** all five priority tokens PASS (56-76 months, no post-launch near-zeros, USD magnitudes sane — CRV peak $23.1B Jan-2022, YFI peak $5.9B, RPL last $1.1B). Lambda assets with TVL 49 -> 80 (of 282); lambda asset-months with same-month TVL 2,103 of 6,021; **3-channel asset-months with TVL: 331 of 332** (the one gap = SUSHI 2020-08, its launch month, before DL's sushiswap series begins — genuine early-launch, per the A5 rule). 0 fetch failures in the final rebuild.
**Decision made:** ship the expanded panel; chain-level rows carry the 'chain:' prefix so any downstream analysis can include/exclude them explicitly; parent-slug aggregation is the canonical treatment for multi-version protocols.
**Rationale:** every slug verified name+series before writing (cmc_id joins only); the parent-vs-child choice matches the token's whole-protocol governance claim; treasury/bridge/foundation TVL explicitly kept OUT of the denominator.
**Downstream impact:** NV/TVL is now computable for all 9 three-channel assets (SUSHI missing only its launch month). The ~140 remaining lambda-no-TVL assets are mostly Snapshot-governance/dead/small tokens with no DL protocol entry — a name-match pass found no further defensible hits; do NOT loosen the match bar to chase them.

### Entry 69 — Session 027 (Task B): Channel-2 tail COMPLETE for all 43 ch1-or-ch3 lambda tokens <=500k holders — every one now multi-channel; 2+ channel share 11.0% -> 24.4%
**Date:** 2026-07-04
**Spec section affected:** 3.2 (holding-duration channel); 3 (lambda depth).
**Asset(s)/period affected:** the 43 lambda assets with ch1 OR ch3_voting but NO ch2 and holder_count <= 500k (from `universe_coverage_status.csv`), built smallest-first into `03_data/phase1/channel2_holding.csv` via the validated session-026 streaming engine (`phase1_channel2_stream.py`, unchanged — no code edits, thresholds untouched).
**What was built:** ALL 43 COMPLETED, zero network aborts, zero errors: NFTX HAKKA IQ BZRX COW MC SSV OHM KP3R ORBS RGT SYN PNT STRK XAN LQTY ALCX PERP HFT TRU FARM CAKE GNS(Polygon) LINA API3 MNT BADGER BNT STG BAL REN ARB LDO ENS PENDLE GTC ENA LRC GRT APE ZRX COMP UNI. 60,100,476 Transfer events replayed; ch2 panel 217 -> 260 tokens / 5,663 -> 7,823 rows. Hidden giants absorbed in bounded memory (holder_count under-predicts transfer volume, the ORBS lesson): UNI 8.3M transfers, APE 5.9M, BNT 5.7M (2017-era history), GNS 3.5M, ENA/PENDLE 3.3M each.
**Budget (two quota days, both compliant):** day 1 (2026-07-03 UTC) 141,005 getLogs — the engine cap-stopped after APE at DAILY_CAP=140k (in-process cap set BELOW the 180k stop-rule so a mid-flight giant cannot overshoot past it; APE finished at 141,005, day total ~141.1k, 59k headroom); day 2 (2026-07-04 UTC) 41,871 for ZRX/COMP/UNI after the 00:00 UTC reset. Total 182,876. The per-token checkpoint made the cap-stop a clean resume, exactly as designed.
**B2 integrity scan (full 43):** reconstructed on-chain supply vs circulating — **0 months above the 100x contamination threshold**; worst ratio 31x (HAKKA), inside the legitimate Entry-49 heavy-lock band; 0 months nulled. The two-layer guard (VAL_CAP_MULT / CONTAM_MULT = 100, Entry 66) was NOT modified.
**B4 sanity (>50k-holder tokens):** screened HODL-6m medians all economically bounded — REN 42.5%, LRC 44.0%, APE 47.9%, ZRX 51.3%, UNI 50.9%, GRT 37.2%, LDO 32.0%, ENA 32.7%, ENS 13.4%, ARB 22.1%, PENDLE 25.5%, GTC 24.0%, COMP 40.7%, BAL 19.6% — none degenerate. **XAN flag explained, not excluded:** median 0.0% is an AGE artifact (token launched mid-2025; no lot CAN be >6m old before 2026-03; from 2026-03 screened HODL is a real 74-77%, coherent with its NON-CUSTODIAL XanV1 lock — locked tokens never leave holders wallets, Entry 58 — so they age in place; note ch1 and ch2 therefore partially measure the same locked stock for XAN, inherent to the lambda design, same as staked CVX/FRAX aging in place).
**lambda DELTA:** **6,021 -> 7,051 observed asset-months (+1,030); assets unchanged at 282** (all 43 were already lambda members — this session is DEPTH, the +1,030 months are where ch2 extends beyond each token's ch1/ch3 window). n_channels 1/2/3 = **5,331 / 1,388 / 332** (was 5,356 / 333 / 332): 2-channel asset-months +1,055. **2+ channel share 11.0% -> 24.4%.** 3-channel unchanged (none of the 43 had BOTH ch1 and ch3 — confirmed, the priority list was ch1-OR-ch3 by construction). ch2_holding standardizable in 114 monthly cross-sections, the widest of any channel.
**Decision made:** accept all 43 series into lambda (assembler z-score/equal-weight logic untouched — channel inputs only). HEX not attempted (permanent deferral, Entry 66).
**Rationale:** the streaming engine was validated byte-identical in session 026; every series from real Transfer events; the guard thresholds proven on the 026 build were left alone; budget rules observed with headroom on both quota days.
**Downstream impact:** the remaining ch2-less lambda assets are now ONLY: coins (9, ch2 requires non-EVM archive indexers — the Entry-21 wall), non-free-chain tokens, and the ~500 >3k-holder tokens that are NOT lambda members (breadth, not depth — lower priority). The 43 new 2-channel tokens all have TVL-or-slug coverage checked in Entry 68; NV/TVL + lambda regressions can now run on a 1,388-month 2-channel cross-section.

### Entry 70 — Session 027 close-out: lambda 6,021 -> 7,051 asset-months / 282 assets; TVL panel 4,999 -> 6,620 asset-months / 99 -> 130 tokens; NV/TVL now computable for all nine 3-channel assets
**Date:** 2026-07-04
**Spec section affected:** 3 (lambda assembly — counts/depth only; z-score/equal-weight logic untouched) + Phase-2 TVL denominator.
**Session totals:** Task A (Entry 68): TVL +1,621 asset-months / +31 tokens (23 new verified slugs incl. the four missing 3-channel tokens via DL PARENT protocols, 5 reviewed other-class adds, 5 chain-level L2 series); lambda assets with TVL 49 -> 80; 3-channel asset-months with TVL 331/332 (gap = SUSHI launch month). Task B (Entry 69): all 43 ch2-tail tokens built (+1,030 lambda asset-months, 2-channel 333 -> 1,388, 2+ share 11.0% -> 24.4%), B2 clean, 182,876 getLogs across two compliant quota days.
**Decision made:** accept both panels. Depth AND denominator coverage were this session's product: the 2-channel cross-section is now 4.2x larger and the 3-channel regression set is TVL-complete.
**Rationale:** all numbers from live sources (DeFiLlama keyless; Etherscan Pro under quota with headroom); every join cmc_id-only; both engines unchanged from their validated forms.
**Downstream impact / next priorities (session 028+):** (a) coin staking ch1 for AVAX/BNB/NEAR/INJ/SUI/APT etc. (non-EVM, separate research effort — the deferred scope note in the kickoff); (b) the ~500 >3k-holder non-lambda breadth tokens (ch2 single-channel adds); (c) AAVE spam-excluded 2024-08 -> 2026-05 ch2 window recovery via a per-token totalSupply value cap (Entry 66 refinement, still open); (d) PQ/NVT_GL expansion (still deferred); (e) the ~140 lambda assets with neither TVL nor a defensible DL protocol (mostly Snapshot-governance/dead tokens) stay TVL-NaN — do not loosen the name-match bar.

### Entry 71 — Session 028 (Task A, EVM chains): coin Channel-1 BUILT for BNB, S, GLMR, MOVR, XDC via Etherscan Pro V2 + official archive RPCs; BERA documented gap (consensus-side staking invisible to EL logs)
**Date:** 2026-07-04
**Spec section affected:** 3.1 (staking/locking ratio, coins); Entry-26 cross-check bar applied to coins (reconstructed series must reproduce the chain's own on-chain staked total at ~0% drift).
**Asset(s)/period affected:** BNB (cmc 1839) 2024-07→2026-05 (23 mo); S/Sonic (32684) 2025-01→2026-05 (17 mo); GLMR (6836) 2022-01→2026-04 (52 mo); MOVR (9285) 2021-09→2026-05 (57 mo); XDC (2634) 2020-06→2026-05 (72 mo); BERA (24647) NOT built. New builder `phase1_channel1_pos_coins_evm.py` → `03_data/phase1/channel1_pos_coins_evm.csv` (picked up by the channel1_*.csv glob). Raw event/state caches under `03_data/raw/phase1_onchain/pos_coins_evm/` (stage scripts `_s028_*_fetch.py`; shared helpers `_s028_evm.py`).
**What was found and built (all response-body verified live this session):**
- **BNB — BUILT, replay drift +0.000%.** BSC StakeHub `0x...2002` (chainid 56) has a verified ABI; events fire. TWO kickoff premises corrected live: (1) the event data order is `(shares, bnbAmount)` — bnbAmount is the SECOND data word for both Delegated and Undelegated, not the first; (2) the correct accounting is `cum(Delegated.bnbAmount) − cum(Undelegated.bnbAmount) + cum(RewardDistributed.reward)` — rewards accrue into the pools daily without Delegated events, and `MigrateSuccess` (BC-fusion migration, 2,070 events 2024-04-18→2024-07-14) must NOT be added because migration also emits Delegated (adding it → +80% drift; adding rewards → EXACT match). Cross-check: replay head = 25,717,017 BNB vs live sum(`totalPooledBNB()`) over all 53 validator StakeCredit contracts = same figure to the integer (0.000%; re-run at build time +0.0005%, minutes of drift). Redelegated is pool-neutral; zero ValidatorSlashed events. WINDOW: series starts 2024-07 (first month-end after BC-fusion completed 2024-07-14); 2017→2024-06 staking lived on the retired Beacon Chain and is NOT reconstructable from BSC logs — documented gap, not interpolated. 106k events total, one quota-trivial fetch.
- **S (Sonic) — BUILT, replay drift ±0.0000% at every probed block.** SFC `0xFC00FACE...0000` (chainid 146) is a proxy; implementation ABI verified via the EIP-1967 slot. KICKOFF PREMISE CORRECTED: the naive `Delegated − Undelegated + RestakedRewards` replay drifts +0.86% AND GROWING — block-bisection (down to block 60,010,966) proved `restakeRewards()` emits BOTH `Delegated` AND `RestakedRewards` for the same amount (live totalStake moved by the amount ONCE). Correct replay = `cum(Delegated) − cum(Undelegated)` alone: matches archive `totalStake()` at six blocks across the full history (2M→75M) at ±0.0000% each, and the live head exactly. Metric = SFC totalStake (includes deactivated validators' still-locked stake; ~1.2% above totalActiveStake) — flagged. 246k events.
- **GLMR / MOVR — BUILT via the staking pallet's own aggregate (state reads, not reconstruction).** The ParachainStaking precompile `0x...0800` emits NO EVM logs (0 in 50k blocks on both chains) and exposes NO aggregate getter (candidateCount/round answer; totalStake() etc. do not exist) — AND Etherscan's proxy `eth_call` IGNORES the historical block tag on every chain tested (round() identical at all tags), killing the kickoff's A2d fallback as written. RESOLUTION: the OFFICIAL public RPCs (rpc.api.moonbeam.network / rpc.api.moonriver.moonbeam.network) are full archives and answer Substrate JSON-RPC, so the series is `state_getStorage(twox128("ParachainStaking")+twox128("Total"), chain_getBlockHash(month_end_block))` — the chain's own total staked (collator bonds + ALL delegations incl. bottom), one call per month, keyless. Decode cross-check: pallet Total vs eth_call sum(getCandidateTotalCounted over selectedCandidates) = 1.0537 (GLMR) / 1.0153 (MOVR) — exactly the expected superset relation (counted excludes bottom delegations + non-selected candidates). Month-end blocks resolved once via Etherscan getblocknobytime (chainids 1284/1285).
- **XDC — BUILT via Etherscan Pro `balancehistory` (a Pro endpoint, live-confirmed on chainid 50).** XDCValidator `0x...0088` holds masternode stake as NATIVE XDC. Series = the contract's native balance at each month-end block. THREE-WAY cross-check ties out exactly: live Σ getCandidateCap (550 candidates, 265 nonzero) 2.650B ≤ event replay (Propose+Vote−Unvote−Withdraw) 2.668B (+18.0M resigned-but-unwithdrawn, still locked in the 30-day delay) ≤ live balance 2.701B (+32,625,000 XDC of genesis/eventless stake predating the event stream — the replay tracks balancehistory at this CONSTANT offset at every probed block from 40M on, 0.000% co-movement). FLAG: the balance series includes the pending-withdrawal and genesis components (~1.9% above active caps today) — kept with the flag, the RPL/xSUSHI shared-vault standard.
- **BERA — NOT BUILT (documented gap).** BeaconDeposit `0x4242...4242` (chainid 80094, verified ABI) logs deposits only; withdrawals are consensus-side balance credits with NO EVM logs (ETH2 model). Cumulative deposits = 382.6M BERA — far ABOVE circulating supply (~120M), proving heavy withdraw/redeposit cycling that EL logs cannot net out. No free historical validator-balance API found (routescan 404, berascan consensus-less, hub.berachain.com API is PoL/BGT-side). Gap requires a Berachain CL (beacon-kit) archive API — none public today.
**Decision made:** Accept BNB/S/GLMR/MOVR/XDC into λ Channel 1 (5 of the 6 kickoff EVM chains); BERA logged as a gap. Every accepted series passed the Entry-26 bar at ~0% (BNB, S exact; GLMR/MOVR/XDC are state reads of the chain's own figures with decode/identity cross-checks).
**Rationale:** spec §0 verify-live discipline caught three kickoff-premise errors (StakeHub data order, StakeHub reward/migrate accounting, Sonic RestakedRewards double-emission) that would each have shipped a wrong series; the corrections are event-bisection-proven, not inferred.
**Downstream impact:** the sub-channel remains ch1_staking (same z-score cross-section). BNB pre-2024-07 and BERA are the two documented gaps of this entry. The `_s028_evm.py` helper (keccak topics via pycryptodome, capped getLogs walker) and the archive-RPC pallet-storage pattern generalize to other parachains (e.g. future ASTR) — reuse before building new machinery.

### Entry 72 — Session 028 (Task A2/A7): DOT/KSM still key-gated (deferred, no signup possible headless); CELO BUILT 2020-07→2026-05 via Forno archive eth_call getTotalLockedGold() — closes the Entry-46 gap for $0
**Date:** 2026-07-04
**Spec section affected:** 3.1 (coins); Entry-46 (CELO documented gap, now closed); Entry-44 (DOT/KSM gate, unchanged).
**Asset(s)/period affected:** CELO (cmc 5567) 2020-07→2026-05, 70 asset-months, BUILT into `channel1_pos_coins_evm.csv`; DOT (6636)/KSM (5034) not built.
**What was found (live):**
- **DOT/KSM — deferred.** No "subscan" key in `.api_keys.json`; the pro.subscan.io free-signup verification-code failure (kickoff note) stands. Per Entry 44 the build is otherwise ready (era_stat endpoint, paginate, cross-check). MOAZZAM ACTION: retry the free signup at pro.subscan.io, drop the key into `04_code/.api_keys.json` under `"subscan"`, and DOT/KSM become a short extension of `phase1_channel1_pos_coins_bucket2.py`. No Pro purchase.
- **CELO — the kickoff's balancehistory route WORKS but only post-migration; the better route is Forno.** Etherscan Pro `balancehistory` on chainid 42220 answers ONLY for blocks ≥ ~31.06M (the 2025-03-26 L2 migration boundary; every pre-migration block returns NOTOK) and returns the RAW contract balance (includes pending withdrawals; live balance 86.0M vs getTotalLockedGold 78.1M = +9.2%, too dirty for the Entry-26 bar). BUT the official Forno RPC (forno.celo.org, keyless; mirrored by celo.drpc.org) serves the FULL archive INCLUDING pre-migration L1 state, so `eth_call LockedGold.getTotalLockedGold()` — the exact clean number Entry 46 identified — is readable at every historical month-end: block 10M (2021) → 316.6M, block 20M → 307.4M, block 32M → 151.0M, latest → 78.1M (Entry 46 measured 82.43M on 2026-06-26; consistent declining trend). Series built from the chain's own aggregate getter; month-end blocks via Etherscan getblocknobytime (works across the migration boundary).
**Decision made:** CELO accepted into λ Channel 1 (state read of the chain's own getter; excludes pending withdrawals — cleaner than the balance-based alternative). DOT/KSM logged as deferred with the exact Moazzam action.
**Rationale:** Entry 46's conclusion ("only fix is a paid balance-history endpoint or archive eth_call node") was half right — the archive eth_call node turned out to be Celo's own free public endpoint, which nobody had probed for PRE-migration state before. Flag-don't-guess preserved: early months where circulating supply was tiny show locking_ratio>1 (max 272% in 2020-08); kept un-capped and flagged (SOL/AERO precedent).
**Downstream impact:** Entry 46's gap classification is superseded by this entry. If Forno ever prunes pre-migration state, the raw month-end values are cached in `03_data/raw/phase1_onchain/pos_coins_evm/celo_lockedgold_history.json`.

### Entry 73 — Session 028 (Task A8-A10): AVAX BUILT keyless via Ava Labs' official Metrics API (resolves the Entry-42/47 pricing ambiguity: it is FREE, no key at all); NEAR and Cosmos (ATOM/INJ/SEI/KAVA) remain gaps with their gates re-verified
**Date:** 2026-07-04
**Spec section affected:** 3.1 (coins); Entry-42/47 gate map updates.
**Asset(s)/period affected:** AVAX (cmc 5805) 2020-11→2026-05, 67 asset-months, BUILT; ATOM/INJ/SEI/KAVA/NEAR not built.
**What was found (live, response-body verified):**
- **AVAX — BUILT.** `GET https://metrics.avax.network/v2/networks/mainnet/metrics/validatorWeight` (and `delegatorWeight`) answers with NO key, NO signup: daily values in nAVAX back to network genesis (2,112 rows to 2020-09), paginated via nextPageToken. The kickoff's endpoint guesses (glacier-api .../chains/mainnet/metrics/staking; /v2/network/staking/historic) both 404 — the working shape is `/v2/networks/mainnet/metrics/{metric}`. SEMANTICS VERIFIED against the chain itself: P-Chain `platform.getTotalStake` (live, keyless) = 199.87M AVAX ≈ validatorWeight+delegatorWeight (196.7M at yesterday's snapshot; stake currently moves ~2M/day) and NOT validatorWeight alone (159.9M) — i.e. the weights are ADDITIVE and total staked = validatorWeight + delegatorWeight. Month-end sample of the daily series; cross-check drift −1.6% explained entirely by the snapshot-vs-live timing (gate set at 5%). FLAG: early months show staking_ratio≫1 vs CMC circulating (2020-09: 212M staked vs ~18M circulating — genesis staking of vesting-locked tokens CMC excludes); kept un-capped and flagged, the SOL/AERO precedent. This RESOLVES Entry-42/47's "AvaCloud pricing ambiguous, needs signup-flow check": the network staking metrics require no account whatsoever.
- **NEAR — still a gap.** NearBlocks: `/v1/stats` and `/v1/validators` confirmed current-state-only (totalStake present, no history); `api3.nearblocks.io/v1/charts` DOES serve 2,174 days of daily history back to 2020-07 but its field set (price/supply/txns/accounts/gas) contains NO staking figure. Pikespeak remains key-gated, pricing undisclosed. Gate unchanged from Entry 47.
- **Cosmos (ATOM/INJ/SEI/KAVA) — still gaps.** StakingRewards GraphQL (`api.stakingrewards.com/public/query`) → HTTP 401 "you should be authenticated" with no anonymous path (their key requires a commercial signup; not self-serve-free-confirmed). Numia (`data.numia.xyz`) → HTTP 401 on every path (key required; docs route through BigQuery/Google-account territory, outside a headless session). Mintscan stays contact-sales (Entry 47). No signup attempted per the session rules.
**Decision made:** AVAX accepted into λ Channel 1 (official first-party historical series, same source-of-record treatment as ADA/Koios and XTZ/TzKT in Entry 41, PLUS a live P-Chain cross-check those never had). NEAR/Cosmos gates re-verified and left open; no purchase, no signup.
**Rationale:** the Metrics API is Ava Labs' own (it powers the official explorer graphs — Entry 42's strongest-type source), now response-body verified keyless with semantics anchored to the P-Chain's own getter.
**Downstream impact:** AVAX raw daily weights cached (`avax_validatorWeight.json` / `avax_delegatorWeight.json`). If metrics.avax.network ever gates, the cache preserves 2020-09→2026-07. NEAR/Cosmos remain the two structural non-EVM holdouts of the 49-coin target list, joining HBAR/SUI (engineering, Entry 45), ALGO (structural, Entry 42), EOS/ICP/APT (no source, Entry 47).

### Entry 74 — Session 028 (Task B): AAVE ch2 spam window RECOVERED — the real poisoning vector was fake-value SELF-transfers; fix = engine-wide self-transfer skip (accounting identity) + per-token totalSupply value cap; all 22 nulled months restored, AAVE now 3-channel through 2026-05
**Date:** 2026-07-04
**Spec section affected:** 3 (Channel 2 coin-age engine); Entry 66 (the AAVE exclusion + its per-token-totalSupply refinement note, now executed); Entry 63 (denominator conventions unchanged).
**Asset(s)/period affected:** AAVE (cmc 7278) ch2, all 67 months 2020-11→2026-05; engines `phase1_channel2_stream.py` / `_panel.py` / `_holding.py` (mirrored fix); no other token's shipped values change.
**What was found:** the kickoff's premise (phantom lots only pollute the DENOMINATOR; swap in real totalSupply and recompute) was mechanically incomplete — phantom lots sit at EOA-class addresses and AGE past 6m, so they poison the NUMERATOR too (the first rebuild with only a tighter cap recovered the months but showed a fake HODL jump 17.8%→48.9% at exactly 2025-01 = the 2024-07 spam wave crossing the 6-month age line, and reconstructed supply still climbed 16M→62M). Root cause isolated by fetching the largest transfers in the sharpest jump month (2024-07): address `0x3d16ee6d46edb674e728b5923e2ecac4092f5920` (live AAVE balance: **0.0**) emits **Transfer events with from == to** on the REAL AAVE contract carrying fabricated values — max-uint256 (= Entry 66's 1.16e60 reading exactly), 8.0e16, 1.0e11, and sub-cap values like a fake 10,000,000 that pass ANY value cap. The FIFO engines replayed self-transfers as pop-then-append: the pop under-fills (no real lots) while the append credits the full fake value → phantom supply at any cap. ALSO corrected: the kickoff's AAVE token address (`…DDaE8`) was wrong — the identity map's `0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9` is canonical (caught because tokensupply returned 0).
**The fix (two layers, in priority order):**
1. **Self-transfer skip** (`if frm == to: skip`) in all three engine variants. This is an ACCOUNTING IDENTITY — a self-transfer never changes any balance — not a threshold: processing one as pop+append can only (a) mint phantom supply when the value exceeds the address's live lots, and (b) wrongly refresh a real holder's lot age. Applies engine-wide going forward.
2. **`PER_TOKEN_VAL_CAP = {7278: 16_000_000}`** in the stream engine (Entry 66's refinement as written): an ABSOLUTE per-event cap at the token's constant on-chain totalSupply (verified live: eth_call totalSupply() == 16,000,000.0 exactly). Defense-in-depth for AAVE; the global VAL_CAP_MULT / CONTAM_MULT thresholds are UNTOUCHED, per the kickoff rule.
**Verification (all passed):**
- Full re-fetch + replay (5,564,724 transfers, 16.6k getLogs): reconstructed on-chain supply now 16.00M→17.97M across all 67 months (real totalSupply 16.0M constant; the residual ≤+12% is ordinary sub-cap churn/Entry-49-band, far under CONTAM_MULT) — vs 1.02e9 (Entry 66) and 62M (cap-only rebuild).
- **All 22 nulled months (2024-08→2026-05) recovered**; screened HODL-6m in the recovered window ranges **20.0%–31.3%** — inside the kickoff's economic-sanity gate (0.5%–80%, not 100%), continuous with the pre-window level, and the fake 2025-01 jump is gone.
- Pre-spam months (<2024-04, 41 months): max |Δ screened HODL| = 0.000019 vs the Entry-66 stored rows — the fix is a no-op where no spam existed (the kickoff (d) cross-check).
- **Panel-wide diagnostic** (`_s028_selftransfer_diag.py`, offline, zero network): re-replayed ALL 210 stored-event checkpoints with the fixed engine and diffed against their stored rows — **210/210 unchanged** (no month moves >1pp, no null flips). AAVE was uniquely poisoned; no panel-wide recompute is warranted. (The 50 streamed rows-only checkpoints cannot be offline-diffed; their B2 supply-vs-circ scans were already clean in sessions 026/027.)
- Old checkpoint preserved as `7278_AAVE.entry66.bak`.
**Decision made:** accept the recovered AAVE ch2 series into λ. AAVE is now 3-channel through 2026-05: 67/67 ch2 months, 60 three-channel asset-months; the panel's 3-channel total rises 332 → 354 (+22 = exactly the recovered window).
**Rationale:** flag-don't-guess executed both ways — the kickoff's denominator-swap reading was REJECTED on evidence (it would have shipped a numerator still carrying ~9M phantom aged AAVE), and the engine fix chosen is provably identity-preserving (210-token diff + 41-month AAVE no-op check), not a tuned threshold.
**Downstream impact:** any FUTURE ch2 build/rebuild automatically gets the self-transfer skip; streamed tokens rebuilt later will silently drop this spam class. If another token ever needs a totalSupply cap, add it to PER_TOKEN_VAL_CAP with a live eth_call verification — do not loosen the rule that the global thresholds stay fixed. ORBS-class lesson recorded: fake-value SELF-transfers are a poisoning vector that value caps cannot stop — the identity skip is the structural defense.

### Entry 75 — Session 028 close-out: lambda 7,051 → 7,409 asset-months / 282 → 289 assets; regression-ready coins (lambda∩NVT_GL) 5 → 12; AAVE 3-channel complete; 3-channel asset-months 332 → 354
**Date:** 2026-07-04
**Spec section affected:** 3 (lambda assembly — counts only; z-score/equal-weight logic untouched; the assembler was re-run unmodified, new inputs picked up by the existing channel1_*.csv glob).
**Session totals:** Task A (+358 coin ch1 asset-months / +7 coin assets): BNB 23, S 17, GLMR 52, MOVR 57, XDC 72, CELO 70, AVAX 67 — every series Entry-26-cross-checked at ~0% against the chain's own figure (Entries 71–73). Task B: AAVE's 22 spam-nulled ch2 months recovered via the self-transfer identity fix (Entry 74). **lambda 7,051 → 7,409 observed asset-months / 282 → 289 assets (coins 9 → 16); coin lambda∩NVT_GL 5 → 12 assets / 505 overlapping coin asset-months (ADA, AVAX, BNB, CELO, ETH, GLMR, GNO, MOVR, S, SOL, TRX, XDC); 3-channel asset-months 332 → 354; 2+ channel share 23.2%** (dip from 24.4% is compositional: +358 single-channel coin months entered the denominator).
**Quota:** single Etherscan Pro day, ~45k calls total (two full AAVE re-fetches 33.1k; coin event fetches + balancehistory + cross-checks ~12k) — under 200k/day with wide margin. Keyless sources: official Moonbeam/Moonriver RPCs (Substrate state), forno.celo.org, metrics.avax.network, api.avax.network P-Chain, rpc.soniclabs.com (diagnosis only). No signups, no purchases.
**Open items for session 029+:** (a) DOT/KSM — the ONE actionable gate: free Subscan key (pro.subscan.io signup → `.api_keys.json` under "subscan" → Entry-44 era_stat build); (b) NEAR/Cosmos/BERA/HBAR/SUI/ALGO/EOS/ICP/APT gates documented in Entries 71/73 (no self-serve free path); (c) BNB pre-2024-07 Beacon-Chain era = permanent documented gap; (d) ~500 >3k-holder non-lambda breadth tokens (ch2) still deferred; (e) PQ/NVT_GL expansion still deferred; (f) coin PQ for the new lambda coins (S/GLMR/MOVR/XDC already have NVT_GL by construction of the target list — nothing to do there). Report: `03_data/SESSION028_COIN_STAKING_REPORT.md`.

### Entry 76 — Session 029 (Task A): Channel-2 BREADTH build — 40 of 47 non-lambda TVL-covered tokens built (36+4 across two quota days); 39 enter lambda as new assets; engine extended to BSC/Base; 7-token resume list pending
**Date:** 2026-07-05
**Spec section affected:** 3.2 (holding-duration channel); 3 (lambda breadth — first deliberate BREADTH session since 025).
**Asset(s)/period affected:** the 47 universe tokens with confirmed TVL but ZERO lambda channels (kickoff list). BUILT 40: all 35 Ethereum-mainnet targets + MDX/EPS/BAKE/BTCST/MBOX (BSC). `channel2_holding.csv` 260 -> 300 tokens / 9,794 rows.
**A0 multi-chain adaptation:** `phase1_channel2_stream.py` was ALREADY per-token multi-chain (every call passes the token's chainid); the only constraint was the CHAIN_ID chain-name lookup in load_worklist -> extended with BSC(56)/Base(8453), nothing else touched (VAL_CAP_MULT/CONTAM_MULT=100 unchanged). getLogs coverage probed live: 56/137/42161/8453 all answer (heads 108.06M/89.65M/480.38M/48.20M).
**Results:** 39/40 built targets entered lambda (+1,849 asset-months, all single-channel ch2). WARP (cmc 1166) built but EMPTY — its observed universe window (2016..2018-02) predates the mapped contract's first Transfer entirely (every month "pre-history") = an identity-map mismatch between the old dead cmc-1166 listing and the later-deployed 0x83e6f1E4... contract; flagged for identity review, NOT forced. Hidden giants absorbed in bounded memory (the ORBS lesson again, now at record scale): MDX 17.67M transfers (largest ch2 build ever, 135k getLogs alone), MBOX 21.2M transfers (172k getLogs), BAKE 9.0M, EPS 2.9M, FLOKI 1.67M, ATH 1.34M, AMP 1.17M.
**B2 integrity scan (all 40):** 0 months above the 100x contamination threshold; worst AURORA 49.5x (legit Entry-49 heavy-lock band; treasury-locked supply vs small circ). B4: screened HODL-6m medians bounded — BMX 96.2%/MVL 84.5% are the documented illiquid-inactivity band (Entry 63 liquidity-screen advisory applies); EPIC median 0% = XAN-class age artifact.
**Budget — two quota days + a QUOTA ANOMALY logged honestly:** day-1 process 186,942 getLogs (mainnet 51,109 + MDX 135,833; cap-stopped cleanly before EPS at DAILY_CAP=180k); day-2 process 281,671 (EPS 25.8k + BAKE 74.6k + BTCST 9.4k + MBOX 171.9k; cap-stopped before SFUND). MBOX alone blew through the in-process cap mid-flight — the cap only checks at TOKEN boundaries (the session-027 landmine, now demonstrated at 172k/token scale: pre-size giants before launching; holder_count does NOT predict transfer volume). The API NEVER returned a daily-limit rejection at ~292k calls on the 2026-07-05 UTC day — the assumed 200k/day hard cap did not bind (plan evidently credit-based/higher); we STOPPED anyway per the documented budget rule rather than compound the overshoot.
**Pending (resume list, zero-loss from checkpoints):** SFUND(8972), MYX(36410), ADF(24796, Polygon), AVNT(38299)/KAITO(35763)/VVV(35509) (Base), RAIN(38341, Arbitrum, ~14k est — build last). Skipped by construction (non-EVM): SXP/RUNE/OSMO/SUN/CASINO; HEX permanently deferred (Entry 66).
**Decision made:** accept all 40 series (39 lambda entrants + WARP flagged); resume the 7 next quota day.
**Rationale:** engine unchanged from its validated form beyond the two-line chain map; B2/B4 clean; every target was pre-screened to have TVL so each new lambda asset is regression-ready the moment it lands.
**Downstream impact:** lambda tokens/other with same-month TVL 80 -> 118 assets (the kickoff's "78" figure was from the stale pre-027 coverage file). See Entry 79 for panel totals.

### Entry 77 — Session 029 (Task B): all six orphaned dl_slugs REJECTED — DeFiLlama serves metadata but zero TVL data for COW/ZRX/FORTH/ENS/GTC/CHEEL
**Date:** 2026-07-05
**Spec section affected:** Phase 2 NV/TVL denominator (no change shipped).
**What was found (live, keyless):** `/protocol/{slug}` for cowswap, 0x-aggregator, forth-dao, ens, gitcoin, cheelee each answer HTTP 200 with an EMPTY top-level tvl[], EMPTY chainTvls sub-series on every listed chain, and empty currentChainTvls — DL lists the protocols but tracks no TVL. COW double-checked against the full /protocols dump + parentProtocols: CoWSwap (cmcId 19269) carries tvl null (category "DEX Aggregator" — batch-auction settlement holds no persistent liquidity), and the ONLY CoW-named TVL series (balancer-cow-amm, $391k) belongs to parent BALANCER — not the COW token's protocol claim.
**Decision made:** REJECT all six; tvl_panel.csv and asset_onchain_identity.csv unchanged; no rebuild. GBYTE/PENGU/CYBER not re-attempted per Entry 68.
**Rationale/impact:** confirms Entry 68's "genuinely-no-TVL" classification with response-body evidence. Do NOT re-probe these six; an empty-series 200 is a verdict, not an API failure.

### Entry 78 — Session 029 (Task C): coin Channel-1 BUILT for POL/MATIC, RON, KAIA(KLAY), FLR, EGLD, STRK, XRD, PEAQ — 8 series / 9 lambda assets, +322 asset-months, every one a state read of the chain's own aggregate; 10 gaps/gates documented
**Date:** 2026-07-05
**Spec section affected:** 3.1 (coins); Entry-26 bar applied throughout.
**Asset(s)/period affected:** MATIC(3890) 50 mo 2020-06→2024-08 + POL(28321) 21 mo 2024-09→2026-05 (listing handoff at the Polygon-2.0 boundary — one physical stake never enters lambda twice); RON(14101) 39 mo; KLAY(4256) 43 mo (full observed window); FLR(7950) 32 mo; EGLD(6892) 68 mo; STRK(22691) 19 mo; XRD(11948) 32 mo; PEAQ(14588) 18 mo. Builders: pol_series() added to phase1_channel1_pos_coins_evm.py (429 asset-months/9 assets); NEW phase1_channel1_pos_coins_native.py -> channel1_pos_coins_native.csv (251/7). Fetch stages _s029_pol_fetch.py / _s029_coin_fetch.py / _s029_coin_fetch2.py; raw caches under pos_coins_evm/ (gitignored).
**Sources + kickoff corrections (all response-body verified):**
- **POL/MATIC:** StakeManager 0x5e3Ef2...D908 on ETHEREUM mainnet; the aggregate is currentValidatorSetTotalStake() (3.58B live) — the kickoff's totalStaked() is validator SELF-stake only (11.7M). Etherscan proxy ignores historical tags (Entry 71), and of the free RPCs only **eth.drpc.org serves full mainnet archive eth_call KEYLESS** (publicnode gates archive behind a personal token; llamarpc/meowrpc/flashbots refuse). Cross-checks: drpc==etherscan at head +0.00000%; token balanceOf(StakeManager)/stake in [1.018, 1.341] every month (superset floor >=1 is the integrity condition; the 1.34 peak is the Q1-2021 delegation-churn buffer, reverting <=1.13 after).
- **RON:** official api.roninchain.com RPC is PRUNED; **ronin.drpc.org is a keyless full archive**. Balance route REJECTED (+15.6% over stake at head = pending undelegations incl. revoked candidates); metric = sum(Staking.getManyStakingTotals(ValidatorSet.getValidatorCandidates(b),b)) — contract identities verified against axieinfinity/ronin-dpos-contracts deployments/ronin-mainnet. Balance/sum recorded monthly as superset check [1.000, 1.180]. The 2026 decline (235M->135M) is a genuine unstaking wave (live July figure 105.8M confirms the trend).
- **KAIA/KLAY:** public-en.node.kaia.io returns "execution reverted" for historical calls, but the OFFICIAL **archive-en.node.kaia.io** answers klay_getStakingInfo(block) at any height — the node's OWN consensus staking snapshot (units: KAIA). Cross-check: councilStakingAmounts == CnStaking contract native balances at 0.0000% (8/43 spot-checked).
- **FLR:** P-chain platform.getTotalStake answers live but has no history; the build reads **PChainStakeMirror.totalSupply()** (address resolved from the FlareContractRegistry) via flare-api.flare.network archive eth_call. Cross-check: mirror vs P-chain live -0.21%.
- **EGLD:** tools.multiversx.com/growth-api staking-metrics serves 2,130 DAILY points back to 2020-07-30 keyless; month-end sample; chart head vs live /economics staked -0.10%. (AVAX/Koios/TzKT source-of-record treatment.)
- **STRK:** the kickoff's contract 0x04718f... is the STRK TOKEN and 0x00ca1705... the MINTING CURVE (both ABI-verified); the real staking contract is **0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7** (docs.starknet.io chain-info). blastapi retired; **rpc.starknet.lava.build is a keyless archive** for starknet_call. get_total_stake() at month-end blocks (binary-searched); series from 2024-11 launch (short series kept per kickoff). STRK-only stake (v2 BTC staking power excluded).
- **XRD:** the Radix Babylon Gateway (mainnet.radixdlt.com, official keyless) accepts **historical at_ledger_state timestamps** on /state/validators/list -> sum(stake_vault.balance) over all validators (single page, 245-287 items; fetch raises if it ever paginates). Babylon era only — Olympia (2021-07..2023-09) is a documented gap (old gateway retired).
- **PEAQ:** peaq's staking pallet is a **KILT fork** — storage item ParachainStaking.TotalCollatorStake {collators,delegators}; Moonbeam's .Total is null on peaq (probed). peaq.api.onfinality.io/public is a keyless archive. Early ratio>1 (max 259%) = genesis/vesting stake, SOL/AERO/AVAX flag.
- **Etherscan V2 chainlist probed:** NONE of Flare(14)/Ronin(2020)/Kaia(8217)/Cronos(25)/Chiliz(88888)/Lisk(1135) are among the 64 covered chains — all Task-C1 non-mainnet coins used native/third-party archives.
**Session-028 regression fixed in passing:** the XDC cross-check compared the STATIC event-cache replay to the LIVE balance; a net -10M outflow on 2026-07-04 moved the apparent offset 32.6M->22.6M within hours and tripped the gate. Both sides now pinned at the cache's scan_to block (Pro balancehistory) — offset back to 32,625,000 EXACTLY, identity now time-invariant.
**GAPS/GATES (verdict + exact action):** CRO = Cosmos-side (LCD live-only; ATOM gate, same key sourcing); **CHZ = GATE-OPEN**: rpc.chiliz.com is its own keyless archive and system contract 0x...1000 holds 2.38B CHZ (243M@5M->2.38B head, plausible total-staked trajectory) but the contract is unverified with no aggregate getter and unknown event schema — MOAZZAM ACTION: read total-staked off staking.chiliz.com at a known time and compare to the 0x...1000 balance; if it ties, the build is a ~30-line balance fetch (XDC pattern); LSK = no locatable staking contract (docs 404, Blockscout search empty); TON = Elector balance is a superset (stakes+credits) and live-only; FLOW = spork-bound history; DFI = ocean stats current-only (chain sunset); DASH = no free masternode-count history (stats.masternode.me dead, chainz unsupported, dashcentral current-only 2,062 MNs); WAN = explorer HTML-only; HYPE = validatorSummaries live-only (~438M staked incl. foundation); **CORE = GATE-OPEN (key)**: openapi.coredao.org 401s everywhere — MOAZZAM ACTION: check scan.coredao.org for a free self-serve key -> .api_keys.json under "coredao" -> probe /api/stats/staking_summary. No signups attempted (session rule).
**Decision made:** accept all 8 series into lambda ch1_staking. Every accepted series is the chain's own figure (state read) with an Entry-26 identity/cross-check; nothing reconstructed-and-unanchored was shipped.
**Rationale:** the GLMR/MOVR/CELO state-read standard scaled to 5 more archive sources (drpc mainnet+ronin, kaia archive-en, flare-api, lava starknet) + 2 official first-party APIs (multiversx growth, radix gateway) + 1 pallet fork (peaq).
**Downstream impact:** coin lambda∩NVT_GL 12 -> 20 assets / 505 -> 645 coin-months (new: POL RON KLAY FLR EGLD STRK XRD PEAQ; MATIC adds lambda only, no NVT_GL series). The archive-RPC map (drpc/lava/onfinality/archive-en) generalizes — probe drpc FIRST for any future EVM-chain history need.

### Entry 79 — Session 029 close-out: lambda 7,409 -> 9,580 asset-months / 289 -> 337 assets; regression-ready 92 -> 138 (coins 12->20, tokens/other 80->118); coverage CSV regenerated with a reusable builder
**Date:** 2026-07-05
**Spec section affected:** 3 (lambda assembly — counts only; assembler re-run unmodified, new inputs picked up by the channel1_*.csv glob and the ch2 aggregate).
**Session totals:** Task A (Entry 76) +1,849 asset-months / +39 assets (ch2 breadth, all TVL-covered); Task C (Entry 78) +322 asset-months / +9 coin assets. **lambda 7,409 -> 9,580 observed asset-months / 289 -> 337 assets (coins 16 -> 25); n_channels 1/2/3 = 7,860 / 1,366 / 354; 2+ share 23.2% -> 18.0%** (compositional: +2,171 single-channel months entered the denominator; the 2-ch count's 1,388->1,366 shift is the Entry-74 AAVE months having moved 2ch->3ch in session 028). **Regression-ready: coins (lambda∩NVT_GL) 20 assets / 645 months + tokens/other (lambda∩TVL) 118 assets / 4,194 months = 138 assets** (pre-session true baseline 92 = 12 + 80; the kickoff's "90" used the stale coverage file).
**Coverage CSV:** universe_coverage_status.csv regenerated by NEW reusable 04_code/build_coverage_status.py (replaces the pre-027 inline generation; coin_staking_type carried forward as static metadata; "complete" = SAME-MONTH overlap semantics: pow_only coins on NVT alone, pos coins on lambda∩NVT, tokens/other on lambda∩TVL): 149 complete / 236 partial / 1,554 not_started.
**Quota:** getLogs 186,942 (day-1 process) + 281,671 (day-2 process) + ~1k coin-probe calls; keyless sources did the entire Task C (drpc, lava, onfinality, archive-en.node.kaia.io, flare-api, multiversx growth-api, radix gateway). Quota anomaly documented in Entry 76.
**Open items for session 030+:** (a) the 7-token Task-A resume list (Entry 76 — one clean quota day, ~30-45k calls); (b) DOT/KSM Subscan key (unchanged, Entry 72); (c) CHZ manual anchor + CORE key (Entry 78 actions); (d) WARP cmc-1166 identity-map mismatch review; (e) breadth ch2 for the ~500 >3k-holder non-lambda tokens WITHOUT TVL (lower priority than this session's TVL-covered set was); (f) PQ/NVT_GL expansion still deferred; (g) MATIC has lambda but no NVT_GL — a bitinfocharts/native-series probe could make it the 21st regression-ready coin. Report: 03_data/SESSION029_BREADTH_AND_COIN_PROBE_REPORT.md.


### Entry 80 — Session 030: Task-A resume cut short at user departure — SFUND BUILT (hidden giant); MYX ABORTED mid-build (mega-giant, no checkpoint); 5 tokens untouched
**Date:** 2026-07-05
**Spec section affected:** 3 (lambda assembly — counts only; no engine or threshold changes).
**What happened:** resume of session 029's Task A (7-token WORKLIST, Entry 76 estimated ~30-45k calls). The estimates proved wrong in the same direction as session 029's giants, but worse:
- **SFUND (8972/BSC) BUILT + ACCEPTED:** tf=3,415,005 / gl=28,553 (vs ~4k estimated — a 7x hidden giant). Contract screen 20/45 top-coded; 23/23 observed months built (2023-12..2025-10). **B2 PASS** (max onchain/circ = 1.94x, nowhere near the 100x guard); **B4 PASS** (screened HODL-6m in [12.3%, 24.9%], median 20.6%, last 18.6%, no nulls). All 23 months have same-month TVL (seedify) -> regression-ready immediately.
- **MYX (36410/BSC) ABORTED mid-build, NO checkpoint:** a MEGA-giant. At kill time (batch 81/128): tf=15,438,541 and climbing (would likely have passed MBOX's 21.2M record), gl ~120,440 for MYX alone. The token's Aug-2025 BSC launch region (blocks ~49M+) forced a ~2.5h silent binary-split storm between batch prints. Remaining ~47 batches at ~790s/batch put completion ~10h out — past the user's 4:30 PM departure, so the process was killed at 15:07. The streamed engine has no partial checkpoint by design (Entry 66 tradeoff), so MYX restarts from scratch next session. **Budget a dedicated session/quota day for MYX alone (~250-300k calls).**
- **Untouched:** ADF (24796/Polygon), AVNT (38299/Base), KAITO (35763/Base), VVV (35509/Base), RAIN (38341/Arbitrum).
**Decision made:** kill at the departure cutoff rather than leave the engine running unattended for a week (user out 7/6-7/12); accept the ~120k-call loss on MYX. SFUND accepted into ch2/lambda.
**Rationale:** an unattended week-long process risks a sleep/reboot kill mid-token (same loss) plus a week of unpushed local state, violating the record-keeping rule. The quota is daily-resetting (and per Entry 76 evidently non-binding), so the redo cost is time, not budget.
**Methodology lesson:** est_getlogs_calls from holder counts UNDERSHOOTS BSC tokens by 7-30x (SFUND 4k->28.5k; MYX 4k->120k+ unfinished). For BSC, treat any estimate as a lower bound and sequence SMALL CHAINS FIRST (Polygon/Base/Arbitrum), BSC last.
**Downstream impact:** channel2_holding.csv 300 -> 301 tokens / 9,817 rows. **lambda 9,580 -> 9,603 asset-months / 337 -> 338 assets. Regression-ready 138 -> 139** (coins 20 unchanged; tokens/other lambda∩TVL 118 -> 119 assets / 4,194 -> 4,217 months). Coverage regenerated: 150 complete / 235 partial / 1,554 not_started.
**Quota:** ~149k getLogs this session (28,553 SFUND + ~120,440 MYX-aborted + startup), single process, no API rejection.
**Open items for session 031 (Monday 2026-07-13):** (a) 6-token resume — small-first order WORKLIST=24796,35509,35763,38299,38341 then MYX=36410 alone on a fresh day (see 04_code/CLAUDE_CODE_SESSION031_TASK_A_RESUME_PROMPT.md); (b)-(g) of Entry 79 unchanged. Report: 03_data/SESSION030_TASK_A_RESUME_REPORT.md.

### Entry 81 — Session 031: Task-A day-1 resume — ALL 5 SMALL TOKENS BUILT (three Base hidden giants); two OS interruptions survived; MYX still queued for its dedicated day
**Date:** 2026-07-24 (ran 2026-07-23 14:52 CDT → 2026-07-24 evening; the intervening night was lost to OS sleep, see interruptions below)
**Spec section affected:** 3 (lambda assembly — counts only; no engine or threshold changes; VAL_CAP_MULT/CONTAM_MULT untouched at 100).
**What happened:** the 5-token day-1 WORKLIST (24796,35509,35763,38299,38341) ran to completion in small-chains-first order. Per-token:
- **ADF (24796/Polygon) BUILT:** tf=367,684 / gl=1,499 (vs 1,871 est — Polygon estimate HELD, 0.8x). 9/41 months coded, 4 screened months into ch2. B2 PASS (max onchain/circ 8.2x); B4 PASS (screened HODL-6m median 3.9%, last 3.9%).
- **VVV (35509/Base) BUILT — NEW ALL-TIME ch2 RECORD:** tf=27,792,859 (beats MBOX's 21.2M) / gl=82,066 (vs ~1k est — an **82x** hidden giant). 12/29 coded, 4 screened months. B2 PASS (max 2.4x); B4 PASS (median 5.7%, last 5.5%).
- **KAITO (35763/Base) BUILT:** tf=8,621,771 / gl=25,870 (vs ~3k est — 8.6x). 7/54 coded, **16 screened months** (largest month contribution this session). B2 PASS (max 5.3x); B4 PASS but FLAGGED HIGH: median 64.9% / last 66.7% — consistent with KAITO's airdrop-lockup profile; inside [0,80%], kept per protocol.
- **AVNT (38299/Base) BUILT:** tf=17,646,973 / gl=52,758 (vs ~4k est — 13x). 7/36 coded, 9 screened months. B2 PASS (max 7.4x); B4 PASS (median 0.0%, last 4.6% — token is ~10 months old, near-zero 6m-HODL is structural, not anomalous).
- **RAIN (38341/Arbitrum) BUILT (twice):** tf=4,284,832 / gl=19,315 (vs 13,637 est — Arbitrum estimate held, 1.4x). 11/52 coded, 7 screened months. B2 PASS (max 5.0x); B4 PASS (median 0.0%, last 17.2% — young token, same pattern as AVNT). First attempt killed by an OS restart at batch 536/587 (~9,824 gl lost, no partial checkpoint by design); rebuilt from scratch same day, clean.
**Interruptions (both OS-level, neither corrupted data):** (1) **Modern Standby stall:** the machine's sleep timeout was 20 minutes; it slept on-and-off from ~18:00 on 7/23 through the 9:10 AM wake on 7/24, freezing the build mid-VVV for ~15h. Diagnosed via Kernel-Power event log + py-spy thread dump (workers healthy, blocked in-flight); the engine's 60s request timeout + 6 retries self-healed on wake with zero loss. **Sleep set to NEVER (AC+DC) via powercfg — keep it that way through MYX day.** (2) **Windows Update auto-restart at 16:40 on 7/24** killed RAIN at 90%. Sleep settings do not prevent update restarts — **pause Windows Update before the MYX run.**
**Methodology lesson (extends Entry 80):** holder-count estimates undershoot **Base** the same way they undershoot BSC: VVV 82x, KAITO 8.6x, AVNT 13x. Polygon (0.8x) and Arbitrum (1.4x) held. Treat Base like BSC in all future sequencing: estimates are lower bounds; build Base late with dedicated headroom.
**Downstream impact:** channel2_holding.csv 301 → **306 tokens / 9,857 rows** (+40 screened months). **lambda 9,603 → 9,638 asset-months / 338 → 341 assets. Regression-ready 139 → 142** (coins 20 unchanged; tokens/other λ∩TVL 119 → 122 assets / 4,217 → 4,243 same-month rows). Accounting note: only ADF/KAITO/AVNT are net-new λ assets — VVV and RAIN already carried ch3 λ months; VVV's 4 ch2 months coincide exactly with its existing ch3 months (rows upgraded to multi-channel, no new rows), RAIN netted +6. TVL overlap of the new builds: ADF 4, AVNT 9, KAITO 7, RAIN 7, VVV 1 months. Coverage regenerated: **153 complete / 232 partial / 1,554 not_started**.
**Quota:** ~191k getLogs total across the session (≈28.9k on 7/23 before sleep; ≈162.5k on 7/24 including the 9.8k lost RAIN first attempt). Single-day 7/24 usage ~162k under DAILY_CAP=185k; no API rejection at any point (consistent with Entry 76's credit-based-cap finding).
**Open items for session 032:** (a) **MYX (36410/BSC) alone on a dedicated quota day** — budget ~250-300k calls / 12-15h wall-clock, start EARLY, sleep=never confirmed, **pause Windows Update first**; reuse the Day-2 section of 04_code/CLAUDE_CODE_SESSION031_TASK_A_RESUME_PROMPT.md. (b)-(g) of Entry 79 unchanged (DOT/KSM key, CHZ anchor, CORE key, WARP review, non-TVL breadth, MATIC NVT probe). Report: 03_data/SESSION031_TASK_A_RESUME_REPORT.md.

### Entry 82 — Session 032: MYX (36410/BSC) ch2 BUILT; Task-A fully closed
**Date:** 2026-07-24 (overnight session; build ran ~17:58–20:37 CDT — 2.7h, not the budgeted 12–15h)
**Spec section affected:** 3 (lambda assembly — counts only; no engine or threshold changes; VAL_CAP_MULT/CONTAM_MULT untouched at 100).
**What happened:** MYX ch2 (HODL-wave) built clean on the dedicated quota day: **67,233 getLogs** (+40 getcode) vs the ~250–300k budget — **0.22–0.27x, the first large BSC token to come in far UNDER budget**. 10/10 months built (2025-08..2026-05, the full observed window since the Aug-2025 launch), 10 screened months. Screened HODL-6m median **3.0%** / last **5.2%**. **B2 PASS** (max onchain/circ 10.5x in the launch month, decaying to 5.8x — nowhere near the 100x guard). **B4 PASS** (young token; near-zero early 6m-HODL is structural, same pattern as AVNT/RAIN). Contract screen 21/40 top-coded. **tf=22,451,143 — second-largest ch2 build ever (beats MBOX 21.2M; VVV holds the record at 27.8M) and the largest BSC build.**
**Consistency check vs the session-030 abort:** at batch 81/128 this run printed tf=15,459,154 vs 15,438,541 at the 030 kill — near-identical, the rebuild reproduces the aborted run's data.
**Anomaly (favorable, unexplained):** session 030 logged ~120,440 gl for MYX by batch 81; this run needed only 46,346 to the same point (2.6x fewer) with identical tf. Engine unchanged and block density is fixed, so the 030 counter likely included retry storms (rate-limit churn); treat 030-derived call estimates as upper bounds. The predicted multi-hour silent stretch after batch ~61 materialized but lasted only ~1h (batch 61→66: 67s→3,659s).
**Ops:** sleep=never held (no standby events). Windows Update could NOT be paused — the session shell is non-elevated and the pause keys are HKLM; verified instead that no reboot was pending and the July cumulative wave had already installed the same morning. No OS interruption occurred. For future long builds: pause WU manually from Settings before leaving, or run the session elevated.
**Downstream impact:** channel2_holding.csv 306 → **307 tokens / 9,867 rows** (+10 screened months). **lambda 9,638 → 9,648 asset-months / 341 → 342 assets. Regression-ready 142 → 143** (coins 20 unchanged; tokens/other λ∩TVL 122 → 123 assets / 4,243 → 4,253 same-month rows). MYX has same-month TVL (myx-finance) in all 10 λ months → regression-ready immediately. Coverage regenerated: **154 complete / 231 partial / 1,554 not_started**.
**Quota:** 67,273 calls total (67,233 getLogs + 40 getcode), single process, no API rejection, well under DAILY_CAP=185k — cap never approached.
**Task A fully closed:** all 47 session-029 targets resolved — 41 built, 5 non-EVM skipped, 1 (WARP, cmc-1166) deferred for identity-map review (built-but-empty, Entry 79).
**Open items for session 033:** Entry-79 (b)–(g) unchanged — DOT/KSM Subscan key, CHZ manual anchor (gate-open), CORE key, WARP identity review, non-TVL breadth ch2 (~500 >3k-holder tokens), MATIC NVT_GL probe (candidate 21st regression-ready coin). Report: 03_data/SESSION032_MYX_REPORT.md.

### Entry 83 — Session 033: XTZ/MATIC NVT_GL probes NEGATIVE (prompt premise wrong); JOE/SAFE gaps closed as architectural
**Date:** 2026-07-25
**Spec section affected:** 4.1 (NVT_GL coverage — no data changes; two NaN-marker notes refined; JOE/SAFE/DYDX gaps classified).
**What happened:** Session 033's kickoff prompt directed building XTZ PQ from TzKT's `/v1/statistics/daily` field `totalTransferred`. **That field does not exist.** Verified live: the Statistics schema is supply/staking-only (totalSupply, circulatingSupply, totalFrozen, staking/delegation fields — no volume); the full 287-path TzKT swagger has NO historical volume/sum endpoint anywhere; `back.tzkt.io/v1/home` (browser UA+Referer required) serves only current-day volume aggregates + a 30-day price chart. The prompt's premise — "TzKT was never tried" — was correct, but trying it yields nothing: TzKT indexes everything EXCEPT aggregate historical transfer value.
**XTZ (2011, 78 λ months):** exhaustive free-source sweep, all NEGATIVE: TzStats api.tzstats.com DEAD (connection refused); TzPro unreachable; CoinMetrics community API exposes only TxCnt/TxTfrCnt for xtz (TxTfrValUSD → 403 pro-gated; GitHub csv/xtz.csv same); bitinfocharts sentinusd-xtz EMPTY page (not the BTC default — simply no data); Messari legacy keyless API 404 (dead); CryptoCompare blockchain histo 401 key-gated. Raw TzKT operation iteration forbidden (Entry 31/32). **XTZ stays PQ=NaN**; marker refined to `NaN:xtz_no_free_native_series_s033` with the full probe list. XTZ remains the largest single pq_nvtgl gap (78 λ months) — only a paid source (Artemis/CM-pro/TzPro key) closes it.
**MATIC (3890, 50 λ months):** bitinfocharts `sentinusd-matic` returns the **BTC default series** (BTC-guard triggered: identical first date 2010/07/17 and last value to the BTC reference — Polygon didn't exist in 2010). CoinMetrics community rejects value metrics for 'matic'. No free keyless Polygon native-transfer-value source; λ window ends 2024-08 at POL handoff. **MATIC stays PQ=NaN**; marker refined to `NaN:polygon_native_volume_no_free_source`. The "candidate 21st regression-ready coin" idea (Entry 79g) is closed negative.
**JOE (11396, 6 λ months) and SAFE (21585, 10 λ months): PERMANENTLY CLOSED — architectural, not data-sourcing.** Both are classified `asset_class=coin` via `consensus tags: ['staking']`, but neither is a chain-native gas coin: JOE is Trader Joe's DEX governance token (Avalanche/Arbitrum, λ from veJOE vote-escrow), SAFE is the Safe{Wallet} governance token. No native chain ⇒ no settlement value ⇒ no valid NVT_GL denominator exists in principle. Verified both also have ZERO rows in tvl_panel.csv ⇒ no TVL path either. Neither has (or needs) a pq_coins.csv row. Do not re-probe.
**DYDX (28324, 1 λ month):** legitimately a coin (dYdX Chain Cosmos L1 native) but 1 λ month (2024-03) is far too short for regression. Skip; revisit only if λ extends via a Cosmos/Mintscan key.
**Downstream impact: NONE.** pq_coins.csv row count unchanged (3,275; 2 marker notes edited). phase2_nvt_gl.py + build_coverage_status.py re-run clean and identical: NVT_GL 2,526 asset-months / 67 assets; **coins regression-ready (λ∩NVT_GL) 20 / 645 months — unchanged**; coverage 154 complete / 231 partial / 1,554 not_started. Regression-ready total stays 143.
**Open items for session 034:** Entry-79 (b)–(e) unchanged — DOT/KSM Subscan key, CHZ manual anchor (gate-open), CORE key, WARP identity review, non-TVL breadth ch2 (~500 >3k-holder tokens). (f)/(g) MATIC probe now CLOSED (this entry). Report: 03_data/SESSION033_XTZ_MATIC_NVT_REPORT.md.

### Entry 84 — Session 034: CHZ ch1 BUILT; Blockchair XTZ/MATIC FAILED (keyless unusable);
  EVM DeFi Breadth Batch 1 (101 of 102 tokens)

CHZ (4066): ch1 staking built via Chiliz Chain 2.0 public RPC (chiliz.drpc.org;
eth_getBalance on 0x...1000 staking contract at month-end blocks; anchor drift -1.03%
vs 2,416,757,292 CHZ confirmed 2026-07-25 on staking.chiliz.com). Window:
2023-07..2026-05 (35 months). Staking ratio range 2.35%..26.61% (real ~4x step-up
2024-06). pq_source suffix: chiliz-chain-pubRPC. CHZ already had 21 non-NaN PQ months
in pq_coins.csv -> CHZ = 21st regression-ready coin.

Blockchair XTZ: FAILED. tezos/{calls,operations,transactions} all HTTP 404 (no
aggregation tables exposed for Tezos); IP was then blacklisted (HTTP 430 "apply for
an API key") after ~4 anonymous requests, including on /stats. Free anonymous tier is
effectively unusable in 2026. Paid key (~$30/mo) MIGHT unblock, but the 404s suggest
Tezos aggregation may not exist at any tier - confirm with Blockchair support before
paying. NOT subscribed (needs Moazzam approval). XTZ stays PQ=NaN.

Blockchair MATIC: FAILED, same blacklist; polygon/transactions also 404 before the
430s started. Same paid-key caveat. MATIC stays PQ=NaN.

EVM DeFi Breadth Batch 1: 101 of 102 tokens built (MSOL 11461 already complete ->
skipped). 154,049 getLogs (est 147k), 47.56M transfers, 2,916 screened lambda months.
B2 clean across the batch (no 100x contamination flags). B4 flagged-high (HODLmed>80%,
kept per rule): META, TROY, SMT, YOU, BOX(3475), WHITE, HOT, BOX(2945), STRONG.
Biggest builds: STRONG 6.66M tf / 20.0k gl, WSTETH 4.02M tf / 11.9k gl, XAI 2.62M tf.
Survivorship targets built: CEL (Celsius, 54 scrMo), FTT (FTX, 81 scrMo), MULTI
(Multichain, via prior slug).

TVL slug matching (the ABC-validation lesson applied): raw symbol match was ~40% wrong
(Litentry->lighter, old-Jupiter 1503->jupiter-lend, Wrapped Solana->solana-farm, etc.).
Re-matched with DL cmcId authority + name corroboration + individual verification:
- 24 token-class dl_slugs written to asset_onchain_identity.csv (incl. ETHDYDX->dydx-v3,
  KNC 9444->kyberswap-classic, SYRUP->maple, SKY->sky-lending, MORPHO->morpho-blue).
- OTHER_ADDS += MULTI/multichain (dead, 49 mo), ORC/orbit-bridge (hacked, 46 mo),
  MUBI/multibit-protocol, FF/falcon-finance.
- CHAIN_LEVEL += METIS/chain:Metis (54 mo), XAI/chain:Xai (28 mo) per Entry-68 pattern.
- REJECTED on semantics: UNFI (DL unifi cmcId=1412 collision), LOCUS (Locus Finance !=
  Locus Chain), JUP 1503 (Solana Jupiter != 2017 Jupiter), SOL 16116 (wrapped), DAO 8420
  (vesting tracker != protocol TVL), AGIX (own-token staking pool = circular), WOO woo-x
  (CEX reserves; used woofi-swap instead).
- LST receipt tokens (wstETH/weETH/cbETH/rETH/sfrxETH/mETH/ETHx/swETH/rswETH/ezETH/
  rsETH/WBETH/tETH/LBTC/MSOL/aEthWETH/bUSD0) deliberately get NO protocol TVL: the
  receipt token's NV IS the protocol TVL (NV/TVL ~= 1 by construction, circular).
- CEL and FTT have NO DeFiLlama entries (CeFi books never TVL-tracked); dead-protocol
  TVL defense rests on MULTI/ORC/dydx-v3/ribbon/idex-v1 etc.
- ARKM, PRIME (echelon-prime): slugs valid but DL series empty (zero-TVL protocols).
tvl_panel.csv rebuilt: 159 assets / 7,889 asset-months (was ~128/6,7xx).

Post-assemble: lambda 12,599 asset-months / 444 assets (was 9,648/342).
Regression-ready 143 -> 173 (coins 20->21 [CHZ], tokens/other 123->152 [+29 Batch-1]).
channel2_holding.csv: 408 tokens / 12,955 rows. Coverage: 184 complete / 302 partial /
1,453 not_started.
Remaining EVM DeFi breadth batches:
  Batch 2 (session 035): 13 tokens, ~119k getLogs - WORKLIST in 034 prompt
  Batch 3 (session 036): stETH + MEME, ~110k getLogs
  Batch 4 (session 037): SHIB alone, ~128k getLogs

### Entry 85 — Session 035: EVM DeFi Breadth Batch 2 (13/13 tokens); KNCL window-clip;
  SNX/LEND/ANKR TVL

Batch 2 built 13/13 in one run: 74,783 getLogs (est 119k -> 0.63x), 22.9M transfers,
592 screened months. B2 clean. B4 flagged-high kept: PNT (97.9% - dead token, 5 scrMo).
Long histories: FUN 105 scrMo (2017+), ANKR 85, SNX 73 (assemble window 2019-05+),
SLP 58, ELON 56. Note: cmc 2691 "PNT" is Penta (dead 2018 token), NOT pNetwork - the
034 prompt's note was wrong; actual gl ~1.1k not 14.3k.

TVL decisions:
- SNX (2586) -> parent slug `synthetix` (children v1+v2/v3/v4 only in /protocols;
  parent fetchable per Entry-68 CRV/GMX precedent). 82 mo, 73 lambda-overlap.
- LEND (2239) -> `aave-v1` (AAVE 7278 keeps aave-v2; protocol-era split, no window
  needed). 73 mo, 4 lambda-overlap (2020-05..2020-08 - LEND died 2020-08; the
  low-TVL dead-token region).
- ANKR (3783) -> OTHER_ADDS `ankr` (cmcId=3783 exact; other-class filter gap, same as
  RPL Entry 68). 67 mo, 66 overlap.
- KNCL (1982) -> `kyberswap-classic` WINDOW-CLIPPED <=2021-06 via new CLIP mechanism
  in phase2_build_tvl_panel.py (MATIC/POL rule: KNC 9444 lambda starts 2021-07;
  one physical TVL never in two assets' rows same month). 9 mo 2020-10..2021-06.
- MKR investigated: DL parent `maker` 400s; MakerDAO history lives in sky-lending
  (parent#maker) already on SKY 33038. MKR has ZERO lambda months -> no assignment,
  no double-count risk (SKY lambda 2025-05+ only touches post-migration months).
  Revisit only if MKR ever gets lambda.
- SAI (2308): NO TVL by rule - liability/receipt-token circularity (SAI is the CDP
  stablecoin itself; NV ~= pegged supply, NV/TVL = inverse collateral ratio, not a
  valuation multiple). Same family as the LST receipt exclusion (Entry 84). SAI keeps
  its 25 lambda months (ch2 survivorship) but is not regression-ready.
- EETH (28568): LST receipt token -> excluded (Entry 84 rule). 11 lambda months kept.
- No TVL exists: FUEL, FUN, ERC20, MLK, SLP, ELON, PNT (meme/game/dead, no protocol).

tvl_panel: 163 assets / 8,120 asset-months. Post-assemble: lambda 13,191 / 457 assets.
Regression-ready 173 -> 177 (coins 21, tokens/other 156). ch2 421 tokens / 13,580 rows.
Coverage 188/311/1,440.
Remaining breadth batches: 036 stETH+MEME (~110k gl), 037 SHIB (~128k gl).

### Entry 86 - Session 036: stETH + MEME ch2 built (lambda-only; no TVL regression entry)

stETH (8085/Ethereum): 13,365 getLogs / 4,529,175 transfers / 50 screened months.
B2 pass. B4 pass (HODL-6m median 13.4%, last 13.1%). TVL excluded: LST receipt
circularity (NV~=Lido TVL by construction, Entry 84 rule). Lambda months retained for
conviction-only panel. No stETH -> lido mapping created.

MEME (28301/Ethereum): 9,079 getLogs / 2,932,933 transfers / 31 screened months.
B2 pass. B4 pass (HODL-6m median 3.7%, last 15.4%). TVL: DeFiLlama HAS a `memecoin`
protocol listing (cmcId=28301, correct contract 0xb131...cd74, category Farm) but its
TVL series is EMPTY (0 data points, no currentChainTvls) -> no usable protocol TVL,
lambda-only. Nuance vs prompt: cmcId match exists but carries no data; not a symbol
clash (conflux MemeDex is the unrelated symbol match).

getLogs actual 22,444 total vs ~110k estimate (est was ~5x high; sparse pre-2021
blocks). Runtime ~50 min.

Post-assemble: lambda 13,272 asset-months / 459 assets. Regression-ready 177
(no change, as expected - both adds lambda-only). ch2 423 tokens / 13,661 rows.
Coverage 188/313/1,438.

Remaining EVM breadth: Session 038 - SHIB (5994), ~128k getLogs est (likely high),
lambda-only. (Session 037 repurposed for DOT/KSM/CORE ch1 — see Entry 87.)

### Entry 87 — Keys received; Session 037 scope: DOT + KSM ch1 (Subscan) + CORE ch1 probe (CoreScan)
**Date:** 2026-07-27
**Keys added to .api_keys.json:**
- "subscan": 3d09e805af23487a9e1ee546338b7216 (received prior session — confirmed in place)
- "coredao": 97375a02225a40688d743659236ea82b (received this session from scan.coredao.org)

**Assets unlocked:**
- DOT (6636) + KSM (5034): Subscan era_stat key-gated (Entry 44). With key in place, build is
  ready: POST polkadot.api.subscan.io/api/scan/staking/era_stat (X-API-Key header), paginate
  all eras, bonded_total / 1e10 (DOT) or 1e12 (KSM), map end_block_num -> timestamp via
  genesis_ts + block_num * 6s, bucket to months. Both have NVT_GL -> regression-ready on ch1
  build. Expected: coins 21 -> 23.
- CORE (23254): openapi.coredao.org 401 without key (Entry 78). Key now available.
  Probe: GET openapi.coredao.org/api/stats/staking_summary?apikey=<key>. If historical series
  available -> build directly. If current-only -> block-level balance reads on PledgeAgent/staking
  contract (Core EVM chainid 1116, block time ~3s, genesis 2023-01-14). CORE has NVT_GL
  (40 months) -> regression-ready if ch1 confirmed. Expected: coins -> 24.

**Session 037 prompt:** 04_code/CLAUDE_CODE_SESSION037_DOT_KSM_CORE_PROMPT.md
**Session 038 (SHIB ch2):** deferred; see prior "next" note above.
**Regression-ready target post-037:** 177 -> 180 (coins 21->24) if all three PASS.

### Entry 88 — Session 037 RESULTS: DOT + KSM + CORE ch1 ALL BUILT (method pivot: archive-RPC state reads)

**Method pivot (supersedes the Entry-87 build plan):** Subscan `era_stat` turned out
to be PER-ADDRESS (400 "address is a required field") — Subscan exposes NO
network-wide bonded history on the free plan (`/api/scan/daily` category `Bonded`
returns all zeros and the key has a ~2-month `history_window_exceeded` cap; the
subscan.io site itself was mid-upgrade, charts unreachable). Instead: raw-key
state reads (twox128/twox64concat, no metadata decode) of
`Staking.ErasTotalStake(ActiveEra)` at month-end blocks (interpolation search on
`Timestamp.Now`) from public ARCHIVE RPCs. Post-Asset-Hub-Migration months
(relay staking storage cleared) read from the Asset Hub at the same timestamp:
DOT relay<=2025-10 / AH from 2025-11; KSM relay<=2025-09 / AH from 2025-10.
Endpoints: OnFinality public (relays); parity `*-asset-hub-rpc.polkadot.io` (AHs,
archive verified to >=2022). Script: `04_code/session037_build_dot_ksm.py`.

**DOT (6636):** 71 months (2020-08-31..2026-06-30) built. 1 DOT = 1e10 Planck.
Latest 862,345,368 DOT. Cross-check: fresh head 881,519,184 -> drift -2.18% PASS
(July growth); external anchor ~881.9M / 52.0% (Coinbase+StakingRewards 2026-07)
matches fresh to 0.05%. AHM boundary continuous (831.5M -> 825.9M, -0.7%).
Source: archiveRPC polkadot(+assethub):Staking.ErasTotalStake / 1e10.

**KSM (5034):** 76 months (2020-03-31..2026-06-30) built. 1 KSM = 1e12 Planck.
DROPPED 2019-11..2020-02: pre-runtime-1050 storage only exposes `SlotStake` =
MINIMUM validator backing (11k KSM), not network total — wrong metric (and
pre-universe anyway). Latest 8,384,479 KSM; fresh 8,559,862 -> drift -2.05% PASS;
external anchor ~8.5M / 46.0% matches. staking_ratio suppressed for 2020-07
(CMC circulating 2.99M < staked 5.98M — bad CMC point; 8.47M next month). Note:
CMC holds KSM circulating at 8.47M through 2020-2024 -> ratios 0.77-0.93 there
carry a stale denominator (universe panel remains supply authority).
Source: archiveRPC kusama(+assethub):Staking.ErasTotalStake / 1e12.

**CORE (23254):** BUILT EXACT, 42 months (2023-01-31..2026-06-30).
staking-api.coredao.org `/staking/summary/overall` is CURRENT-ONLY (round param
ignored), openapi.coredao.org proxy/balancehistory endpoints return empty 200s,
and rpc.coredao.org is pruned — but Ankr (`rpc.ankr.com/core`) and dRPC
(`core.drpc.org`) are ARCHIVE. Definition validated TO THE DIGIT at head:
official stakedCoreAmount == sum over ACTIVE validators
(ValidatorSet.getValidatorOps(), legacy fallback currentValidatorSet(i) walk) of
CoreAgent.candidateMap(op).amount (0x...1011, post-StakeHub upgrade; from
2024-11) / PledgeAgent.agentsMap(op) word0 (0x...1007, legacy; <=2024-10;
word0 vs word2 differ <2%, boundary continuous with real Oct-Nov 2024 decline).
Naive contract-BALANCE reads would run ~6% HIGH (335.9M vs 315.8M) — rejected.
Latest 307,727,006 CORE; fresh API 315,775,339 -> drift -2.55% PASS.
Ratio range 0.114-0.81 (early CMC circulating tiny). CORE-only (BTC/hashpower
dual-staking excluded). Script: `04_code/session037_build_core.py`.
Source: core-archiveRPC eth_call active-validator stake sum.

**Post-assemble:** lambda 13,272 -> 13,449 asset-months / 459 -> 462 assets.
Coverage 188/313/1,438 -> 189/314/1,436. Regression-ready 177 -> 178:
coins 21 -> 22 (CORE enters — it already had 27 NVT_GL months; same-month
lambda x NVT overlap confirmed). DOT/KSM do NOT enter: the Entry-87/prompt
premise "DOT+KSM have NVT_GL" was WRONG — nvt_gl_panel has 68/70 rows for them
but pq_usd ALL NULL (no PQ source) -> they move not_started -> PARTIAL
(pq_nvtgl is now their only gap; ch1 gate CLOSED).

**Bookkeeping note:** the narrative "coins 21" vs coverage-file pos-coin count 20
pre-session is explained by TRX (cmc 1958): coin_staking_type mislabeled
`pow_only` (TRON is DPoS) while having ch1 lambda (78 months) — the file counts
it in the pow bucket, narrative counted it as a staking coin. Worth a one-line
fix in a future universe-map pass; not touched this session.

**Open items for session 038:** SHIB (5994) ch2 ~128k gl est (treat as ~5x high);
WARP (1166) identity review; Cosmos key -> CRO/INJ/SEI/KAVA ch1; Blockchair
support email re XTZ/MATIC before paying; DOT/KSM PQ source hunt (would make
them regression-ready); TRX coin_staking_type fix; bibliography sanity-check.
Report: 03_data/SESSION037_DOT_KSM_CORE_REPORT.md

### Entry 89 — Session 038: SHIB ch2 built (λ-only; no TVL regression entry)

SHIB (5994/Ethereum): 53,683 getLogs / 17,845,462 transfers / 61 screened months
(2021-05..2026-05, zero contaminated). B2 pass (no month excluded by the 100×
contamination guard). B4 pass (screened HODL-6m median 78.1% ≤ 80%; last month
82.5%). Contract screen 13/81 candidate addresses. Actual getLogs vs 128k
estimate: 0.42x (holder-count overestimate pattern of sessions 034–036 holds).
Wall time ~2.1h at 8 workers.

TVL: no protocol TVL for SHIB. `shibaswap` slug in tvl_panel belongs to BONE
(cmc_id=11865, ShibaSwap governance token, 59 months already in panel) —
assigning to SHIB would double-count the DEX TVL against the wrong token.
SHIB → λ-only.

Post-assemble: λ 13,449 → 13,510 asset-months / 462 → 463 assets.
channel2_holding.csv 423 → 424 tokens / 13,661 → 13,722 rows. Coverage
189 complete / 315 partial / 1,435 not_started (SHIB not_started → partial).
Regression-ready 178 → 178 (no change, as expected: coins 22, tokens/other 156).

EVM DeFi breadth complete (all batches 1–3b done). Next: Session 039 — DOT/KSM PQ
source probe; TRX coin_staking_type fix; WARP identity review.

### Entry 90 — Session 039: DOT/KSM PQ probe negative; TRX label fix; WARP closed

**DOT/KSM PQ probe (Task A): NEGATIVE — no free source.**
Subscan /api/scan/daily (key on file): `format=month` not supported (day/hour/6hour
only); `format=day` over any multi-year window → 403 `history_window_exceeded` for
ALL four categories (transfer/extrinsic/transaction/fee), both polkadot and kusama.
Window bisection: 30-day range returns data, 90-day fails → free window ≈ 2 months,
same wall session 037 hit for "Bonded". The 30-day payload is also degenerate
(2026-06-01: total=3 transfers / 5.98 DOT — not network-wide volume).
Blockchair: /polkadot/stats and /kusama/stats return 200 keyless, BUT (a) the
aggregation endpoint (`/{chain}/calls?a=date(time),sum(value)&q=type(transfer)`)
is HTTP 404 — same no-aggregation-tables pattern as XTZ/MATIC (Entry 84), and
(b) both indexes are FROZEN (DOT best block 2025-05-26, KSM 2025-05-09) — even a
paid key could not cover the panel through 2026-06. Raw block iteration remains
FORBIDDEN (Entry 31/32). Decision: **no free PQ source for DOT/KSM; candidates
exhausted. They stay PARTIAL (gap = pq_nvtgl only). Reopens only with Subscan Pro
or another paid volume series** (Blockchair ruled out — stale index).

**TRX (1958) coin_staking_type fix (Task B):**
Label was `pow_only`; corrected to `pos` (TRON = DPoS; ch1 freezeresource series,
78 λ months). Source of label: `universe_coverage_status.csv` itself —
build_coverage_status.py line 33 carries `coin_staking_type` forward from the old
file (static metadata, no live source). Edited the CSV row + re-ran the builder.
TRX coverage status: complete (unchanged), but now via the pos λ∩NVT same-month
path (58 overlap months) instead of the pow_only NVT-alone path. Regression-ready
coins now derive cleanly to 22 WITH TRX included — the Entry-88 "coin-count ±1"
bookkeeping discrepancy is resolved; headline totals unchanged (178).

**WARP (1166) identity review (Task C): PERMANENT IDENTITY MISMATCH — CLOSED.**
CMC id 1166 = "WARP" warpcoin.com — a 2016-02 standalone PoS coin (CMC category
"coin"), inactive since 2018-05-08, own chain (chainz.cryptoid.info explorer),
supply 1.1M. It NEVER deployed an ERC-20. The stored contract
0x83e6f1E41cdd28eAcEB20Cb649155049Fac3D5Aa (ch2 checkpoint: 27,257 getLogs,
0 transfers ever) is a different, later "WARP"-named token; the dl_slug
`polkastarter` is DeFiLlama's own wrong cmcId (Polkastarter = POLS, cmc 7208 —
the Entry-52 collision). Actions: (1) `phase1_build_identity_map.py` gains a
BAD_DL_CMCID = {"1166"} registry-drop override so rebuilds can't resurrect the
mapping; (2) identity CSV row cleared (dl_slug/address/chains blanked,
dl_matched=False); (3) 54 bogus polkastarter TVL months PURGED from tvl_panel
(8,120 → 8,066 months / 163 → 162 assets); (4) coverage now `not_started`.
No λ rows existed (empty checkpoint never contributed) — no λ impact.

Post-assemble: λ 13,510 / 463 assets (unchanged). Coverage 189 complete /
314 partial / 1,436 not_started (WARP partial → not_started). Regression-ready
178 (coins 22, tokens/other 156) — unchanged, now internally consistent.

**Open items for session 040:** Cosmos key → CRO/INJ/SEI/KAVA ch1; Blockchair
support email decision (XTZ/MATIC only — DOT/KSM now ruled out); DOT/KSM PQ
reopens only on Subscan Pro decision; bibliography sanity-check.
Report: 03_data/SESSION039_DOTKSM_PQ_FIXES_REPORT.md

### Entry 91 — Session 040: CRO/KAVA ch1 via Cosmos Archive LCD; INJ/SEI negative

**Approach:** free, keyless Cosmos SDK LCD `cosmos/staking/v1beta1/pool` with
`x-cosmos-block-height` header at month-end blocks found via binary search on
`cosmos/base/tendermint/v1beta1/blocks/{height}` timestamps. Candidate endpoints
refreshed from the chains.cosmos.directory registry after the kickoff prompt''s
CRO candidates proved DNS-dead (rest.crypto.org, notional.ventures).

**Archive probe results (liveness + 365-day state-depth test):**
- CRO: `rest.mainnet.crypto.org` — PASS
- INJ: FAIL — all 7 registry candidates pruned (`no commit info found` /
  `version mismatch on immutable IAVL tree`). No free archive LCD exists.
- KAVA: `api.data.kava.io` (official archive) — PASS, but aggressive HTTP-420
  rate limiting; required 0.6–1.5 s call pacing + 15–45 s backoff retries and
  two retry passes to complete.
- SEI: FAIL — all 8 registry candidates pruned. **Two gateways
  (`sei.api.pocket.network`, `rest.cosmos.directory/sei`) are FAKE archives:
  they silently ignore the `x-cosmos-block-height` header and return live
  state.** Caught because "archive" bonded == live bonded digit-for-digit; the
  probe now hard-fails any node whose year-old bonded equals live bonded. This
  guard is load-bearing — without it SEI would have shipped a flat bogus series.

**State-decode (codec) boundaries — `invalid denom:` on older heights:**
- CRO: block store is complete back to genesis (2021-03-25) but staking state
  decodes only from ~2025-06 onward → 11 months built.
- KAVA: current chain kava_2222-10 restarted at height 1 on 2022-05-25 (older
  months have no blocks at all); state decodes only from ~2024-Q2 →
  26 months built. 2022-05..2024-03 permanently unavailable on this node.
- Binary search gained a guard: if the earliest stored block postdates the
  target month-end, the month is skipped (previously it would silently return
  block 1 and mis-attribute post-restart state to earlier months).

**Built (03_data/phase1/channel1_cosmos_lcd.csv, 37 rows):**
- CRO (3635, basecro/10^8): 11 months 2025-07-31..2026-05-31, ratio 0.309–0.370
- KAVA (4846, ukava/10^6): 26 months 2024-04-30..2026-05-31, ratio 0.091–0.127

**Cross-check (latest built month vs live pool):**
- CRO drift: 1.81% — PASS
- KAVA drift: 23.06% — WARN, investigated and explained: bonded was 99.1M at
  2026-06-30 and 103.1M at ~2026-07-14 vs 127.8M live (2026-07-28) — a genuine
  ~25M-KAVA staking surge in the two weeks before this session, not a
  denom/decimal error. Series trajectory is smooth and ratio bounded.

**Coverage label fixes:** coin_staking_type pos_possible → pos for CRO (3635)
and KAVA (4846). SEI stays pos_possible (nothing built); INJ was already pos.

**Environment note:** user-site pandas was found mid-upgrade-interrupted
(`~andas` remnant; `to_csv` ModuleNotFoundError, then full import failure) —
reinstalled clean (pandas 3.0.5); assemble + coverage builders ran unmodified.
The session builder writes its CSV via stdlib `csv` as defense.

**Post-assemble:** λ 13,510 → 13,547 asset-months / 463 → 465 assets.
Coverage 191 complete / 312 partial / 1,436 not_started.
Regression-ready 178 → 180 (coins 22 → 24: CRO + KAVA in; tokens/other 156
unchanged).

**INJ/SEI ch1 verdict:** blocked on archive state access, not on method.
Reopen only if a free archive LCD emerges or a dedicated indexer (paid) is
approved.

Output: 03_data/phase1/channel1_cosmos_lcd.csv
Builders: 04_code/session040_cosmos_lcd.py, 04_code/session040_kava_retry.py
Report: 03_data/SESSION040_COSMOS_LCD_REPORT.md

### Entry 92 — Session 041: HXRO moot (λ-on-observed); SXP ch2 built; OSMO ch1 (2 mo); gap closures
**Date:** 2026-07-30
**Spec section affected:** 3 (λ assembly — counts only); coverage semantics clarification.

**HXRO (3748) ch2 extend — NOT RUN, task moot under existing spec:**
The session-041 prompt premise ("checkpoint monthly: [] → fresh rebuild extends
to 2026-05") was a schema misread: streamed checkpoints store `rows`/`mblocks`
(24 months, 2020-09→2022-09, intact), not `monthly`, and the stream engine skips
any non-deferred checkpoint. The deeper blocker: HXRO's panel months are
`carried_forward` from 2022-10 onward (CMC top-1000 visibility lost; supply
frozen at 4.285e8, subtype presumed_failed per Entry 17) while TVL starts
2023-02. phase1_assemble_lambda.py computes λ on `status='observed'` rows ONLY
(core spec rule), so no ch2 rebuild can ever create λ∩TVL overlap for HXRO —
the observed window (→2022-09) and the TVL window (2023-02→) are disjoint.
**Decision:** zero Etherscan quota spent; HXRO stays partial as a PERMANENT gap
under current spec. Reopen only if Phase 3 changes the λ-on-observed rule for
carried-forward months (would affect 89,535 asset-months, not just HXRO).

**SXP (4279) ch2 — BUILT (chainid 1):**
Coverage flag `non-EVM/etherscan_reachable:no` was wrong — caused by the
unprefixed Multi-Chain address in asset_onchain_identity.csv. Probe confirmed
0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9 live on Ethereum: ABI OK, supply
285,368,788.7 (18 dec), getLogs clean. Fixed universe_lambda_channel_map.csv
(chain=Ethereum, etherscan_reachable=yes, ch2_holding=Transfer-log) and
identity (ethereum: prefix). Build: tf=569,311, getLogs=1,886, contracts
screened 10/96, 77 λ months (2019-09→2026-02), HODL-6m median 27.0% (B4 pass),
no B2 contamination warnings. λ∩TVL overlap 60 months (2021-03→2026-02).

**OSMO (12220) ch1 — BUILT, 2 months (archive floor 2026-04-02):**
Prompt's blocks/day=15,000 (~5.75 s/block) is STALE — Osmosis now produces
~73,300 blocks/day (~1.2 s/block; epochs-module anchors). All 16 chain-registry
REST endpoints + publicnode/ecostake/quickapi extras: pruned or fake.
osmosis.api.pocket.network is a FAKE ARCHIVE (ignores x-cosmos-block-height —
same landmine family as sei.api.pocket.network, Entry 91). Only real archive:
https://osmosis-api.noders.services, app-state + block floor ≈ h 58.44M =
2026-04-02 (apparent chain-wide post-upgrade state-sync point; an initial
"598-day retention" estimate was an artifact of the stale 15k blocks/day
constant). Built 2026-04-30 (h=60630953, ratio 0.2749) and 2026-05-31
(h=63027468, ratio 0.2630) via pool @ month-end blocks, binary-search
timestamps. Drift vs live 1.77% PASS. Denom uosmo / 10^6.
Output: 03_data/phase1/channel1_cosmos_osmo.csv (separate file, picked up by
the assembler's channel1_*.csv glob). coin_staking_type NaN → pos.
2021-06→2026-03 unreachable keyless; reopen only on a paid indexer (Numia/
Mintscan) decision.

**Permanent gap closures (no build path):**
CASINO (1573): Fantom chainid 250 — not in Etherscan V2 coverage, no free alternative.
RUNE (4157): THORChain — non-EVM, non-Cosmos; custom indexer required.
SUN (10529): Tron — ch2 engine not adapted for Tron; TronScan API deferred.

**Regression-ready semantics (recorded):** regression-ready = coverage
'complete' AND lambda_months > 0 (excludes the 11 pow_only coins complete on
NVT alone); 193 complete − 11 = 182.

**Post-assemble:** λ 13,547 → 13,626 asset-months / 465 → 467 assets.
Coverage 193 complete / 310 partial / 1,436 not_started.
Regression-ready 180 → 182 (coins 24 unchanged; tokens/other 156 → 158:
SXP + OSMO in).

Note: Etherscan Pro subscription lapsed after this session (2026-07-30 last
day). Remaining Etherscan-dependent work: none identified (HXRO moot, not
quota-blocked).

Output: 03_data/phase1/channel1_cosmos_osmo.csv; channel2_holding.csv 425 tokens / 13,799 rows
Builders: 04_code/session041_osmo_ch1.py
Report: 03_data/SESSION041_HXRO_SXP_OSMO_REPORT.md

---

### Entry 93 — Cowork 2026-08-04: Growth-Levelized NV/TVL adopted for token track

**Decision:** The token-track valuation anchor is NV/TVL_GL = MC / TVL*, replacing plain
NV/TVL, so both tracks carry a growth adjustment (user: "otherwise we miss the growth
metric completely"). TVL* uses the identical DCF machinery and PARAMS as PQ* (rf 4%,
MRP 30%, g_inf 3%, n=10, g cap [-50%,+200%], re_floor, beta36 vs BTC). Because TVL is a
stock (not a flow like PQ), TVL0 = trailing-12m AVERAGE month-end TVL (>=6 obs), g =
trailing 3y CAGR of TVL0 with 2y/1y fallback.

**Consequences:** NV/TVL_GL panel 111 assets / 3,125 mo (2021-01..2026-05). Token
regression sample 136/4,627 -> 101/2,771 (growth history requirement); combined panel
125 assets / 3,489 mo / $451B (19.0% of universe) at 2026-05. Raw NV/TVL retained in the
panel as robustness column. CAVEAT for Phase 3 robustness: 44.6% of regression
asset-months hit the g cap (mostly the -50% floor; median token TVL g = -33%/yr,
post-2021 DeFi contraction) — cap sensitivity must be checked.

Builder: 04_code/phase2_tvl_gl.py
Output: 03_data/phase2/nv_tvl_gl_panel.csv
Paper: Section 3.3 (TVL* equation), Table 1 funnel + Table 2 updated (commits 2b9ac26, 9308322).

### Entry 94 — Cowork 2026-08-04: Phase 3 empirical design fixed

**Decision:** Three-element test plan (user-specified): (1) H1/H2 via pooled panel
regressions with month + category FE, two-way clustered SEs, interaction + split-sample
for H2; FM secondary for tokens only (coin cross-section too thin at 11-20/month).
(2) H3 via Stars-minus-Avoid quadrant portfolio evaluated against self-built MONTHLY
analogs of the Liu-Tsyvinski-Wu (2022 JF) three-factor model (CMKT/CSMB/CMOM from our
own 1,939-asset universe; LTW original is weekly — deviation documented). (3) Horse race
vs raw NVT, Metcalfe (needs BitInfoCharts active-addresses build), MVRV (needs realized-
cap probe of ch2 checkpoints — NO new getLogs, Etherscan lapsed Entry 92), S2F, and
technical signals (momentum family, 52wk high, MA cross); panel + spanning + sub-period
designs. Full spec: 04_code/PHASE3_ANALYSIS_SPECIFICATION.md. Kickoff:
04_code/CLAUDE_CODE_PHASE3_KICKOFF_PROMPT.md (core = Tasks A-D; horse race = Phase 3b).

**Conviction variable resolution:** coins use ln-odds of raw ch1 staking share
(SoV/MoE = lambda/(1-lambda) requires a raw share, not the z-score index), lambda_z
fallback flagged; tokens use lambda_z. Standardization within class-month.

### Entry 95 — Session 043: Phase 3 core build decisions (Tasks A–D)

**Date:** 2026-08-04
**Spec section affected:** PHASE3_ANALYSIS_SPECIFICATION.md sections 1–4 (operationalizations
where the spec was silent). All decisions below were fixed BEFORE any regression output
was produced (honest-results clause).

**Sample membership (funnel gate):** coin sample = universe_coverage_status
coverage_status=='complete' AND lambda_months>0 AND asset_class=='coin' (the 24
regression-ready coins, incl. pos_possible + POL), month has non-missing lambda_z
AND positive NVT_GL. A naive coin_staking_type=='pos' filter yields 11/396 and does
NOT reproduce the paper funnel. Token sample = token rows of nv_tvl_gl_panel with
finite positive NV/TVL_GL and non-missing lambda_z. Gate verified EXACTLY (24/718,
101/2,771, medians match paper Table 2) before proceeding; assert() in phase3_panel.py.

**Return machinery:** monthly simple returns from universe_panel observed prices only,
consecutive calendar month-ends (a gap in observed status = NaN link; no backfill).
Cumulative t+1..t+3 / t+1..t+6 require ALL monthly links present. Regression dep
winsorized 1/99 at the monthly cross-section of the COMBINED panel (both tracks);
portfolios use raw returns (spec sec. 1).

**Variable operationalizations:** mom_3m = P_{t-1}/P_{t-4}-1 (months t-3..t-1);
mom_12_2 = P_{t-2}/P_{t-13}-1; r_1m = month-t return. Valuation ln-ratios winsorized
1/99 POOLED WITHIN TRACK before class-month standardization. conv_vw = equal-weight
mean of ch3 sub-channel z-scores (voting, delegation; each z-scored over all
asset-months with that channel, mirroring the composite lambda_z construction).
Sector FE: first ';'-tag of classification_table sector consolidated to 7 groups
(DEX, LendingCDP, Derivatives, Bridge, YieldStaking, Stables, Other) — 30 raw tags
over 101 tokens is too granular (many singletons).

**Median splits (H2 s5, H3 quadrants):** hi_conv = conv > class-month median;
lo_val = val <= class-month median (median asset goes to the cheap side). Split-sample
difference test = pooled spec-2 + high_val dummy + conv x high_val (controls NOT
interacted; conservative simple form).

**Portfolio evaluation:** turnover = 0.5*sum|w_t+ - w_t-| one-way per leg;
net-of-cost return = gross - (TO_star + TO_avoid)*cost_per_side. Sub-period rows
require >=12 months (coin pre-2023 rows absent: only 20 guard-surviving months, all
2023-05 onward). Sharpe = annualized mean/sd of (r - rf_m), rf_m = 4%/12.

**Small-cluster caveat (recorded):** coin track has 24 entity clusters; the split-sample
above-median t=-10.9 is not quotable — use the interacted difference test (t=-3.99).

**RESULTS (pre-registered ladder, no tuning):** H1a REJECTED at t+1 (coin conv t<=0.7
unconditional); H2 SUPPORTED for coins (conv x val = -0.0169, t=-3.54; split diff
-0.042, t=-3.99; +0.7%/SD in cheap coin-months vs -3.0%/SD in expensive); H1b weak
support (~+0.7%/mo per SD, t=1.5-2.3, strongest with sector FE / FM); H2 REJECTED for
tokens (interaction +0.003, t=0.8, wrong sign); voting-weighted lambda NOT better than
passive (710-month subsample, all t<0.6); H3 REJECTED (no SMA variant significant;
coin quadrant only 20 months after breadth guard excludes 45/65 class-months).
Monthly CMOM factor premium is NEGATIVE (-4.6%/mo, t=-1.6) — monthly analog deviation
from weekly LTW documented. Full readings: 03_data/PHASE3_RESULTS_REPORT.md.

Outputs: 03_data/phase3/{regression_panel,ltw_factors_monthly,portfolio_returns}.csv,
03_data/phase3/tables/{h1h2_coefficients,h1h2_fm_tokens,h3_alphas,h3_stats}.csv
Builders: 04_code/phase3_{panel,factors,regressions,portfolios}.py

### Entry 96 — Session 043: Phase 3b probes (E1 BitInfoCharts AA; E2 realized-cap)

**Date:** 2026-08-04
**Spec section affected:** PHASE3_ANALYSIS_SPECIFICATION.md section 5 (horse-race data builds).

**E1 — BitInfoCharts active addresses: FEASIBLE but ETH-only within the coin sample.**
Test coin ETH end-to-end: /comparison/activeaddresses-eth.html parsed with the existing
sentinusd Dygraph regex — 4,003 daily obs 2015-08-07..2026-08-04, monthly averaging
clean (raw HTML cached at 03_data/raw/bitinfocharts/activeaddresses_eth.html).
TRX/ADA/SOL return HTTP 200 STUB pages with zero data rows (checked explicitly —
page-exists is not series-exists). Of the 24 sample coins only ETH has a real series;
coverage is otherwise legacy PoW (BTC/LTC/DOGE/...). DECISION: Metcalfe cannot enter
the cross-sectional horse race; keep only as an ETH+PoW time-series baseline if
Phase 3b wants it (~10 pages, minutes of work).

**E2 — ch2 checkpoint realized-cap probe: NO for the coin track (MVRV dropped).**
Schema survey of all 428 files in 03_data/raw/phase1_onchain/holding/: 211 events-schema
checkpoints retain the FULL raw transfer list ([block, logidx, timestamp, from, to,
value]) — last-move attribution IS replayable locally with zero new API calls; 215
streamed-schema checkpoints store only monthly aggregate rows (hodl_6m/hodl_12m) +
mblocks — per-unit age state destroyed at stream time, unrecoverable (Etherscan lapsed,
no rebuild path). BUT the 24 regression coins have ZERO ch2 checkpoints of either kind
(ch2 covered EVM tokens; coin conviction is ch1 staking) — MVRV was specced as a COIN
comparator (spec 5.1) and is therefore infeasible regardless of schema. Token-side
overlap: 12 of 101 sample tokens events-schema, 80 streamed, 9 none. DECISION: MVRV
dropped from the horse race; a 12-token MVRV side-panel remains possible but too thin
as a comparator. No realized_cap.csv built.

### Entry 97 — Cowork 2026-08-04: EXPLORATORY token conviction-only sorts (user-directed, post-hoc)

**Context:** Moazzam observed that the token conviction signal is one-dimensional (H2
interaction dead) and asked for a pure high-conviction-minus-low-conviction token sort.
The session-043 comparator (median split EW) exists and fails (alpha +0.33%/mo, t=0.38).

**Finding (EXPLORATORY — run after seeing session-043 results, not pre-registered):**
sharpening the sort strengthens the signal monotonically, as a genuine linear signal
should: median EW t=0.38 -> tercile EW t=0.44 -> QUINTILE EW alpha +1.71%/mo t=2.18
Sharpe 1.01 (50 mo); quintile VW +3.11%/mo t=1.83. Post-2023: quintile EW +1.48%/mo
t=1.79 Sharpe 1.28 — the only portfolio variant so far that survives the sub-period.
Leg breadth ~9.4 tokens; leg turnover 0.18/mo -> 50bps/side cost drag ~36bps/mo (net
~+1.35%/mo EW). Median split dilutes the signal because information is in the extremes.

**Sector-neutral variant INFEASIBLE at current labels:** DeFiLlama compound category
strings are hyper-granular (median 1 token per sector-month; only 1.1% of sector-months
have >=3 tokens; only 7 tokens ever qualify). Requires coarse sector remap
(DEX/Lending/Yield/Derivatives/Other) before a within-sector signal can be built.

**Status:** exploratory, to be treated as hypothesis-generating. Confirmatory treatment
queued for Phase 3b: pre-specified quintile conviction sort (EW primary), spanning vs
momentum/reversal/52wk-high competitor portfolios, coarse-sector-neutralized version,
cost-adjusted, sub-periods. Script: 04_code/phase3_explore_conv_quintile.py.

### Entry 98 — Cowork 2026-08-04: Phase 3b design fixed (spec §8)

**Decisions (user-directed):** (1) Confirmatory conviction-only token sorts: quintile EW
primary, decile/tercile/VW secondary, factor alphas vs monthly LTW; exploratory origin
(Entry 97) must be disclosed in the paper. (2) Coarse sector remap {DEX, Lending, Yield,
Derivatives, Staking/LSD, Other} replaces raw DeFiLlama strings for token sector FE AND
enables sector-level tests. (3) Single-dimension by-sector alpha tests are powered
precisely BECAUSE the dead valuation dimension is dropped (double sort needs 4 joint
cells and fails when conv/val correlate; single sort needs 2) — sector-neutralized
full-breadth quintile primary, per-sector terciles for largest 2-3 groups as power
check. (4) Spanning against reversal/momentum/52wk-high/size long-shorts is the make-or-
break test given the strong token reversal (FM t=-3.4). Spec §8; kickoff
CLAUDE_CODE_PHASE3B_KICKOFF_PROMPT.md.

### Entry 99 — Cowork 2026-08-04: M1–M4 mechanism framework added to paper + spec §8.6

**Decision:** The coin/token H2 asymmetry (interaction strong for coins, dead for
tokens) is elevated from anomaly to mechanism section. Paper Section 2.3 gains "When
does conditioning bite?" — formalizes that Prop 2 requires cross-sectional variation in
delta and states four discriminating mechanisms: M1 attention-dependent absorption
(token premium should concentrate in small/low-turnover; conv x turnover < 0), M2 TVL
denominator endogeneity (interaction should revive under sector-demeaned valuation),
M3 growth-adjustment measurement (raw NV/TVL + cap-excluded), M4 seigniorage confound
(coin interaction must survive staking-yield controls — a THREAT to the coin result,
reported regardless of outcome). Spec §8.6 maps each to its test; 3b kickoff Task E
added. Preferred narrative if M1 holds and M2/M3 fail: single theory, two absorption
regimes — coins are the partially-priced corner, tokens the unpriced corner.

### Entry 100 — Session 044: Coarse sector remap rule (Task A, spec §8.1)

**Date:** 2026-08-04
**Rule (fixed before any 3b estimate):** raw DeFiLlama compound category strings split
on ';'; token assigned to the FIRST coarse group in priority order DEX > Lending >
Yield > Derivatives > Staking/LSD with >=1 matching tag; no match -> Other. Tag-level
case-insensitive keyword match: DEX = tag contains 'dex' (Dexs/DEX/DEX Aggregator);
Lending = contains 'lending' or tag=='CDP'; Yield = contains 'yield' or 'farm';
Derivatives = contains 'derivatives'/'options'/'perpetuals'; Staking/LSD = contains
'staking' (Liquid Staking, Staking Pool, Restaking). Literal reading of spec §8.1
"priority-ordered". Documented consequence: perp/derivative DEXes carrying any DEX tag
(GMX, PERP, SNX, dYdX-v3-with-DEX-tag) land in DEX; only pure-derivatives strings land
in Derivatives (6 tokens). Counts over 101 tokens: DEX 41, Other 21, Lending 16,
Yield 15, Derivatives 6, Staking/LSD 2; median names/group-month DEX 25, Other 9,
Lending 8, Yield 7, Derivatives 3, Staking/LSD 1. Largest-3 groups for per-sector
tests: DEX, Other, Lending (Other is the residual grab-bag; noted in report).

**Result (Task A second half):** token ladder with coarse-sector FE ATTENUATES the
conviction slope vs the 043 raw-7-group FE (s6_1 +0.0071 t=2.30 -> +0.0063 t=1.95;
s6_2 t=1.93 -> 1.49; s6_3 t=2.01 -> 1.60; s6_4 t=1.93 -> 1.52); interaction dead under
both. Part of the token conviction premium is between-coarse-sector. raw7 columns
reproduce session 043 exactly (machinery check). Builders phase3b_sector_map.py +
phase3b_regressions_coarse.py; outputs sector_coarse_map.csv,
tables/sector_coarse_sizes.csv, tables/h1h2_sector_fe_comparison.csv.

### Entry 101 — Session 044: horse-race signal operationalizations + race results (Task C, spec §5/§8.3)

**Date:** 2026-08-04
**Operationalizations (fixed pre-run):** raw_val = ln(raw NVT)=ln(MC/PQ0_annual) coins
/ ln(nv_tvl_raw) tokens, winsorized 1/99 within track (mirrors GL val treatment). S2F
dual build: s2f_ln = ln(circ_supply / trailing-12m Dsupply) only where flow>0 (literal
spec; 83% coin / 75% token coverage), plus supply_g12 = 12m supply growth (defined
everywhere incl. deflationary months, monotone-inverse of S2F) used in the JOINT race.
high52 = price / rolling-12m max (>=6 obs, George-Hwang). ma_cross = 1[MA3>MA10]
monthly closes, full windows. Momentum family from the 043 panel. All standardized
within class-month. Builder phase3b_signals.py -> horserace_signals.csv.

**Results:** (a) Panel race — COIN: no single comparator significant full-sample; the
H2 interaction added to the full joint spec survives everything: conv x val = -0.0176
(t=-2.83); sub-2024 -0.0104 (t=-1.92) with 52wk-high the strongest coin signal
(+0.044, t=3.12) and supply growth significantly NEGATIVE (scarcity-positive). TOKEN:
conv single +0.0064 (t=1.97) but attenuates to +0.0032 (t=1.10) in the joint race;
only reversal survives jointly (r_1m -0.0166 t=-2.46; sub-2024 -0.0267 t=-3.95).
Claim boundary recorded: token conviction is a portfolio-extremes phenomenon, not a
robust linear panel slope. (b) Spanning both directions: q5_ew alpha survives every
single-competitor control (+1.53% to +2.53%/mo, t 1.85-3.18); the ltw+all (n=28) and
ltw+macross (n=31) cells are underpowered (macross_ls needs 10m MAs + min-3 binary
legs) — reported, not treated as refutations. No competitor LS earns positive alpha on
LTW+q5. (c) sub-2024 rows all reported. Metcalfe DESCRIPTIVE only: 7 real BitInfoCharts
AA series (BTC/ETH/LTC/DOGE/BCH/DASH/ETC); ZEC = stub (0 rows); NEW LANDMINE: unknown
tickers ('btg') redirect HTTP-200 to the DEFAULT btc-ltc-eth comparison chart — the
Dygraph regex happily parses the BTC series; page-title guard added to
phase3b_metcalfe.py. BTC Metcalfe mean-reversion t=-3.69 (own-asset, full-sample z,
look-ahead acknowledged). Outputs tables/horserace_{panel,spanning}.csv,
metcalfe_panel.csv, tables/metcalfe_summary.csv.

### Entry 102 — Session 044: confirmatory conviction-only token sorts (Task B, spec §8.2)

**Date:** 2026-08-04
**Design as pre-specified** (quintile EW min-3 primary; decile/tercile/VW secondary;
sector-neutral quintile via coarse-sector demeaning n>=3 else class-month; per-sector
terciles for DEX/Other/Lending; coin tercile analog; NW-3 alphas vs monthly LTW;
pre/post-2023; 25/50bps; turnover; spanning vs identically-built r_1m / mom_3m /
52wk-high / size quintile long-shorts). Builder phase3b_sorts.py.

**RESULTS (Entry 97 exploratory quintile now confirmed within battery — paper must
disclose origin):** q5_ew alpha +1.71%/mo t=2.18 (exact match to Entry 97), net-50bps
+1.53% t=1.95, post-2023 +1.48% t=1.79, Sharpe 0.86, ~10.6 names/leg, turnover
0.19/0.16 per leg. SPANNING (make-or-break): alpha STRENGTHENS with reversal control
(+2.53%, t=3.18; rev_ls loading +0.18 — high-conviction leg tilts to recent winners,
and winner-minus-loser has alpha -4.68% t=-3.02) and stays +2.34% (t=2.60) vs all four
competitors. Conviction is NOT repackaged reversal. HONEST LIMITS, equal prominence:
(1) decile DIES (t=0.02, ~5.8/leg) — the "sharper sorts monotonically strengthen"
narrative does NOT extend past quintiles (progression: median 0.38, tercile 0.37,
quintile 2.18, decile 0.02); (2) sector-neutral quintile DIES (t=0.39, post-2023
negative) — premium is between coarse sectors; (3) per-sector terciles all null
(DEX t=0.89, Other t=-0.77, Lending t=-0.16) — the by-category power test fails;
(4) coin tercile analog flat (t=0.16); (5) q5_vw bigger but noisier (+3.11%, t=1.83).
Outputs conv_sort_returns.csv, tables/convsort_{alphas,stats,spanning}.csv.

### Entry 103 — Session 044: ve/plain + fee/nofee classification of the 101 tokens (Task D 2-3)

**Date:** 2026-08-04
**Rules:** ve_lock='ve' iff governance power or the primary staking/value-accrual
mechanism requires time-locking/escrow/bonding (veToken, fixed-term locked staking,
bonded node/validator stakes); cooldown-only modules (stkAAVE) and unstake-anytime
staking = 'plain'. fee_share='fee' iff protocol fees/revenue accrue to holders/stakers
via distribution, revenue-funded rewards, or systematic buyback/burn. DOMINANT-REGIME
rule for mid-sample changes (BAL -> veBAL 2022-03 = ve; UNI = nofee, UNIfication burn
only from ~2025-11; AAVE = nofee, buybacks only 2025-04+; CAKE = ve via 2022-04 locked
staking + 2023-04 veCAKE; 1INCH = ve via 2022-12 st1INCH Fusion locks; PENDLE = ve from
2022-11). Classified from official protocol documentation (docs domain recorded per
token in the CSV); 32/101 flagged low-confidence and the split regressions re-run
excluding them. Identity note: cmc 8615 EPIC = Ethernity Chain (ERN rebrand), NOT an
'Epic' protocol. Counts: ve 31 / plain 70; fee 66 / nofee 35. Output
token_gov_classification.csv (cmc_id, ve_lock, fee_share, confidence, source, note);
builder phase3b_gov_classification.py.

### Entry 104 — Session 044: heterogeneity batch results (Task D, spec §8.4 — run all, report all)

**Date:** 2026-08-04
**(1) Delta-lambda (conv_lz diffs, consecutive-month guard):** nothing. Token
levels+changes: d1m +0.0033 t=0.88, d3m +0.0060 t=1.31 (conv level attenuates
alongside); coin negative insig. Quintile sorts on changes: d1m alpha +1.33%/mo
t=1.11, d3m +0.53% t=0.34.
**(2) ve split REJECTED — wrong direction:** ve conv slope +0.0016 (t=0.21) vs plain
+0.0047 (t=1.21); pooled conv x ve = -0.0023 (t=-0.27); excluding low-confidence
-0.0120 (t=-0.94). The costly-lock prediction fails; premium sits in plain tokens if
anywhere. **(3) fee split: no difference** (fee +0.0052 t=0.94 vs nofee +0.0056 t=0.87;
interaction -0.0005 t=-0.05). Caveat recorded: between-token test, weak vs the model's
within-token b_t comparative static. **(4) size terciles flat (t 0.32-0.51); turnover
terciles TILT WRONG WAY** (lo t=0.36, mid 0.55, hi 1.41) — limits-to-arb prediction not
supported. **(5) regimes:** token slope symmetric bull/bear (t=1.44/0.96); coin
interaction concentrated POST-2023 (-0.0205, t=-4.32; pre-2023 flips sign on 74 obs —
uninterpretable) and mildly bull-tilted (-0.0241 t=-1.83 vs -0.0088 t=-0.98).
**(6) measurement:** coin interaction robust to MRP 20/40 (-0.0175/-0.0163, t=-3.55/
-3.54; PQ*/TVL* re-derived from emitted pq0/tvl0+g+beta, re_floor 5%) and STRONGER
ex-conv-fallback (-0.0181, t=-4.67); but RAW NVT shrinks it to -0.0060 (t=-1.90) and
dropping g-capped months (40% of the coin panel!) keeps magnitude (-0.0163) but kills
significance (t=-0.97, n=406). Growth-levelization is load-bearing — caveat goes next
to the headline t=-3.5 in the paper. Token interaction dead in every variant; token
conv slope stable (+0.005..0.008), significant only ex-B4 (+0.0078, t=2.08; B4 =
screened HODL-6m>80% from channel2_holding, tokens only — coins have no ch2). Builder
phase3b_heterogeneity.py; outputs tables/heterogeneity.csv, tables/het_portfolios.csv.

### Entry 105 — Session 044: mechanism discrimination M1–M4 verdicts (Task E, spec §8.6)

**Date:** 2026-08-04
**M4 staking-yield construction (new):** yield ~= trailing-12m issuance rate / staked
share = supply_g12 / logistic(conv), coin ch1_lnodds months only (logistic(conv)
recovers raw lambda_ch1 exactly on those rows), winsorized 1/99 within track,
class-month standardized. Approximation logged: 12m TRAILING supply growth proxies
current issuance; no forward-looking or protocol-schedule data used.

**VERDICTS (report table section 5):** M1 attention NOT SUPPORTED — conv x turnover
POSITIVE (+0.0069, t=+1.21) and D4 gradient larger in HIGH-turnover tokens (wrong sign
for the prediction). M2 REJECTED — token interaction with coarse-sector-demeaned
valuation stays positive (+0.0056, t=+1.27); sector-neutral-val quadrant portfolio
alpha +1.50% t=1.18 n.s. M3 REJECTED (= good news for the theory reading) — token
interaction ~0 under raw NV/TVL (+0.0002, t=0.05) and ex-g-cap (-0.0024, t=-0.54): the
token-H2 null is NOT a measurement artifact. M4: COIN RESULT SURVIVES — conv x val =
-0.0188 (t=-4.39) with staking-yield level and interaction included (conv x sy
-0.0163, t=-1.58 n.s.): not a seigniorage/b_t artifact. CONSEQUENCE FOR THE PAPER: the
intended "M1 supported + M2/M3 rejected" narrative loses its M1 leg; Section 2.3 must
reframe (evidence pattern = between-sector, high-turnover, extremes-only -> sector-
level repricing of governance value rather than individual-token attention neglect).
M4 is the session's best defensive result. Outputs tables/mechanisms.csv.

### Entry 106 — Cowork 2026-08-04: Full results written into paper (Sections 5, 6, abstract, intro, conclusion)

Results (5.1-5.5): coin ladder + token ladder tables; H2 asymmetry as central result;
H3 power-limited null; token quintile battery with Entry-97 disclosure paragraph and
full median->decile progression; spanning table (reversal-distinct); horse race
summary (coin interaction survives battery at t=-2.83; token slope attenuates to
t=1.10; token conviction = portfolio-extremes claim). Robustness (6.1-6.3):
measurement table with BOTH coin caveats (raw-NVT attenuation t=-1.90; g-cap subsample
t=-0.97) at equal prominence; M1-M4 verdict table with M1 wrong-sign reported and the
between-sector reframe offered as interpretation-not-tested-mechanism; heterogeneity
nulls incl. ve-prediction rejection. Abstract + intro findings rewritten to
conditional-for-coins / extremes-for-tokens. Conclusion drafted. 37 pp. Moazzam to
review and prune tests for the final table set.

### Entry 107 — Cowork 2026-08-04: DCF misattribution fixed; P/F comparator added (spec §8.7)

Moazzam challenged the intro's claim that DCF dominates the academic literature. He is
right: pagnotta2022/biais2019 are equilibrium models, liu2021risks is factor lit. Intro
para 1 recast as equilibrium (academic) vs DCF/fee-multiple capitalization (applied).
Consequence: the horse race must include the implementable DCF version. §5.1's
"fee multiples are paid-data" was WRONG — DeFiLlama fees endpoints are free/keyless.
Spec §8.7 adds P/F and P/F_GL (same F* machinery) for tokens and coins, coverage-
matched re-estimates, spanning vs conviction quintile, and the P/F-as-valuation
interaction spec (cleanest remaining M2 test: fee denominator is not mechanically
price-linked the way TVL is). To run as a short Phase 3c session. NOTE: does not
conflict with Entry 30 (fees rejected as OUR PQ measure); fees here are the
competitor's fundamental.

### Entry 108 — Cowork 2026-08-04: Size (normalized MC) as model-free delta proxy (user-requested robustness)

**Question (Moazzam):** is the token H2 failure a NV/TVL measurement issue? Test with
simple normalized market cap as the delta measure (big = more visible = more priced).

**Tokens:** conv x size = +0.0003 (t = 0.07) — nothing. Size-median split: small
+0.0014 (0.32), LARGE +0.0101 (1.67) — direction WRONG for a delta story (premium sits
in large tokens, echoing the M1 wrong-sign turnover result). Verdict: the token H2
null is NOT about the TVL denominator; even the model-free delta proxy shows no
conditioning. Remaining measurement candidate: fee-anchored P/F denominator (spec 8.7).

**Coins (new fact):** conv x size = +0.0329 (t = 2.21). Conviction premium is NEGATIVE
in small coins (-0.0323, t = -1.89), mildly positive in large. With BOTH interactions,
conv x val survives attenuated (-0.0134, t = -1.96) alongside conv x size (+0.0314,
t = 2.17); corr(val,size) = -0.10 so they are near-orthogonal conditioners. Reading:
high staking in SMALL coins is a negative signal (yield-trap/dead-float candidate
interpretation — small chains advertise extreme staking APRs), independent of the
valuation-conditioning effect. Coin H2 keeps 10% significance in the toughest spec yet.

Script: 04_code/phase3_explore_size_delta.py. Paper: added to Section 6.1.

### Entry 109 — Cowork 2026-08-04: Phase 3c scoped tokens-only; kickoff written

Moazzam directed the fee/revenue DCF comparators to TOKENS ONLY (coins dropped from
§8.7: chain fees are a toll, not a holder claim — Entry 30 logic). Two measures:
P/F = MC/trailing-12m fees (practitioner multiple) and prev_gl = MC/REV* (revenue DCF,
same PARAMS as PQ*/TVL*; revenue preferred over fees as DCF base). Core question,
stated as C1 in the kickoff: does the token H2 interaction revive with a fee-anchored
valuation denominator (which, unlike TVL, is not mechanically price-linked)? This is
the sixth and final measurement candidate for the token conditioning null; Entry 108's
five prior conditioners all failed. Coverage-matched baselines required so denominator
and sample effects are separable. CLAUDE_CODE_PHASE3C_KICKOFF_PROMPT.md.

### Entry 110 — Cowork 2026-08-04: Technical battery completed (spec §8.8, 3c Task D)

Five signals added to the horse race: ma_dist (continuous MA-distance, SUPERSEDES
binary MA-cross — fixes the 28-31-month underpowered spanning cells of session 044),
vol12, ivol (36m vs CMKT), amihud (|r|/volume_24h snapshot proxy — caveat logged),
skew36 (lottery proxy). Rationale: vol/skew are the last plausible spanners of the
token conviction quintile; amihud completes the limits-to-arbitrage race; monthly
RSI/MACD/Bollinger excluded as transformations of the included set; daily-native
signals (MAX, true RSI) excluded for data-depth reasons — both exclusions get one
justifying sentence in the paper. Runs inside session 045 (Phase 3c).

### Entry 111 — Session 045: DeFiLlama fees/revenue panel built (Phase 3c Task A)

**Date:** 2026-08-04
**Endpoints verified live:** `api.llama.fi/summary/fees/{slug}?dataType=dailyFees|
dailyRevenue` (daily [ts, usd] chart; HTTP 400 = no adapter exists) and
`/overview/fees` (2,288 protocol + 237 chain adapters). Parent slugs accepted by
/summary even when the overview lists only version children (uniswap, curve-finance,
compound-finance etc. all resolve) — the overview listing is NOT authoritative for
what /summary accepts; live probe per slug is.

**Identity rule:** cmc_id -> dl_slug from tvl_panel.csv (the map actually used in the
NV/TVL build), 1:1 on all 101 sample tokens. The 4 chain-level TVL tokens (ARB,
METIS, APE, BLAST) get the DL CHAIN fee adapters (arbitrum/metis/apechain/blast,
verified live), flagged `chain_level_sequencer_fees` — L2 sequencer fees accrue to
the DAO (a holder claim), unlike the L1 validator toll rejected in Entry 30/109;
consistent with their chain-level TVL precedent (Entries 68/84). METIS and APE have
no chain revenue adapter (400) — fees only.

**Coverage:** 55/101 tokens with fees, 51/101 with revenue; median 44 months per
covered token; starts 10 pre-2021 / 13 in 2021 / 32 in 2022+. Fees-without-revenue:
METIS, APE, RBN, MAV (no revenue adapter), 10 more tokens with shorter revenue than
fee windows. Monthly sum by calendar month (universe month_end convention);
incomplete trailing month dropped; n_days kept as diagnostic.

**Probed-and-REJECTED slug resolutions** (house conservatism — fees slug must equal
the TVL identity slug or its chain mapping): `metronome` (MET, real parent match but
fees start 2023-01 vs MET regression window ending 2023-06 -> zero usable DCF months);
`rari` (= Rarible RARI, NOT Rari Capital RGT — collision); `nerve` (2024-09 start,
wrong-protocol risk vs nerve-staking); `aurora` (chain adapter; AURORA's TVL identity
is protocol-level aurora-plus; chain-toll logic applies); `bounce.tech` (2026-01
start, 0 usable regression months); `thundercore` (1 day of data). All other misses
are genuine 400s (augur, loopring, hashflow, biconomy, aevo-perps, flexa, ...).
**Known limitation:** DL `dydx-v3` fees cover only 2023-11..2024-10 (the wind-down),
missing the 2021-22 v3 fee peak — ETHDYDX under-covered.

Raw cache 03_data/raw/phase3c/fees/ (202 files); builder phase3c_fees_panel.py;
outputs fees_revenue_panel.csv (2,437 rows) + tables/fees_coverage.csv.

### Entry 112 — Session 045: P/F and prev_gl comparator construction (Task B)

pf = MC / trailing-365D fee sum (>=6 monthly obs — PQ0 house convention). prev_gl =
MC / REV* and pf_gl = MC / F* via the EXACT phase2_nvt_gl.py pq_star machinery and
PARAMS (rf 4%, MRP 30%, g_inf 3%, n 10, g cap [-50%,+200%] flagged, beta36 from the
regression panel, r_e floor 5%); base = trailing-12m revenue (fees); g = trailing 3y
CAGR of the base, 2y/1y fallback, window recorded. ln, winsorized 1/99 pooled within
track, standardized within token-month (mirrors the val treatment).

Coverage on the 2,771 token asset-months: pf 1,367 (51 tokens), pf_gl 1,178 (44),
prev_gl 976 (35); 202 pf_gl-only rows (13 tokens) where fees exist but revenue does
not — the flagged variant of the kickoff. prev_gl needs >=1y of prior base history
for g, so its months are effectively 2023+. Sanity: median P/F 12.1, median prev_gl
23.0; corr(ln P/F, raw ln NV/TVL) = 0.48, vs GL 0.32, vs size -0.06 — distinct axis.
Builder phase3c_comparators.py; output fee_comparators.csv.

### Entry 113 — Session 045: C1 VERDICT — token H2 null survives the sixth (fee-anchored) measurement candidate; P/F is a real token panel signal

**C1 (the session's core question):** token s4 with val = ln P/F: conv x val =
-0.0024 (t = -0.45), n = 1,282/49 tokens. With val = ln prev_gl (primary DCF):
-0.0035 (t = -0.31), n = 915/33. pf_gl variant: +0.0060 (t = +0.73). First time in
six conditioners the SIGN goes the H2 way and splits order correctly (P/F cheap
+0.0085 vs expensive +0.0023; prev_gl +0.0050 vs -0.0096) — but s5_diff t = -0.89 /
-0.87: a null. Coverage-matched NV/TVL_GL baselines on the SAME subsamples equally
dead (+0.70 / -0.80) -> no denominator effect; the prev_gl-subsample TVL interaction
going negative is sample composition, not measurement. **PAPER CLAIM NOW AVAILABLE:
the token conditioning null survives TVL-raw, ex-g-cap, sector-demeaning, size,
turnover, AND fee/revenue anchoring — it is a fact about tokens, not measurement.**

**New horse-race fact:** ln P/F is the first valuation signal to work in the token
panel — singles -0.0103 (t = -2.50) full / -0.0148 (t = -2.70) sub-2024; level term
in s4 -0.0119 (t = -3.21); survives the completed joint battery (-0.0090, t = -2.32)
where raw NV/TVL never did. The DCF transform DESTROYS it (prev_gl t = -0.42, pf_gl
t = -0.68) and the quintile portfolio earns nothing (-0.18%/mo, t = -0.10 at ~5-6
names/leg; post-2023 +1.15%, t = 0.85) — a panel-level, not extremes, phenomenon
(mirror image of conviction). Conviction's joint slope is unchanged by the fee
column on the P/F subsample (+0.24 -> +0.19 t). CAVEAT logged: on the revenue-covered
subsample (33 tokens, ~2023+) the conviction slope flips negative (-0.0124,
t = -2.01) BEFORE any fee variable enters — composition, reported in the report
headline. Neither fee comparator spans the conviction quintile (q5 alpha +1.22%
t = 1.67 on pf months, +1.54% t = 1.84 on prev_gl months; direction 2 alphas null).

### Entry 114 — Session 045: technical battery results (Task D) — conviction quintile SURVIVES the completed battery; 044 MA-cross cells superseded and resolved

Signals built from universe_panel only (phase3c_technicals.py): ma_dist (px/MA10-1),
vol12 (>=8 obs), ivol (36m resid SD vs CMKT, >=12), amihud (ln trailing-12m mean
|r|/volume_24h, >=6 obs — **CAVEAT: volume_24h is a month-end SNAPSHOT, not a monthly
aggregate; noisy proxy**), skew36 (>=18 obs). Returns clipped (-90%, +300%) before
moments (phase2 beta-build convention). Coverage 90-100% per track.

**Token spanning verdict (the key question):** q5_ew conviction alpha vs LTW + the
COMPLETED 12-long-short battery = **+1.74%/mo (t = 2.45, n = 43)**; + both fee LS =
+2.17% (t = 2.82, n = 35). The two underpowered session-044 MA-cross cells are
SUPERSEDED by continuous ma_dist and RESOLVED in conviction's favor: +all cell
+0.99% (t = 0.99, n = 28) -> +1.66% (t = 2.73, n = 43); single-MA cell +1.09%
(t = 1.16, n = 31) -> +1.83% (t = 2.46, n = 50). Vol/skew (the Entry-110 candidate
spanners) do not span. Direction 2: no competitor earns alpha on LTW + q5. None of
the five technicals earns a significant token long-short on its own; ma_dist singles
are the only significant token panel cell (-0.0120, t = -2.21 — momentum-adjacent
negative, like the 044 reversal family).

**Coin track:** conv x val survives the completed battery: -0.0235 (t = -2.68) full,
-0.0188 (t = -3.17) sub-2024 (044 eight-comparator figure was -2.83). Amihud is the
strongest new coin single (-0.0223, t = -2.65; sub-2024 -3.23; illiquid-coin
discount), vol12/ivol also significant sub-2024; none touches the interaction.
Joint-race construction note: ma_cross REPLACED by ma_dist in the completed joint
set (supersession, not addition). Exclusions sentence for the paper (monthly
RSI/MACD/Bollinger redundant; daily-native MAX/RSI infeasible at free-tier depth)
drafted in PHASE3C_RESULTS_REPORT.md section 6.

### Entry 115 — Cowork 2026-08-04: Phase 3c results written into paper

Per PHASE3C_RESULTS_REPORT §7: (1) Section 6.1 — fee-anchored rows added to
measurement table; six-conditioner definitive statement ("the conditioning failure is
a fact about tokens, not about measurement"); sign-flip-but-null reported honestly;
revenue-subsample conviction sign flip (-2.01) as external-validity note. (2) Section
5.5 — completed 12-comparator battery (coin interaction -2.68/-3.17); P/F as the one
working token valuation comparator (panel level -2.32 joint, no portfolio translation,
DCF transform kills it); "growth-levelization helps throughput flows, hurts cash
flows" framing; exclusions footnote (RSI/MACD/Bollinger redundant; daily-native
infeasible; amihud snapshot caveat; fee coverage 55/101). (3) Spanning table upgraded
to completed battery incl. supersession note for 044's underpowered MA-cross cells
(now +1.66%/t=2.73 and +1.83%/t=2.46 with continuous ma_dist); completed battery
+1.74% (t=2.45); +fees +2.17% (t=2.82). (4) Intro: one sentence on P/F beating its
own DCF refinement. 39 pp, clean compile. Ready for Moazzam's table-pruning review.

### Entry 116 — Cowork 2026-08-04: Alternative-valuation results made visible; H3 re-run under P/F and REV* (user-directed)

Moazzam flagged that the 3c results were prose-only. Added to the paper: (1) Table
horserace — full signal-by-signal race, both tracks, singles + joint rows; (2) Table
altport — every alternative signal as a token quintile long-short (all null) vs the
conviction quintile reference; (3) Table h2altval — the H2 interaction spec under
NV/TVL_GL / ln P/F / ln MC/REV* side by side with split-samples and coverage-matched
baselines. (4) NEW RUN (inline, phase3_explore_h3_altval.py): H3 quadrant re-formed
with fee-anchored valuation axes. Verdict: still null under all three measures —
P/F quadrant +1.67%/mo alpha, Sharpe 0.82, but t=1.35 (46 mo) and DEAD post-2023
(t=0.07); REV* quadrant negative (-1.89%, t=-1.24, 31 mo, 33 excluded by breadth
guard); coverage-matched NV/TVL_GL baseline t=0.68. Two-dimensional portfolio adds
nothing over the conviction quintile under ANY valuation measure. Paper 42 pp.

### Entry 117 — Cowork 2026-08-05: DEX-only conviction quintile (user-prompted exploratory)

Moazzam asked whether the within-sector null was a power issue and whether per-sector
QUINTILES were ever tested. They were not (only terciles; Entry 100/session 044).
DEX is the only coarse sector deep enough (39 tokens, median 25/month). Result:
DEX-only conviction quintile EW = +3.48%/mo raw, +3.37%/mo LTW alpha, t = 2.04,
46 months, ~4.6 names/leg. DEX tercile confirms 044 (t = 0.62). VERDICT: the
within-sector "null" was tercile dilution + thin-sector noise in the pooled
sector-neutral construction, NOT absence of within-sector signal. The premium is
present WITHIN the deepest sector at fine granularity; other sectors untestable at
quintile granularity. The "between-sector repricing" mechanism framing (Entry 105 /
paper 6.2) must be qualified accordingly. EXPLORATORY (user-prompted, post-hoc) —
disclose like Entry 97. Script: 04_code/phase3_explore_dex_quintile.py.

### Entry 118 — Cowork 2026-08-05: VW spanning + P/F quadrant VW (user questions)

(1) Why EW primary: pre-registered in spec 8.2 before results; better precision
(t 2.18 vs 1.83); VW 10-name legs concentrate in 1-2 large tokens. NEW: VW quintile
does NOT survive the 12-battery spanning — inline identical-construction comparison:
EW +1.36%/t=1.67 vs VW +0.97%/t=0.86 (inline battery replicates 045's EW cell at 1.67
vs official 2.45 — construction detail differences; the EW-vs-VW comparison under
identical construction is the informative one). VW's role in the paper = microcap-
robustness sentence only. (2) H3 quadrant with P/F valuation, VW variant: +2.05%/mo,
t=1.05, Sharpe 0.64 (EW was +1.67%/t=1.35, Entry 116) — best quadrant point estimates
in the paper, never significant; two-dimensional construction fails under fee-anchored
valuation in both weightings. Script: 04_code/phase3_explore_vw_checks.py.

### Entry 119 — Cowork 2026-08-05: Pruning batch 1 executed (Moazzam's directives)

(1) Hypotheses UNIFIED: H1/H2/H3 stated once for both classes in new 2.4 "Testable
Hypotheses"; per-class Prop 1a/1b/H1a/H1b/Prop 2 removed; 2.1/2.2 end with
measurement-mapping sentences. (2) Voting-weighted refinement removed from hypotheses,
results, and scorecard. (3) Token significance prose CORRECTED everywhere: significant
only alone (t=1.97) and in FM (1.77/2.19); t~1.5 with controls (prior "1.9-2.0 with
sector FE" was stale raw7-FE numbers). (4) M1-M4 moved from theory 2.3 to 6.2 with
postulate-then-test framing (mechanisms arose from results — honest learning-process
narrative); 2.3 keeps only the delta-variation qualification. (5) Disclosure reworded
(no "author-directed"). (6) Table restructure: horse race = joint multivariate table
(all coefficients, N, assets, R2-within 0.032/0.023); singles grid -> Appendix B;
Tables 7+9 MERGED (own-alpha column + q5-survival column; own alphas for
rev/mom/high52/size computed inline, reversal replicates official -4.68/-3.02
exactly); Table 10 (h2altval) -> Appendix B; quadrant pooled rows dropped.
(7) 4.2 funnel prose condensed (~1.4k chars). (8) 5.4/6.2/scorecard updated with
Entry-117 DEX-quintile finding (between-sector framing qualified) and Entry-118 VW
microcap sentence. 5.5 rewritten around three learnings (incrementality; coin
cross-section info-free at level; P/F partial vindication with DCF twist).

### Entry 120 — Cowork 2026-08-05: Proper summary statistics table (Moazzam's request)

Old Table 2 was a coverage table, not summary stats. New Table 2: distributions
(N/mean/SD/p10/p25/median/p75/p90) of main variables by track. Coins: staking share
(median 38.6%), SoV/MoE (median 0.63), NVT_GL, MC, forward return, beta. Tokens:
lambda_z, NV/TVL_GL, TVL, P/F (median 12.1), MC, forward return, beta. Unwinsorized;
heavy-tail note motivates the log/winsorization choices; negative median returns
flagged. Old coverage table -> Appendix (tab:coverage_appendix). Builder:
04_code/phase3_sumstats_table.py.

### Entry 121 — Cowork 2026-08-05: Review-round edits (Moazzam's six points)

(1) Delta-uniformity statement rewritten to distinguish levels: between-class variation
absorbed by class-separate estimation (surfaces as different avg premiums); between-
sector-within-class detectable in principle; full degeneracy only if uniform across the
estimation cross-section. (2) 4.2: appendix list references + survivorship paragraph
(universe snapshot-based/survivorship-free; regression samples have a coverage tilt
toward scale/longevity, not conditioning-on-survival). (3) 5.1: FM-vs-panel divergence
explained (FM includes same controls, full cross-section monthly; equal month-weighting
upweights the strong pre-2023 premium; asset clustering absorbs lambda persistence) —
slope significance is estimator-sensitive because the premium is time-varying.
(4) NEW RUN: coin quadrant guard relaxation — min3: -2.7%/mo (t=-1.36, 33 mo); min2:
-1.5% (t=-0.79, 46 mo); negative at every threshold; footnote added, "mechanical"
framing softened to "robust to guard, poorly powered at every setting". (5) Tercile-
dilution sentence removed from DEX passage per Moazzam (quintile already established
as the instrument); passage now leads with thin-category-demeaning noise + DEX
within-sector quintile; between-vs-within left explicitly unsettled. (6) NEW RUN +
Table (tab:channels): token conviction by channel — HODL-6m carries essentially all
signal (slope t=1.50, 88 tokens; q5 alpha +1.48%/t=1.71) vs staking/delegation/voting
individually uninformative on 9-32 tokens; composite edge = governance increment;
"revealed patience, not governance participation" reading; disclosed as review-stage.
Script: 04_code/phase3_explore_channels_guard.py. Paper 51 pp.

### Entry 122 — Cowork 2026-08-05: Figures added; working-paper ordering finalized

Two figures created (04_code/phase3_figures.py -> 05_paper/figures/):
Fig 1 two-panel — (A) coin mean next-month returns by conviction-valuation cell (the
H2 asymmetry visually: Star cell positive, high-conv/expensive lowest); (B) token mean
returns by conviction quintile (extremes concentration). Fig 2 — cumulative log return
of the token conviction quintile LS vs EW token universe (LS accumulates while
universe loses value; LS series replicates official mean +2.28%/50mo exactly).
Document order restructured via endfloat[tablesfirst] + processdelayedfloats after
Conclusion: text (1-34) -> Tables 1-12 (36-47) -> Figures 1-2 (48-49) -> References
(50-51) -> Appendices A-C with their tables (52-60). 60 pp. NEXT: introduction +
abstract rewrite (Moazzam: agree the one-sentence headline claim first).

### Entry 123 — Cowork 2026-08-05: Introduction rewrite, iteration 1 (Moazzam's directives)

(1) lambda front-loaded as THE contribution: new paragraph 2 bridges QTM with
Cong-Li-Wang (2021) and Sockin-Xiong (2020) via the conviction measure — "the models
supply the valuation object; lambda supplies the measurement those models have lacked."
Dual role stated upfront: velocity channel for coins (MoE present), direct
network-value/membership signal for tokens (MoE absent). (2) SoV/MoE equation REMOVED
from intro (stated in words, appendix ref). (3) Flow reordered: motivation -> bridge/
lambda -> QTM mechanics + MoE/SoV definitions (compressed, lambda already introduced)
-> why lambda informative (three traditions + token costly-signal, merged and
trimmed) -> operationalization -> findings -> Contributions. (4) "Related Literature"
replaced by "Contributions" paragraph: three contributions (measurement: first
supply-side monetary aggregate — claim MOVED from conclusion; empirical asset pricing:
first on-chain supply-side characteristic vs LTW return-based factors, conditional
pricing + revealed-patience channel result; valuation practice: growth-levelized NVT
formalization + horse race discipline of practitioner tools), literature comparisons
woven per strand. (5) Conclusion de-duplicated: novelty claim replaced with
beliefs-revealed-by-costly-actions framing; "patience not governance activity" added.
59 pp. Iteration 2 awaits Moazzam's read.

### Entry 124 — Cowork 2026-08-05: Introduction iteration 2 (Moazzam's three directives)

(1) Order restored with lambda as the bridge paragraph DIRECTLY after the QTM +
tokenized-models framing: P1 motivation -> P2 Fisher/QTM + Cong-Li-Wang/Sockin-Xiong
-> P3 lambda bridge ("its role transforms both models"; velocity channel for coins,
direct network-value signal for tokens; "the models supply the valuation object;
lambda supplies the measurement") -> P4 MoE/SoV definitions + monotone result in words
-> P5 why lambda informative -> P6 operationalization -> P7 findings -> P8
contributions -> roadmap. (2) Findings paragraph rebuilt around THE key finding:
conditional conviction survives every measurable valuation model and technical signal
jointly for coins (12-comparator regression, t=-2.7, nothing else predicts); token
quintile alpha survives the full spanning battery (+1.7%/t=2.5; reversal control
RAISES it to 2.5%/t=3.2; no reverse-direction alpha). DCF-refinement/P-F throughput-
vs-cashflow material REMOVED from findings (Moazzam: minor issues) — retained only as
one clause in the methodology contribution. (3) \paragraph{Contributions} header
removed; contributions now flow as a normal paragraph ("These results make three
contributions...").

### Entry 125 — Cowork 2026-08-05: Long-only token quintile analysis (Moazzam's ask)

Method (best practice, both layers reported): factor alpha (LTW, NW-3) + benchmark-
relative active return / tracking error / information ratio vs EW token universe.
Results (50 formation months): Q5 long-only active +0.68%/mo, IR 0.41, t=0.83 (ns);
Q1 long-only active -1.60%/mo, t=-2.25, IR -1.10 (significant underperformance).
READING: the long-short alpha is earned predominantly on the SHORT side — conviction
is a loser-avoidance screen more than a winner-picker; implementable long-only version
is exclusionary (drop bottom quintile). Added to 6.3 as prose. Also: intro quadrant
sentence now names "Stars-minus-Avoid". Script: 04_code/phase3_explore_longonly.py.

### Entry 126 — Cowork 2026-08-05: Title, abstract finalized (pending weekend fresh-eyes review)

Title changed to "Skin in the Chain: Locked Supply and the Cross-Section of
Cryptocurrency Returns" (Moazzam's pick from fresh-read candidates). Abstract
finalized per Moazzam's own edit (lambda-first opening, theory-conditional-pricing,
coin finding + joint-race survival, token conditioning failure + extremes alpha +
spanning, measurement-contribution close; single-spaced). Paper state: complete
58-pp submission-shaped draft — title, abstract, intro (2 iterations), unified
hypotheses, results with learnings framing, robustness + mechanisms, summary
scorecard, conclusion, 12 main tables + 5 appendix tables + 2 figures in
working-paper order. NEXT: Moazzam's fresh-eyes review after the weekend
(title/abstract/intro possibly revisited); then remaining polish and submission prep.
