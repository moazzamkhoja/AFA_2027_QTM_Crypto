# AFA 2027 AI Finance Research: A Quantity Theory of Money Approach to Cryptocurrency Valuation

**Submission to the AFA 2027 Annual Meeting — Special Session on AI in Finance Research**

> *This paper is predominantly AI-generated as part of the American Finance Association's 2027 special session evaluating AI capabilities in finance research. All AI conversations, human contributions, and workflow documentation are archived in this repository.*

---

## Research Overview

This project develops and empirically tests a **Quantity Theory of Money (QTM)-based valuation framework** for cryptocurrencies. The framework decomposes a crypto asset's market capitalization into its **Store of Value (SoV)** and **Medium of Exchange (MoE)** components, and uses two novel metrics — the **NVT/G ratio** and the **SoV/MoE ratio** — to assess pricing efficiency and guide investment positioning.

### Core Framework

The foundation is the Fisher equation applied to digital assets:

**MC ≈ PQ / V**

Where market capitalization (MC) proxies money supply (M), and on-chain transaction volume proxies nominal economic output (PQ).

Key innovations:

- **λ (Lambda):** Proportion of total token supply that is locked/staked (near-zero velocity). Decomposed from circulating supply using TVL data.
- **V_Free:** Velocity of only the free-circulating supply — the pure exchange efficiency of actively used tokens.
- **MC_MoE = PQ / V_Free** — the transactional value component
- **MC_SoV = MC − MC_MoE** — the speculative/store-of-value residual

### Strategic Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| NVT/G | (MC / Annualized Tx Volume) / Growth Rate | Analogous to PEG ratio for stocks; low = MoE undervalued relative to adoption |
| SoV/MoE | MC_SoV / MC_MoE | High = speculative dominance; Low = utility dominance |

### Quadrant Investment Framework

|  | High SoV/MoE (Speculative) | Low SoV/MoE (Utility) |
|--|--|--|
| **High NVT/G** | AVOID | MATURE / OVERPRICED |
| **Low NVT/G** | STAR / ECONOMIC MOAT | GARP (Growth at Reasonable Price) |

---

## Research Questions & Hypotheses

*(To be developed in `02_hypotheses/`)*

Preliminary hypotheses:
1. Assets with low NVT/G and high SoV/MoE (Star quadrant) generate superior risk-adjusted returns over 12–24 month horizons.
2. λ (staking ratio) is positively associated with SoV premium and negatively associated with velocity.
3. Quadrant transitions are predictable from on-chain signals and precede price movements.

---

## Repository Structure

```
AFA_2027_QTM_Crypto/
├── 01_literature/          # Literature review, related papers, annotation notes
├── 02_hypotheses/          # Formal hypothesis statements, theoretical derivations
├── 03_data/                # Processed datasets (raw data sourced from APIs)
├── 04_code/                # Data pipeline, metric computation, empirical tests
├── 05_paper/               # Paper drafts (LaTeX or Markdown)
└── 06_documentation/       # AFA-required audit trail
    ├── ai_conversations/   # Full chat logs with AI (required by AFA)
    ├── time_log.md         # Running log of human hours and activities
    └── workflow_notes.md   # Notes on AI vs human task allocation
```

---

## Data Sources

- **On-chain transaction volume:** Glassnode, Coinmetrics
- **TVL / Locked supply:** DeFiLlama
- **Market cap / Circulating supply:** CoinGecko, CoinMarketCap
- **Price history:** CoinGecko API

---

## AFA Submission Requirements

- [x] Investigation began on or after **June 1, 2026**
- [ ] Submission deadline: **August 31, 2026**
- [ ] All AI conversations documented in `06_documentation/ai_conversations/`
- [ ] Time log maintained in `06_documentation/time_log.md`
- [ ] Code fraction report completed before submission

---

## Authors

- **Moazzam Khoja** — University of Texas at San Antonio

*Investigation start date: June 10, 2026*
