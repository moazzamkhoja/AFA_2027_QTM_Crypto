# Valuation Multiples for "Fully Priced vs. Not Yet Priced" — Literature Review

**Date:** 2026-06-26 (Cowork session, research only — no main.tex edits, no decision finalized)
**Trigger:** Moazzam's critique that the SoV/MoE label doesn't fit governance/utility tokens (only λ does),
and his request to survey what academic research on valuation multiples says about identifying when market
value is "fully reflected in price" — first in equities, then in crypto — as input to choosing the token-side
Y-axis (NV/TVL vs. NV/Revenue vs. NV/Fee vs. NV/Transactions).

---

## Part A. The coin/token SoV-MoE critique, summarized

(Full reasoning delivered in chat; corrected after Moazzam's follow-up; recorded here for the permanent
record.)

**Corrected position.** Coins keep the SoV/MoE ratio, λ/(1-λ), as the x-axis — MoE is a real, separable
component of a coin's value, so the ratio-of-two-components interpretation is valid. **Tokens use λ
directly** (the conviction index itself — staked/locked fraction, voting-weighted intensity, or whichever
channel(s) the data-construction stage settles on) — **not** λ/(1-λ), and not under any "SoV/MoE" label at
all, even relabeled. The λ/(1-λ) transform was specifically motivated by the SoV/MoE *accounting identity*
(main.tex lines 99-106: "the SoV/MoE ratio simplifies to λ/(1-λ)"), which itself assumes a genuine MC_MoE
component exists to net out. Since MoE is not a real component of a token's value, there is nothing to net
out, and the transform has no remaining justification for tokens — using it anyway would just be applying an
arbitrary monotone rescaling with no economic content behind it. This is consistent with the paper's own
formal theory: Proposition 1 is already stated directly in terms of λ (`Cov_j(r_{j,t+1}, λ_{j,t}) > 0`), not
λ/(1-λ) — the ratio only enters at the *empirical operationalization* stage for coins. Using raw λ for tokens
is therefore not a deviation from the paper's theory, it is closer to it.

This has a real (not just cosmetic) econometric consequence beyond the label: λ/(1-λ) is convex in λ, so a
regression on the ratio implicitly up-weights assets near λ→1 relative to a regression on raw λ. For coins
that weighting is justified by the MoE-depletion story (each marginal unit of locking matters more as free
float shrinks). For tokens, with no such story, raw λ is the more honest functional form. It would not change
quadrant *membership* in a rank/median-split sort (λ/(1-λ) is monotone in λ, so the ordering is identical) —
but it would matter for any regression coefficient or linear hypothesis test run directly on the measure. One
secondary, optional note: if λ for some tokens clusters very close to 1 and raw λ loses discriminating power
there, a log-odds transform of λ is a defensible *statistical* (not SoV/MoE-motivated) fix — worth keeping in
mind once the actual λ distributions for tokens are in hand, but not a reason to default back to λ/(1-λ).

Separately, lines 130-137's "UNI is the protocol's dollar" analogy (citing `cong2021tokenomics`,
`schilling2019bitcoin`) should still be softened or scoped to genuine payment/utility tokens — those citations
describe tokens required to transact on their platform, or coins competing as currency, not a pure governance
token like UNI, where holding/spending the token is not required to use the protocol. The project's own
`PHASE2_PQ_PILOT_REPORT.md` finding (UNI transfer volume ≈ 1/46.6th of, and weakly correlated with, actual
Uniswap swap volume) is direct empirical evidence against that specific analogy.

---

## Part B. Equity valuation multiples — what makes a multiple a "fully priced" signal

### B1. Damodaran's four-bucket framework: assets vs. commodities vs. currencies vs. collectibles

Damodaran's central distinction is that **only assets — things with expected future cash flows — can be
"valued"; everything else can only be "priced."** Commodities are occasionally roughly valued from macro
supply/demand; currencies and collectibles cannot be valued at all, only priced relative to one another or to
history. He places **Bitcoin in the currency bucket** (no cash flows, can only be priced — e.g., via monetary
and network metrics) and notes **Ethereum could be treated as a commodity** if its smart-contract/blockspace
usage gives it a "consumption" demand function analogous to a raw material consumed by industrial activity.
([Musings on Markets: The Bitcoin Boom](https://aswathdamodaran.blogspot.com/2017/10/the-bitcoin-boom-asset.html); [PDF](https://pages.stern.nyu.edu/~adamodar/pdfiles/blog/BitcoinAsset.pdf); [Data Update 2021](https://aswathdamodaran.blogspot.com/2021/01/data-update-3-for-2021-currencies.html))

This is an independent, well-known academic/practitioner framework that draws almost exactly the line
Moazzam is drawing: coins behave like currencies (priced via relative/monetary metrics — NVT-style, SoV/MoE
included), while assets that carry a genuine or plausible claim on future cash flows (fees, revenue, treasury)
belong in the "valuable" bucket where multiples-based and DCF-style methods are legitimate. A governance
token with real or potential fee accrual rights is closer to Damodaran's "asset" bucket than to his "currency"
bucket — which is exactly why NV/TVL, NV/Revenue, and NV/Fee (cash-flow-adjacent denominators) are more
defensible for tokens than for pure-currency coins, and why the paper's NVT_GL (a currency-style metric) may
be the *less* natural fit on the token side, not the more natural one.

### B2. What drives a multiple, and when is it "fully priced"

Damodaran's recurring framework across P/E, P/B, and P/S: every multiple is a function of (i) a profitability/
return measure, (ii) a payout or reinvestment rate, (iii) an expected growth rate, and (iv) risk. A stock is
"fully priced" relative to a peer when its multiple matches what that regression predicts given its own
fundamentals; deviations (positive or negative residuals) are the mispricing signal — not the raw multiple
level itself. ([Multiples: First Principles](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/multiples.pdf); [Relative Valuation](https://pages.stern.nyu.edu/~adamodar/pdfiles/execval/relval.pdf); [Earnings Multiples ch. 18](https://pages.stern.nyu.edu/~adamodar/pdfiles/valn2ed/ch18.pdf))

For Price-to-Book specifically — the closest analogue to NV/TVL — Damodaran's regression evidence on banks
(an asset-heavy, balance-sheet-driven sector, the standard P/B use case) is:

> PBV = 0.88 + 0.82·Payout + 7.79·Growth − 0.41·Beta + 13.81·ROE

i.e., P/B is driven overwhelmingly by **ROE relative to cost of equity** — a bank trades above book value
precisely when its return on that book value exceeds what shareholders require, and below book value when it
doesn't. Comparing P/B *levels* across banks (or sectors) without controlling for ROE is the textbook P/B
mistake. ([Determinants of P/B](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/invfables/pbvdeterminants.htm); [Book Value Multiples ch. 19](https://pages.stern.nyu.edu/~adamodar/pdfiles/valn2ed/ch19.pdf); [BIS: what drives bank P/B](https://www.bis.org/publ/qtrpdf/r_qt1803h.htm))

**This maps directly onto Moazzam's own caveat** on NV/TVL: "the TVL to revenue channel is different for
different tokens." TVL is economically playing the role of *book value* (capital deployed); the missing
control variable is **Fees/TVL or Revenue/TVL — the protocol's "ROE."** The project's own Phase 2c diagnostic
already measured this dispersion directly: per-project turnover (a Fees/TVL-style ratio) varies ~1,455× across
the lending cohort and is unbounded across perps — i.e., empirically confirmed proof that raw NV/TVL is not
comparable across protocol types without controlling for capital efficiency, exactly as Damodaran's bank
literature would predict. The fix Damodaran's literature prescribes generalizes directly: either (a) compare
NV/TVL only within narrow protocol-type cohorts (Moazzam's own proposed mitigant), or (b) regress NV/TVL on
Fees/TVL cross-sectionally within the token universe and use the residual as the mispricing signal — the same
"PBV/ROE" modified-multiple trick used for banks.

### B3. The "law of one multiple" / comparables logic

The standard prescription is to select comparable firms on **profitability, growth, and risk — not on
industry label** — and to choose, *empirically*, whichever multiple has the highest cross-sectional R² against
fundamentals within that comparable set, rather than assuming one multiple works everywhere.
([It's All Relative: Multiples, Comparables and Value](https://pages.stern.nyu.edu/~adamodar/pdfiles/country/relvalAIMR.pdf))

This argues against treating NV/TVL, NV/Revenue, NV/Fee, and NV/PQ as competing "the one true Y-axis"
candidates, and for empirically testing which one has the tightest, most stable cross-sectional relationship
to fundamentals (growth, risk) within the token universe — possibly even using more than one, the way
practitioners use both P/E and EV/EBITDA depending on capital structure.

---

## Part C. Crypto-specific valuation multiples literature

### C1. NVT and its lineage (the coin-side incumbent, and the model for NVT_GL)

NVT (Network Value/Transactions) was proposed by **Willy Woo** as a crypto analogue of the P/E ratio: market
cap over on-chain transacted value, with low NVT signaling activity growing faster than price (undervalued)
and high NVT signaling the opposite. Woo's own framing explicitly invokes **both** store-of-value and
medium-of-exchange utility as the thing NVT is "pricing" — the same duality this paper is now disentangling.
([NVT overview](https://datadriveninvestor.com/articles/the-network-value-to-transactions-nvt-ratio-a-breakthrough-for-cryptocurrency-valuation); [Glassnode NVT docs](https://docs.glassnode.com/further-information/metric-guides/nvt/nvt-ratio))

**Dmitry Kalichkin (Cryptolab Capital, 2018)** refined raw NVT into **NVT Signal**: network value divided by a
90-day moving average of transacted value, to smooth volatility spikes and make it usable as something closer
to a real-time trading signal rather than a noisy spot ratio. Kalichkin separately proposed **NVM (Network
Value to Metcalfe)**, replacing the transaction-value denominator with a Metcalfe's-law-style function of daily
active addresses (log(MC) / log(DAA²)) precisely *because* raw transacted-value data is unreliable or
unavailable for some assets. ([Rethinking NVT](https://medium.com/cryptolab/https-medium-com-kalichkin-rethinking-nvt-ratio-2cf810df0ab0); [NVM ratio](https://medium.com/cryptolab/network-value-to-metcalfe-nvm-ratio-fd59ca3add76); [CryptoQuant NVM docs](https://dataguide.cryptoquant.com/network-indicators/nvm-ratio))

This is directly useful as precedent: when transaction-value data is the weak link (exactly the project's own
96-gap-token problem), the established practitioner response has been to swap in a different, more available
denominator — active addresses/Metcalfe — rather than abandon the NVT *framework*. NV/TVL, NV/Revenue, and
NV/Fee are the DeFi-era version of the same move, motivated by data availability as much as by theory.

A related growth-adjustment, **NVTG (Network Value/Transactions to Growth)**, normalizes NVT by the growth
rate of transaction value — directly parallel to this paper's own Growth-Levelized NVT, and independent
confirmation that "growth-adjusting NVT" is a recognized refinement, not an idiosyncratic one.
([Improvements on NVT / NVTG](https://medium.com/ledgercapital/improvements-on-the-network-value-to-transactions-nvt-ratio-introducing-network-569569f6b3e3))

### C2. Metcalfe's Law network-value models

**Timothy Peterson (2018)** found Bitcoin's medium/long-run price fits a Metcalfe's-law model (value ∝ active
users²) with R² ≈ 0.85. ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3078248); [CAIA PDF](https://caia.org/sites/default/files/metcalfeslaw_websiteupload_7-5-18.pdf))
A later refinement layers in logistic-diffusion adoption dynamics on top of the base Metcalfe model.
([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176518300557))
Countering this, more rigorous **causal-inference testing on block-level data across six proof-of-work coins
found no significant Metcalfe effect** for any of them — a direct empirical challenge to the whole network-value
framework, and a reminder that fit quality in an unconditional time series (Peterson's R²) can overstate a
relationship that doesn't hold up to better identification. ([QuantPedia summary](https://quantpedia.com/metcalfes-law-in-bitcoin/))

### C3. Token quantity-theory and platform-membership models (already cited in main.tex)

**Cong, Li & Wang (2021), "Tokenomics: Dynamic Adoption and Valuation" (RFS 34, 1105-1155)** model token
prices as aggregating heterogeneous users' *transactional demand* for a platform token that is required to
transact — equilibrium price comes from adoption dynamics, not discounted cash flows, with adoption following
an S-curve and tokens lowering users' transaction costs by letting them capitalize on platform growth.
([NBER WP 27222](https://www.nber.org/papers/w27222); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3222802); [RFS abstract](https://academic.oup.com/rfs/article-abstract/34/3/1105/5891182))
This is a precise mechanism — it fits tokens that genuinely function as a required payment/access medium (gas
tokens, pay-per-use utility tokens) very well, but does **not** describe a pure governance token where holding
or spending the token is not required to use the protocol (see Part A) — the mismatch the user's critique
identifies.

**Sockin & Xiong (2020), "A Model of Cryptocurrencies" (NBER WP 26816; Management Science, 2023)** model a
cryptocurrency as *membership* in a platform, with token price reflecting users' and speculators' demand
clearing against a fixed supply, generating a convenience yield to membership and a market-fragility channel
when speculator sentiment crowds out user participation. ([NBER PDF](https://www.nber.org/system/files/working_papers/w26816/w26816.pdf); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3550965))
Already cited in main.tex for the coin-side convenience-yield channel; its actual model (abstract "membership")
is, if anything, a *better* conceptual fit for governance-token holding (DAO membership) than for base-layer
coin holding — worth knowing as a subtlety, though not something that needs to change now.

### C4. TVL as a "stock" measure, and its known measurement problem

**"Piercing the Veil of TVL: DeFi Reappraised" (2024)** is the most direct academic treatment of exactly the
caveat Moazzam raised. It documents that TVL is systematically inflated by recursive wrapping/leveraging
(e.g., stETH deposited into Aave, borrowed against, redeposited as more stETH), and proposes **TVR (Total
Value Redeemable)** as a corrected measure. At its 2021 peak the TVL-to-TVR ratio was roughly 2× across leading
protocols, and TVL is shown to be *more volatile* than TVR in downturns because of cascading liquidations on
top of price declines. ([arXiv:2404.11745](https://arxiv.org/pdf/2404.11745); [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-032-07035-7_1))
This is a genuine, separate-from-Damodaran's-cohort-comparability-point measurement caveat on NV/TVL: even
*within* a protocol category, raw DeFiLlama TVL may not be a clean "book value" analogue unless a
double-counting adjustment (or a TVR-style correction) is applied.

### C5. Fee/Revenue multiples (Token Terminal, practitioner-standard)

**Token Terminal** popularized Price/Sales and Price/Fees multiples for crypto protocols: P/S = market cap (or
FDV) over trailing protocol *revenue* (the take-rate-adjusted share the protocol retains); P/Fees substitutes
gross *fees* (total value paid by users — borrower interest, trading fees, etc.) for revenue, useful when
revenue-distribution structures differ or aren't yet defined. Their own framing matches Damodaran's point B3
directly: "a protocol trading at a lower multiple is not automatically cheap... the right interpretation
depends on growth, sector positioning, business quality, and whether the market is pricing current reality or
future expansion." ([Token Terminal Fees](https://tokenterminal.com/explorer/metrics/fees); [Token Terminal Revenue](https://tokenterminal.com/explorer/metrics/revenue); [Intro to Token Terminal](https://medium.com/@mika_49129/introducing-token-terminal-financial-metrics-for-blockchain-protocols-57abfa80575c))
This is the practitioner-level precedent for exactly NV/Fee and NV/Revenue as candidates, with the Fee-vs-
Revenue distinction mapping onto a real economic difference (gross throughput a protocol facilitates vs. what
it actually keeps) that the paper would need to pick deliberately and label clearly — they are not
interchangeable, and "Fees" is closer in spirit to PQ (gross throughput-priced) while "Revenue" is closer to a
genuine cash-flow-to-the-asset measure (closer to true P/E logic, where it exists).

### C6. Crypto factor models — is there an existing "value" factor to anchor to?

**Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency" (JF 77, 1133-1177)** — already the
paper's own secondary factor-model robustness check — find a three-factor model (market, size, momentum)
spans the cross-section; they do **not** identify a standalone value factor for crypto.
([NBER WP 25882](https://www.nber.org/system/files/working_papers/w25882/w25882.pdf); [JF](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119))
More recent work — **Sakkas & Urquhart (2024), "Blockchain factors"** (JIFMIM) — extends this by proposing
momentum, investor attention, and **valuation ratios** as additional return-predictive factors in crypto,
suggesting the literature is actively moving toward exactly the kind of valuation-multiple-as-predictor
framework this paper already uses for Hypothesis 2/3 — but a dedicated "crypto value factor" akin to
Fama-French HML does not yet exist in the literature. That gap is, in effect, the contribution opportunity
NV/TVL, NV/Revenue, or NV/Fee would be filling for the token side.

---

## Part D. Synthesis — mapping candidates against the literature

| Candidate (Y-axis) | Closest equity analogue | What "ROE-equivalent" control variable the literature implies | Known measurement caveat |
|---|---|---|---|
| **NV/PQ** (existing NVT_GL) | P/E-style (Woo's own analogy) | Growth rate of PQ (already built into the levelized construction) | Data-availability — this is precisely the constraint driving the 96-gap-token problem; also a currency-style metric, arguably the *least* natural fit for governance-only tokens per Damodaran's bucket framework (Part B1) |
| **NV/TVL** | P/B-style (book value) | Fees/TVL or Revenue/TVL ("protocol ROE") — Damodaran's bank-P/B regression form | TVL inflation from recursive leverage/wrapping (Part C4); Fees/TVL dispersion already measured at ~1,455× across the project's own lending cohort — must control for protocol-type cohort or regress out Fees/TVL, exactly as Moazzam already proposed |
| **NV/Revenue** | P/S / true P/E-style (cash flow to the asset) | Growth + margin (take rate) | Revenue ≠ Fees; revenue-sharing mechanisms differ sharply by protocol (some tokens have none, making Revenue=0 or undefined) |
| **NV/Fee** | P/S-style (gross throughput-priced) | Growth + risk | Closer to PQ in spirit (gross value facilitated, not retained) — may end up highly correlated with NV/PQ rather than a genuinely distinct signal; worth checking empirically before treating as a separate candidate |

None of the four is disqualified by the literature; all four have direct precedent (NVT/NVT-Signal/NVTG for
NV/PQ; the bank P/B literature plus the TVL-multiple practitioner discussion for NV/TVL; Token Terminal's P/S
and P/Fees for the other two). The literature's consistent prescription — Damodaran's regression-based
modified multiples, the bank P/B-vs-ROE logic, and Token Terminal's own framing — is to never compare the raw
multiple across dissimilar protocol types without controlling for the type-specific capital-efficiency or
margin variable, which is exactly the caveat Moazzam already raised independently for NV/TVL.

**Recommendation: NV/TVL as the primary token-side Y-axis, with NV/Fee as a robustness/secondary candidate.**
Reasons: (1) coverage — DeFiLlama tracks TVL for essentially every DeFi-categorized token, which is the one
axis the project's own gap-token saga (96 tokens with no defensible PQ) has not been able to solve for
NV/PQ; (2) it is the only candidate that is a true stock-over-stock ratio (NV and TVL are both balance-sheet-
moment measures), the cleanest match to the P/B analogy and to Damodaran's bank regression form; (3) it
reuses data the project already vetted for coverage (the Decisions-Log Entry 38 "TVL × turnover" exploration)
without the part of that exploration that was rightly rejected — back then TVL was being asked to *impersonate*
a flow (PQ) via an imputed turnover rate, which the 1,455× dispersion finding correctly killed; used directly
as a stock-denominator instead of a flow-proxy, that same TVL data does not need the rejected imputation step
at all. NV/Fee is the best fallback for tokens where TVL is thin or not the right capital-stock concept (and
is worth testing for correlation with NV/PQ — it may turn out to be redundant with it, since both price gross
throughput). NV/Revenue is the theoretically purest (closest to a true cash-flow claim) but likely has the
weakest coverage, since many governance tokens have no revenue-sharing mechanism at all (Revenue = 0/undefined
for a large share of the universe) — worth checking empirically before relying on it as a primary measure.
Existing NV/PQ stays as a legacy robustness cross-check for the ~21 tokens it is already built for.

**On controlling for cross-sectional comparability:** category-wise quadrants (median splits within DEX,
Lending, Derivatives, Liquid Staking, Vault sub-universes — already the project's planned approach for the
coin/token split itself) handle *between-category* differences in capital efficiency, but the project's own
Phase 2c finding — ~1,455× turnover dispersion measured *within* the lending cohort alone — shows a large
share of the problem is *within-category*, which category fixed effects do not absorb. The two are
complements, not substitutes: category quadrants (or category fixed effects in a panel regression) for the
between-category level shift, plus a continuous Fees/TVL (or Revenue/TVL) control for the within-category
dispersion — either as a second sort dimension (double-sort: category × capital-efficiency tercile) or, more
in the spirit of Damodaran's modified-PBV/ROE approach, by regressing NV/TVL on Fees/TVL within the token
universe and using the residual as the actual screening variable. Category controls alone would still leave
the within-category 1,455× dispersion unaddressed.

---

## Sources

- [Damodaran — The Bitcoin Boom: Asset, Currency, Commodity or Collectible?](https://aswathdamodaran.blogspot.com/2017/10/the-bitcoin-boom-asset.html) / [PDF](https://pages.stern.nyu.edu/~adamodar/pdfiles/blog/BitcoinAsset.pdf)
- [Damodaran — Data Update 2021: Currencies, Commodities, Collectibles and Cryptos](https://aswathdamodaran.blogspot.com/2021/01/data-update-3-for-2021-currencies.html)
- [Damodaran — Multiples: First Principles](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/multiples.pdf)
- [Damodaran — Relative Valuation](https://pages.stern.nyu.edu/~adamodar/pdfiles/execval/relval.pdf)
- [Damodaran — It's All Relative: Multiples, Comparables and Value](https://pages.stern.nyu.edu/~adamodar/pdfiles/country/relvalAIMR.pdf)
- [Damodaran — Earnings Multiples (ch. 18)](https://pages.stern.nyu.edu/~adamodar/pdfiles/valn2ed/ch18.pdf) / [Book Value Multiples (ch. 19)](https://pages.stern.nyu.edu/~adamodar/pdfiles/valn2ed/ch19.pdf)
- [Damodaran — Determinants of Price-to-Book Ratios](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/invfables/pbvdeterminants.htm)
- [BIS Quarterly Review — The ABCs of bank PBRs](https://www.bis.org/publ/qtrpdf/r_qt1803h.htm)
- [Cong, Li & Wang (2021) — Tokenomics: Dynamic Adoption and Valuation, NBER WP 27222](https://www.nber.org/papers/w27222) / [RFS](https://academic.oup.com/rfs/article-abstract/34/3/1105/5891182)
- [Sockin & Xiong — A Model of Cryptocurrencies, NBER WP 26816](https://www.nber.org/system/files/working_papers/w26816/w26816.pdf)
- [DataDrivenInvestor — The NVT Ratio](https://datadriveninvestor.com/articles/the-network-value-to-transactions-nvt-ratio-a-breakthrough-for-cryptocurrency-valuation) / [Glassnode NVT docs](https://docs.glassnode.com/further-information/metric-guides/nvt/nvt-ratio)
- [Kalichkin — Rethinking NVT](https://medium.com/cryptolab/https-medium-com-kalichkin-rethinking-nvt-ratio-2cf810df0ab0) / [NVM Ratio](https://medium.com/cryptolab/network-value-to-metcalfe-nvm-ratio-fd59ca3add76)
- [Ledger Capital — NVTG (growth-adjusted NVT)](https://medium.com/ledgercapital/improvements-on-the-network-value-to-transactions-nvt-ratio-introducing-network-569569f6b3e3)
- [Peterson — Metcalfe's Law as a Model for Bitcoin's Value, SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3078248)
- [QuantPedia — Metcalfe's Law in Bitcoin (critique summary)](https://quantpedia.com/metcalfes-law-in-bitcoin/)
- [Piercing the Veil of TVL: DeFi Reappraised, arXiv:2404.11745](https://arxiv.org/pdf/2404.11745)
- [Token Terminal — Fees](https://tokenterminal.com/explorer/metrics/fees) / [Revenue](https://tokenterminal.com/explorer/metrics/revenue)
- [Liu, Tsyvinski & Wu — Common Risk Factors in Cryptocurrency, NBER WP 25882](https://www.nber.org/system/files/working_papers/w25882/w25882.pdf) / [JF](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119)

**Next step:** human review; no main.tex changes made. If the SoV/MoE relabeling (Part A) is approved, it is a
contained edit to the abstract/intro narrative and one appendix sentence — not a methodology change. The
Y-axis question (Part D) is an empirical horse race once a candidate panel for NV/TVL, NV/Revenue, and NV/Fee
can be built — worth scoping as a follow-on Claude Code data task if Moazzam wants to pursue it.
