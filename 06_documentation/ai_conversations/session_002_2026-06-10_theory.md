# AI Conversation Log — Session 002
**Date:** June 10, 2026
**Model:** Claude Sonnet (Anthropic) via Claude Cowork
**Human:** Moazzam Khoja

---

## Topic: Theoretical Foundations of the QTM Framework

### Summary
Extended theoretical discussion establishing the academic grounding for the QTM-based crypto valuation framework. Covered: convenience yield, monetary search theory, seigniorage, coins vs. tokens distinction, governance participation as MOAT signal, TVL disambiguation, and the coins-as-currencies / tokens-as-currencies framing.

---

## Key Theoretical Decisions Made

### 1. Primary Theoretical Frame: Convenience Yield + Monetary Search
- **Convenience yield** (Sockin-Xiong 2020) is the primary rational motive for holding
- **Monetary search theory** (Kiyotaki-Wright 1993) grounds the coordination equilibrium
- **Seigniorage** (Cong-He NBER w33640) complements as the income mechanism
- These three are complementary, not competing explanations

### 2. Rational Expectations Confirmed
- The λ → MOAT signal is primarily rational, not behavioral
- Behavioral amplifiers (loss aversion, lock-in) acknowledged but secondary
- Cong-Li-Wang (2021) adoption S-curve is the key rational dynamics model

### 3. Coins vs. Tokens — Fundamental Distinction
**Coins (ETH, SOL):**
- PQ = total on-chain transaction volume in the native coin
- λ = staked / total circulating supply (clean on-chain measure)
- Signal = monetary coordination + convenience yield + seigniorage
- Cong & He (NBER w33640) directly covers this

**Tokens (UNI, AAVE):**
- PQ = protocol throughput (DEX volume, TVL-as-activity) = "nominal GDP" of the protocol economy
- λ = governance staked + voting participation / circulating supply
- Signal = MOAT (economic conviction, voice vs. exit, switching costs)
- Edmans-Manso (2011) "voice vs. exit" is the key framework
- Each token is the currency of its protocol economy — NOT an equity claim

### 4. TVL Disambiguation (Critical)
Two distinct uses of TVL in the framework:
- **TVL as λ (for coins):** Staked coins = M_Locked (supply measure)
- **TVL as PQ (for tokens):** Protocol economic activity = nominal GDP analog
These must never be conflated.

### 5. Rejected: Claim Coefficient (θ)
User correctly rejected θ (fraction of protocol revenue flowing to token holders) as overcomplicating the framework. Rationale: tokens are currencies, not equities. Whether revenue flows to holders is immaterial — the dollar has value because the US economy is large, not because GDP flows to dollar holders. Cong-Li-Wang's approach (present value of future platform utility) is the correct framing.

### 6. Governance Token λ — Composite Measure
For governance tokens, λ should be a composite:
- λ_passive = tokens staked but not voting / total supply (capital commitment only)
- λ_active = voting participation rate × staked / total supply (conviction signal)
- Active governance participation is a costly signal (Spence 1973): gas fees, time, reputational risk

---

## Key Literature Identified

| Paper | Relevance |
|-------|-----------|
| Cong, Li & Wang (2021) RFS | Dynamic token adoption and valuation — primary theory reference |
| Sockin & Xiong (2020) NBER w26816 | Convenience yield pricing of crypto |
| Cong & He (2024) NBER w33640 | Staking tokenomics — coins theory |
| Kiyotaki & Wright (1993) AER | Monetary search theory — coordination equilibrium |
| Edmans & Manso (2011) RFS | Voice vs. exit — governance token theory |
| Hirschman (1970) | Exit, Voice, Loyalty — conceptual foundation for token governance |
| Spence (1973) QJE | Signaling theory — active governance as costly signal |
| Jiang, Krishnamurthy & Lustig (2024) NBER | Exorbitant privilege / reserve currency analog |
| Krishnamurthy & Vissing-Jorgensen (2012) JPE | Convenience yield in Treasury market |
| Nagel (2016) QJE | Liquidity premium of near-money assets |
| Liu & Tsyvinski (2021) RFS | Risks and returns of cryptocurrency |
| DAO Governance ACM (2024) | Voting participation → token returns (+4.7%) |

---

## Paper Outline Agreed

1. **Introduction** — QTM framing, λ/V_Free, coins vs. tokens, findings, related lit, roadmap
2. **Theoretical Framework** — formal derivations, propositions for coins vs. tokens
3. **Hypotheses** — H1 (λ → returns for coins), H2 (governance λ → returns for tokens), H3 (quadrant → cross-sectional returns)
4. **Data and Empirical Design**
5. **Results**
6. **Robustness**
7. **Conclusion**

Literature embedded in introduction (JF/RFS convention), with "Related Literature" paragraph near end of introduction.

---

## Human Time This Session
~60 minutes — theoretical discussion, framework refinement, outline decisions
Activity type: Decision + Review
