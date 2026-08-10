% AI Workflow Documentation
% Supplementary Appendix to "Skin in the Chain: Locked Supply and the Cross-Section of Cryptocurrency Returns"
% Moazzam Khoja --- AFA 2027 Special Session of Papers Written with Generative AI Workflows

# Summary of AI Conversations (June 10 -- August 10, 2026)

The project comprised 46 logged AI sessions across two environments: interactive
Cowork conversations (Claude, Anthropic), where the author set direction, critiqued
output, and made every substantive decision, and autonomous Claude Code build
sessions, each launched from a written kickoff prompt fixed in advance and reviewed
afterward under an honest-results clause forbidding specification changes after
results were seen. Full verbatim transcripts are in Volume II; the repository
(github.com/moazzamkhoja/AFA_2027_QTM_Crypto) archives the 46 contemporaneous session
logs, 33 verbatim kickoff prompts, a 127-entry decisions log, and all code and data.

**Phase A --- Theory and literature (June 10--19; sessions 001--005, Cowork).**
The author shared the AFA call and a two-page QTM valuation framework. Conversations
established the theoretical foundations: convenience yield (Sockin-Xiong) and
monetary search (Kiyotaki-Wright) as primary frames, seigniorage (Cong et al.) as
the income mechanism, the coin/token distinction, and the central construct --- the
conviction ratio lambda, the locked fraction of supply, with the SoV/MoE
decomposition following from QTM. The author rejected an early theta-coefficient
formulation, demanded a rigorous continuum-of-agents aggregation to replace a flawed
step, challenged an artificial model split, and approved the hypotheses (conviction
level; valuation conditioning; quadrant portfolio). First drafts of the
introduction and theory were written and revised through detailed author critique
(eight tracked issues in one round).

**Phase B --- Data construction (June 22 -- July 30; sessions 006--041, mostly
Claude Code).** Autonomous sessions built the empirical infrastructure from free,
verifiable sources under standing constraints (no paid tiers; all joins on
CoinMarketCap id; engine guards immutable): a 1,939-asset monthly universe
(2015--2026); the three-channel conviction panel (staking from chain-native
archives, HODL-6m from full transfer-log replay on thirteen EVM chains, governance
delegation/voting); on-chain transaction-volume series validated within 5 percent of
chain totals; the TVL panel; and the growth-levelized valuation ratios. The phase
was iterative and adversarial with the data: fake archive nodes were detected and
excluded, identity mismatches purged, contamination guards enforced, and every dead
end (Monero's hidden amounts, pruned nodes, paid-only vendors) logged rather than
papered over. Final samples: 24 proof-of-stake coins (718 asset-months) and 101
tokens (2,771 asset-months).

**Phase C --- Empirical testing (August 4; sessions 042--045).** A Cowork session
fixed the analysis specification in advance (regression ladders, self-built monthly
Liu-Tsyvinski-Wu factor analogs, portfolio rules); three Claude Code sessions then
executed it. Results: the conviction level is rejected for coins but its interaction
with valuation is strongly negative and survives a twelve-signal joint race; for
tokens conditioning fails under six valuation measures, while conviction is priced
through the extremes of its distribution --- a quintile long-short earning 1.7
percent monthly factor-adjusted alpha that no competitor portfolio spans. Nulls (the
quadrant portfolio, scarcity models) were reported at equal prominence. Mechanism
tests (M1--M4) were postulated after the coin/token asymmetry emerged and tested
once each; author-directed review analyses (within-sector quintiles, long-only
implementation, channel decomposition) were run once and disclosed as exploratory.

**Phase D --- Writing, revision, and submission (August 4--10; Cowork).** The
author directed successive pruning and rewriting rounds: hypotheses unified across
asset classes, mechanisms moved to robustness with a postulate-then-test framing,
tables restructured around the questions they answer, three introduction iterations
(motivation-first opening; lambda as the bridge between QTM and tokenized models;
findings led by the joint-race and spanning results), the final abstract in the
author's own words, and the title. The author caught and corrected several AI
errors along the way, including a mischaracterization of practitioner valuation
methods, a stale significance claim, and a misleading between-sector framing that a
requested power analysis overturned. The phase closed with assembly of this
documentation package.

**Division of labor.** The author contributed direction, theory judgment, all
hypothesis and identification decisions, quality control, and final language; the
AI contributed drafting, literature synthesis, all data engineering and estimation
code, execution of pre-specified analyses, and revision mechanics. Every
substantive claim in the paper traces to a decision recorded in the logs.

**Line attribution (human vs.\ AI).** Counted from the repository at submission:
17,502 lines of code (Python builders, analysis scripts, utilities), 2,019 lines of
paper source (LaTeX), and 28,262 lines of documentation (session logs, decisions
log, kickoff prompts, specifications, literature review) --- 47,783 committed lines
in total. Measured by who typed the committed line, the AI contributed over 99.9
percent: the author's directly typed contributions are the final abstract text
(drafted verbatim by the author) and scattered sentence-level wordings dictated in
conversation. The author's contribution is instead concentrated in the layer the
line counts do not capture: the initial prompt and all subsequent direction, the
theoretical judgments, every methodological decision (127 logged entries), quality
control that caught and reversed AI errors, and approval of all final language ---
approximately 53 hours of logged human time against roughly two person-months of
AI-executed construction, estimation, and writing.

\newpage

# Time Log by Conversation

Human time from the contemporaneous time log (66 entries; durations marked * are
author estimates). AI session wall-clock time where recorded in session logs;
autonomous sessions ran unattended.

| Session | Date | Topic | Human (min) |
|---|---|---|---|
| 001 | 2026-06-10 | general | 100 |
| 002 | 2026-06-10 | theory | 0 |
| 003 | 2026-06-12 | general | 105 |
| 004 | 2026-06-19 | general | 90 |
| 005 | 2026-06-22 | general | 125 |
| 006 | 2026-06-22 | phase0 pipeline | 0 |
| 007 | 2026-06-22 | phase0 review | 0 |
| 008 | 2026-06-22 | phase0b followup | 0 |
| 009 | 2026-06-23 | phase1 lambda | 35 |
| 010 | 2026-06-24 | phase1 closeout phase2 pq | 50* |
| 011 | 2026-06-24 | pq theory | 0 |
| 012 | 2026-06-24 | pq pilot | 45* |
| 013 | 2026-06-24 | phase2 build | 45* |
| 014 | 2026-06-25 | phase2b coins | 55* |
| 015 | 2026-06-25 | dune pilot | 10* |
| 016 | 2026-06-25 | dune dryrun | 10* |
| 017 | 2026-06-25 | phase2c diagnostic | 10* |
| 018 | 2026-06-26 | repo sync and lambda tvl scope | 30 |
| 019 | 2026-06-26 | lambda scale and tvl panel | 10* |
| 020 | 2026-06-26 | bucket2 bucket3 recovery | 30* |
| 021 | 2026-06-29 | token bucket1 exhaustive reaudit | 10* |
| 022 | 2026-06-29 | etherscan nonEVM lambda channel audit | 135* |
| 023 | 2026-06-29 | hex akro reconciliation survivorship | 55* |
| 024 | 2026-06-30 | lambda free build | 75* |
| 025 | 2026-07-01 | etherscan pro channel2 build | 135* |
| 026 | 2026-07-01 | channel2 tail and op | 75* |
| 027 |  | tvl expansion and ch2 tail | 20* |
| 028 | 2026-07-04 | cowork coverage csv and session028 plan | 45* |
| 029 |  | breadth build and coin probes | 9* |
| 030 | 2026-07-05 | task a resume cut short | 15* |
| 031 | 2026-07-24 | task a day1 complete | 20* |
| 032 | 2026-07-24 | myx build task a closed | 300* |
| 033 | 2026-07-25 | xtz matic nvt probes negative | 0 |
| 034 | 2026-07-25 | chz blockchair defi batch1 | 10* |
| 035 | 2026-07-25 | defi batch2 | 180* |
| 036 | 2026-07-26 | steth meme batch3a | 60* |
| 037 | 2026-07-27 | dot ksm core ch1 | 60* |
| 038 | 2026-07-27 | shib ch2 batch3b | 60* |
| 039 | 2026-07-28 | dotksm pq trx warp | 60* |
| 040 | 2026-07-28 | cosmos lcd ch1 | 60* |
| 041 | 2026-07-30 | hxro sxp osmo | 60* |
| 042 | 2026-08-04 | paper restructure tvlgl phase3 design | 780* |
| 043 | 2026-08-04 | phase3 core tests | 60* |
| 044 | 2026-08-04 | phase3b confirmatory sorts | 60* |
| 045 | 2026-08-04 | phase3c fees dcf technicals | 60* |
| 046 | 2026-08-05 | to 10 writing revision submission | 0 |
| | | **Total human time** | **3154 min (~53 h)** |

AI compute: 36 autonomous Claude Code build sessions (typically 1--3 h wall-clock each where logged) plus interactive Cowork sessions concurrent with the human time above. Autonomous sessions required no human attention between launch and review.
