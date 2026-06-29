# Session 022 — Status, Transition & Next-Session Prompt
**Date:** 2026-06-29
**Topic:** Can Etherscan (and other chains' explorers) recover λ Channels 1/2/3 for the rejected tokens,
and for the whole token universe? Contract-level read + on-chain confirmation, EVM and non-EVM.

---

## 1. What this session did (and did NOT do)

**Did:** a *feasibility / identification* pass — for tokens across the universe, resolved the on-chain
contract, **read the verified contract code**, identified the λ-relevant events/functions, and **confirmed
on-chain via `getLogs`** which mechanisms actually fire. Then assessed non-EVM chains by capability.

**Did NOT:** build or modify any λ panel. No `lambda_*.csv` / `tvl_panel.csv` changed. This is an
identification map that *feeds* a future build, not a build. **No DATA_DECISIONS_LOG source decision was
reversed** — Entries 21–26 still govern; this adds Entry 53 as a feasibility finding.

---

## 2. Headline results

### 2a. EVM (Etherscan V2), full token+other universe = 1,306 assets
- **901 EVM-reachable**, contract read & ABI-classified (793 on free-tier `getLogs` chains, 108 on paid-only).
- **Channel 1 genuine lock/stake, getLogs-CONFIRMED: 6** — HEX, NMR, stkAAVE, XAN (amount-bearing, build-ready);
  AKRO, VSL (bare `Locked()`, need contract-balance reads).
- **Channel 3 ACTIVE on-chain voting, getLogs-CONFIRMED: 34** (UNI, ENS, SUSHI, COMP, GTC, KP3R, BTRST, EIGEN,
  ONDO, STRK, MNT, BLUR, … — all emit `DelegateVotesChanged`).
- **Channel 3 needs PAID plan to confirm: 15** (BSC/Base/Avax ERC20Votes infra) — `ALT,AWE,BAKE,BNX,CHEEL,EDG,
  ESPORTS,FORM,LINEA,MCT,MDX,OP,PONKE,TKO,ZORA`. **+1 Channel-1 paid:** TNC.
- **Channel 3 infra present but DORMANT/negligible: 15** (CORE, SUPER, ILV, FLOKI, PENDLE, … — unusable).
- **Channel 2 (holding duration): all 901** reachable (793 free / 108 paid).

### 2b. THE PAID-API ANSWER (measured live, not assumed)
Free Etherscan-V2 key: `getsourcecode` works on **all** chains; **`getLogs`/`tokentx` is FREE only on
Ethereum, Polygon, Arbitrum, Blast — and PAID-only on BSC, Base, Avalanche** ("Free API access is not
supported for this chain"). So a paid plan is needed (a) for any channel on BSC/Base/Avax (16 candidate tokens),
and (b) for Channel-2 throughput at panel scale.

### 2c. Non-EVM = the 405 off-Etherscan tokens
- **284 have NO chain/contract identity** (dead 2014–2018 listings) → unrecoverable on any chain.
- **92 non-EVM with free indexers** (Solana 59 dominant; Tron 8; Cosmos/Osmosis/Kava 7; Cardano/Stellar/TON/
  Sui/Neo/XRP/Hedera tail) → **Channel 2 recoverable** per chain indexer; Channel 1/3 need per-project
  Anchor/CosmWasm/Realms reads (native staking/gov = gas-coin, out of token-scope) → low expected yield.
- **22 EVM-but-not-Etherscan** (KAIA, HyperEVM, Manta, X Layer, …) → **same contract-read method, different
  explorer** → highest-value/lowest-effort extension.
- Live-verified free APIs: Cosmos LCD (`bonded_tokens`, `gov/proposals`), Tron TronGrid, Solana RPC, Cardano Koios.

---

## 3. Artifacts produced (all committed)
| File | What |
|------|------|
| `03_data/phase1/universe_lambda_channel_map.csv` | **1,306-row** master: per-token chain, address, reachable, free/paid, contract, ch1/ch2/ch3 verdict + event sig |
| `03_data/phase1/etherscan_lambda_channel_map.csv` | the 402 bucket-1 subset (same schema) |
| `03_data/phase1/non_evm_lambda_recoverability.csv` | **405-row** non-EVM per-token class/repo/channel status |
| `04_code/_universe_lambda_findings.csv` | per-event detail (topic0, log counts, first block) |
| `04_code/_etherscan_lambda_findings.csv` | bucket-1 per-event detail |
| `04_code/_etherscan_reach_resolve.csv` | address resolution |
| `03_data/ETHERSCAN_LAMBDA_CHANNEL_EMPIRICAL.md` | EVM empirical write-up (supersedes the pre-data FEASIBILITY.md) |
| `03_data/ETHERSCAN_LAMBDA_CHANNEL_FEASIBILITY.md` | original meta-analysis (kept as prior-reasoning record) |
| `03_data/NON_EVM_LAMBDA_CHANNEL_ASSESSMENT.md` | non-EVM chain-capability assessment |
| `04_code/universe_lambda_pipeline.py` | reusable/resumable pipeline (resolve→read→classify→getLogs) |
| `03_data/raw/cmc_detail/`, `03_data/raw/etherscan_src/` | raw caches (reproducibility) |

---

## 4. Recoverability summary table (universe = token+other = 1,306; coins out of scope)

| Channel | EVM confirmed (free) | EVM needs-paid | Non-EVM recoverable | Not recoverable |
|---------|--------------------:|---------------:|--------------------:|----------------:|
| **Ch1 staking/lock** | 6 genuine | 1 (TNC) | ~22 EVM-other + low-% of 92 | rest (mechanism absent) |
| **Ch2 holding** | 793 | 108 | ~114 (92 nonEVM-idx + 22 EVM-other) | 284 no-identity |
| **Ch3 voting** | 34 active | 15 | ~22 EVM-other + low-% of 92 | rest (Snapshot/off-chain) |

---

## 5. Open decisions for co-work discussion
1. **Build the 6 Ch1 + 34 Ch3 confirmed series?** First dedupe the 34 Ch3 against the existing Snapshot panel
   (Entry 25) — UNI/ENS/SUSHI/COMP likely already covered; isolate the net-new.
2. **Buy Etherscan Pro?** Only justified for (a) the 16 BSC/Base/Avax candidates and (b) panel-scale Channel-2.
3. **Channel 2 at all?** Entry 24 left it unbuilt as "highest-value addition." This pass confirms it's the
   single most-recoverable channel (793 free EVM + ~114 non-EVM). Decide whether to build the coin-age engine.
4. **Non-EVM effort?** Recommend: do the **22 EVM-other** via existing pipeline first (cheap); Solana Channel-2
   prototype second; skip the 284 no-identity entirely.

---

## 6. NEXT-SESSION PROMPT (paste to continue)

> Continue the λ-channel recovery work from session 022 (see
> `06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md` and the three assessment docs in `03_data/`).
> Context: we have an identification map of which tokens can yield λ Channel 1/2/3 from on-chain data
> (`03_data/phase1/universe_lambda_channel_map.csv`, 1,306 rows). Nothing is built yet.
> Tasks, in priority order:
> 1. **Dedupe** the 34 getLogs-CONFIRMED Channel-3 tokens against the existing Snapshot space map
>    (`03_data/phase1/snapshot_space_map.csv`) to isolate net-new λ additions vs. cross-check-only.
> 2. **Build** the 6 confirmed Channel-1 series (HEX, NMR, stkAAVE, XAN amount-bearing; AKRO, VSL via
>    contract-balance) as monthly locked/total-supply ratios via `getLogs` event-replay — extend
>    `phase1_channel1_*` scripts; respect the Entry-21 "logs not eth_call" rule.
> 3. **Decide & document** (DATA_DECISIONS_LOG) the Etherscan-Pro question for the 16 BSC/Base/Avax
>    candidates (`ALT,AWE,BAKE,BNX,CHEEL,EDG,ESPORTS,FORM,LINEA,MCT,MDX,OP,PONKE,TKO,ZORA,TNC`).
> 4. If approved, **prototype Channel-2** coin-age on ONE Ethereum token's full Transfer log (free tier),
>    measure call budget vs the 100k/day cap, then scope the panel-wide build.
> 5. Non-EVM: run the **22 EVM-other** tokens through `universe_lambda_pipeline.py` with chain-specific
>    explorer endpoints (KaiaScan/Blockscout). Leave the 284 no-identity tokens dead.
> Do NOT modify any λ panel without flagging for review first (spec §0).
