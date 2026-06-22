# Human Time Log — AFA 2027 QTM Crypto Research

> Per AFA rules, document all human activity: what you did, how long it took, and whether it was a prompt to AI or a direct contribution.

| Date | Duration (min) | Activity Type | Description |
|------|---------------|---------------|-------------|
| 2026-06-10 | 15 | Prompt | Initial project scoping — shared AFA call and QTM framework write-up with AI |
| 2026-06-10 | 10 | Direct | Created GitHub repository; reviewed AI-generated README and folder structure |
| 2026-06-10 | 60 | Decision + Review | Theoretical framework discussion: convenience yield, coins vs. tokens, TVL disambiguation, rejected θ coefficient, finalized λ framing and paper outline |
| 2026-06-10 | 15 | Review | Reviewed and approved full LaTeX introduction draft (Section 1) |
| 2026-06-12 | 45 | Review + Decision | Read introduction draft, identified 8 issues, reviewed revised draft, empirical design brainstorm (λ measures, NVT/G, asset universe, portfolio construction) |
| 2026-06-12 | 30 | Decision | Finalized NVT/PMT levelized approach, asset category structure (coins/L1, L2, token groups), blockchain-agnostic design, HYPE coin vs. token classification |
| 2026-06-12 | 30 | Decision + Review | Hypothesis structure finalized: λ as primary signal, NVT/f as conditioning variable, H1a/H1b/H2/H3 approved; reviewed Hypotheses section draft |
| 2026-06-19 | 20 | Decision + Review | Chose "applied theory" (light formalization) over full structural model for Section 2; decided to merge Theory and Hypotheses into one combined section; reviewed drafted propositions and theory section |
| 2026-06-19 | 25 | Decision + Review | Identified flawed $F(s_t+\bar c_{t+1})$ aggregation step in Section 2.1; requested rigorous continuum-of-agents fix instead of a bare assumption; explored governance-token staking mechanics (vote-escrow vs. snapshot vs. fee-sharing); decided $\lambda$ should be a multi-channel measurement index (staking/holding/voting), construction deferred to data stage |
| 2026-06-19 | 35 | Decision + Review | Challenged the artificial coin/governance-token model split and the $\theta_{t+1}$ vs. random-walk simplification (accepted correction on the latter); approved unifying Sections 2.1/2.2 into one "Locking Decision" model; identified unjustified "L1-only" restriction in Hypothesis 1a and the implicit asset-index ambiguity in Proposition 1; reviewed and approved the revised, unified Section 2.1 and renumbered Propositions/Section 2 subsections |
| 2026-06-19 | 10 | Decision | Identified that "NVT/fundamental" is a misleading name (implies division by an undefined "fundamental" term); evaluated candidate replacements and selected "Growth-Levelized NVT" over "Growth-Normalized NVT" on grounds of mechanical precision; approved renaming throughout the paper |
| 2026-06-22 | 25 | Decision + Review | Decided to write a data specification document (for a separate Claude Code session) before drafting Section 3 prose; answered clarifying questions on asset-universe scope (point-in-time rank screen, not fixed-dollar floor, to jointly avoid penny-token noise and survivorship bias), sample period (Aug 2015 onward, not Jan 2021), factor model (both CAPM and Liu-Tsyvinski-Wu, reported as mutual robustness), and λ-index construction (equal-weighted average of standardized available channels); reviewed and approved `04_code/DATA_SPECIFICATION.md` and `04_code/DATA_DECISIONS_LOG.md` |
| 2026-06-22 | ~15 (est., confirm) | Prompt + Decision | Launched the Phase 0 pipeline session (Claude Code / Opus 4.8); answered two judgment-call questions when CoinGecko's 365-day historical limit was surfaced — chose the free CoinMarketCap historical endpoint as the ranking backbone, and chose to exclude stablecoins entirely from the universe; confirmed AFA record-keeping requirements and the GitHub repo, and authorized end-of-session commit+push |

---

**Activity Types:**
- `Prompt` — writing/refining a prompt to the AI
- `Direct` — human-authored code, writing, or edits
- `Review` — reading and evaluating AI output
- `Decision` — making a judgment call on research direction
