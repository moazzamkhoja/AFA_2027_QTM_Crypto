# Session 023 — HEX/AKRO Reconciliation + Survivorship-Bias Note
**Date:** 2026-06-29
**Scope:** Resolve the two session-021-vs-session-022 contradictions (HEX, AKRO) by running session 022's
higher-fidelity **verified-contract-read + `getLogs`** method to completion, and document the 284
no-on-chain-identity listings as an acknowledged survivorship-bias limitation. Logged as
DATA_DECISIONS_LOG **Entries 54 (HEX BUILD), 55 (AKRO REJECT), 56 (survivorship)**. Nothing else from
session 022's open items was touched.

The basis for this session (stated, not re-litigated): where session 022's contract-code-read + getLogs
method conflicts with session 021's Dune-top-holder single-escrow substitute, **022's method governs.**
For HEX that overturns 021's rejection; for AKRO, running 022's method *to completion* (reading the event,
not just its name) **agrees with 021** and supplies the better reason — so there is no standing
contradiction left on record.

---

## 1. HEX (cmc_id 5015) — REJECT (session 021) → **BUILD** (Entry 54)

**Session 021 said:** rejected at Stage 2b, *"staking internal to the HEX contract"* + *"DL staking
bucket reads 0"* — its Dune-top-holder probe found no escrow whose `balanceOf` reproduced a DeFiLlama
staked figure, and DeFiLlama reported zero.

**What the contract actually does (read directly, not inferred):** verified source cached at
`03_data/raw/etherscan_src/1_0x2b591e99afe9f32eaa6214f7b7629768c40eeb39.json`.
- `stakeStart()` → `_stakeStart()` does `g._lockedHeartsTotal += newStakedHearts`, then **`_burn(msg.sender,
  newStakedHearts)`**. Staked HEX is **burned out of the ERC20 `totalSupply`**; **no escrow contract holds
  it.** That is precisely *why* session 021's single-escrow `balanceOf` probe (and DeFiLlama) saw nothing —
  there is nothing custodial to see. The staked quantity lives only in the internal `lockedHeartsTotal`.
- This is **non-custodial burn-and-track**, a genuinely different construction than Entry 26's
  transfer-into-escrow reconstruction — logged as a new method (Entry 54), not treated as equivalent.

**Custody question — resolved directly:** the staker's wallet `balanceOf` is *reduced* (burned), and the
HEX contract's own `balanceOf` does **not** rise. So neither "tokens move into the contract" nor "holder
balance unchanged" — it is the third case: tokens leave circulation entirely and are tracked in a global.

**CMC `circulating_supply` methodology — checked, not assumed:** the HEX contract's NatSpec says verbatim:
> *"ERC20 `totalSupply()` is the circulating supply and does not include any staked Hearts.
> `allocatedSupply()` includes both"* — and `allocatedSupply() = totalSupply() + lockedHeartsTotal`.

CMC's `circulating_supply` mirrors the on-chain ERC20 `totalSupply` and therefore **excludes staked HEX**
— the **same** denominator artifact as the Entry-49 AERO/SOL/API3/ORBS series, **not a new double-count.**
(Trajectory check, since free-tier `eth_call` has no archive: panel circ was 173.4B at 2024-05 vs on-chain
liquid `totalSupply` 57.0B now, consistent with the burn-driven decline; current `allocatedSupply` 676.0B,
`lockedHeartsTotal` 619.0B.)

**Reconstruction (exact, from the contract's own accounting):** only `StakeStart` (`+stakedHearts`) and
`StakeEnd` (`−`original `stakedHearts`) move `lockedHeartsTotal` (single `_lockedHeartsTotal -=` site;
`StakeGoodAccounting` does not touch it). So:

```
lockedHeartsTotal(t) = Σ StakeStart.stakedHearts≤t  −  Σ StakeEnd.(orig)stakedHearts≤t
```

decoded on Dune (`hex_ethereum.HEX_evt_StakeStart/_StakeEnd`), `stakedHearts = (data0 >> 40) & (2^72−1)`
via exact UINT256 integer arithmetic (verified == Python arbitrary-precision decode on two sample
stakeIds); StakeEnd's amount recovered by joining `stakeId` back to the StakeStart decode (the contract
subtracts the *original* staked amount). Script: `04_code/phase1_channel1_hex_stake.py`.

**Cross-check (same 0.00% bar as the 5 session-021 BUILDs):**

| | hearts (8 dp) | HEX |
|---|---:|---:|
| reconstructed final (2026-06) | 61,900,823,759,862,091,712 | 619,008,237,598.62 |
| live `globalInfo()[0]` (2026-06-29) | 61,900,823,759,862,091,712 | 619,008,237,598.62 |
| **drift** | | **0.000000%** |

**Shipped:** `03_data/phase1/channel1_hex_stake.csv` — 50 observed asset-months (2020-03..2024-05).
`staking_ratio = locked/circulating` ranges **14.3% → 43.5%** (latest 33.6%), **<1 every month in window**
(the >1 artifact only appears post-2024, outside HEX's observed panel). Clean `locked_fraction_alloc =
locked/(locked+circ)` = 12.5% → 30.3% written alongside for audit.

**λ impact:** 2,080 → **2,130** observed asset-months; 67 → **68** distinct assets (+HEX, single-channel Ch1).

---

## 2. AKRO (cmc_id 4134) — REJECT (session 021) → **REJECT reconfirmed** (Entry 55)

**Session 021 said:** rejected in the *"no single contract reproduces the DL staked figure"* cluster
(KAITO/ATH/SUPER/…), the "treasury dominates balances" suspicion.

**Session 022's map said:** "Ch1 **GENUINE**, `Locked()`, needs contract-balance reads" — the apparent
contradiction this session was asked to resolve.

**Resolution (022's own method, run to completion):** AKRO's address `0x8ab7404063ec…` is the **AKRO token
contract itself** (`TokenProxy` → impl `AkropolisToken`, cached
`03_data/raw/etherscan_src/1_0x95801ba4892afb7c8df0c240d30880b442c1d61a.json`). Its `Locked()` event is
defined in an OpenZeppelin-style `Lockable` base:

```solidity
function lock() public onlyOwner { setLock(true); emit Locked(); }   // event Locked();  — no params
```

It is an **owner-only admin pause switch** (disables restricted methods), carries **no amount**, and
escrows **no tokens**. Live `getLogs` over full history confirms it fired **exactly once** (block 8099298,
`data=0x`). Session 022's Ch1 classifier matched the event *name* `Locked()`; reading the event shows it is
not a holder lock/stake at all — a **false positive**, overturned by the full Entry-26 test (ABI-event
presence was never the bar — Entry 53).

**Verdict:** no staking/escrow mechanism exists to reconstruct → **REJECT**, with 021's verdict standing and
now carrying the precise contract-level reason. **No 021-vs-022 contradiction remains.** (If Akropolis's
separate Sparta/Delphi staking pools are ever brought in scope, those are *different contracts*, not cmc
4134's token address, and would need their own identification + single-escrow cross-check.)

---

## 3. Survivorship-bias note — the 284 no-on-chain-identity listings (Entry 56)

See the standalone, paper-pullable version in **`03_data/SURVIVORSHIP_BIAS_NOTE.md`**. Summary:

**Live count, reconciled to the penny.** From `03_data/phase1/non_evm_lambda_recoverability.csv` (405 rows):
class `NO-IDENTITY` = **284** (chain & tx_repository both null; ch1=ch2=ch3=`no`). Against
`universe_lambda_channel_map.csv` (1,306 token+other): 1,306 = **901** Etherscan-reachable + **405**
off-Etherscan; the 405 off-Etherscan = exactly the 405 `etherscan_reachable≠yes` rows (overlap 405/405,
0 outside the map, 0 duplicate cmc_ids); the 405 = **284 NO-IDENTITY + 92 non-EVM-indexed + 22
EVM-non-Etherscan + 7 obscure**.

**Criteria for "dead":** no contract address resolvable via CMC `detail.platforms[]` + the identity map, and
no chain/explorer (EVM or non-EVM) on which any λ channel can be queried — checked across sessions 021–022.

**Cohort character:** 83% are asset_class **"other"** (non-DeFi/non-governance); 89% (252/284) are pre-2020
listings (191 with cmc_id<2000, the earliest 2013-2017 era), with a ~32-asset tail of newer non-standard
assets (BRC-20/ordinals, BCH-ABC fork, etc.). **Treated as a permanent, acknowledged survivorship-bias
limitation — not a pending data gap.** No further recovery effort is planned.

---

## Rules respected
- Trusted session 022's contract-read + getLogs method over session 021's Dune substitute where they
  conflict (the explicit basis); for AKRO that method, run to completion, *agrees with* 021.
- No paid tier signed up for or used (free Etherscan key for source/getLogs/eth_call on Ethereum; free Dune
  `small` engine for the decoded-event reconstruction).
- Every join on `cmc_id`, never symbol. No numerator guessed/interpolated — HEX reconstructed from real
  events and reconciled to a live on-chain read at 0.0000%.
- DATA_DECISIONS_LOG append-only: Entries 1–53 untouched; continued at 54/55/56.
- Did **not** touch the Channel-3 dedup, the 16 BSC/Base/Avax paid-gated tokens, or the Channel-2 prototype
  — those remain separate, pending review.
