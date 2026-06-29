# Non-EVM λ-Channel Recoverability Assessment (the 405 off-Etherscan tokens)

**Date:** 2026-06-29
**Scope:** the **405** token+other-class assets that the Etherscan pass (`universe_lambda_channel_map.csv`)
could not reach because they are not on an Etherscan-V2 EVM chain. Question: each non-EVM chain has its own
"repository of transactions" (explorer/indexer/RPC) — how much of Channel 1/2/3 is recoverable there?
**Artifact:** `03_data/phase1/non_evm_lambda_recoverability.csv` (405 rows, per-token).
**Live-verified this session:** Cosmos LCD, Tron TronGrid, Solana RPC, Cardano Koios all return 200, free,
keyless (see §2).

---

## 0. Bottom line

Non-EVM does **not** change the fundamental shape found on EVM, and for two structural reasons it is
*harder*, not easier:

1. **Identity collapse.** Of the 405, **284 (70%) have no chain or contract on file at all** — old/dead
   2014–2018 listings with no resolvable on-chain identity. Nothing is recoverable for them on any chain,
   because there is no address to point an explorer at. This dwarfs every other consideration.
2. **The native-staking trap.** The thing that makes non-EVM staking look easy — Cosmos/Cardano/Solana/Tron
   all have rich *native* staking and governance APIs — applies to each chain's **gas coin** (ATOM, ADA,
   SOL, TRX), which are in the **coin** class, *out of this token-scope*. The **tokens** issued on those
   chains still need a **per-project** staking/governance program (a CosmWasm contract, a Solana Anchor
   program, an SPL-Governance/Realms DAO) — exactly the same mechanism-gated sparsity as EVM, but now
   spread across a dozen heterogeneous runtimes with no common ABI.

So the recoverable non-EVM population is small and concentrated, and the only broadly-recoverable channel is
Channel 2 — and only for the ~114 tokens that still have an on-chain identity.

---

## 1. The 405, classified by recoverability

| Class | Count | Channel 2 (holding) | Channel 1 / 3 (lock / vote) |
|-------|------:|---------------------|------------------------------|
| **NO-IDENTITY** (no chain/contract on file) | **284** | ❌ none | ❌ none — no address exists |
| **Non-EVM, free indexer** (Solana 59, Tron 8, Osmosis/Cosmos/Kava 7, Cardano, Stellar, TON, Sui, Neo, XRP, Hedera, …) | **92** | ✅ via chain indexer | ⚠️ per-project program read; native staking = gas-coin only |
| **EVM-but-not-Etherscan** (KAIA/Klaytn 4, HyperEVM 2, Manta, X Layer, EOS-EVM, IOTA-EVM, Velas, Viction, Flare, PulseChain, smartBCH, Chiliz, …) | **22** | ✅ same contract-event method, different explorer | ✅ **same method as Etherscan** via chain Blockscout/RPC |
| **Obscure / explorer varies** | **7** | ⚠️ maybe | ❓ unknown |

**Channel-2 recoverable in principle: 114** (92 + 22, the identity-bearing set). **Not recoverable: 284 + 7.**

---

## 2. The transaction "repository" per chain — verified free & live

| Ecosystem | Tokens | Repository / API (free) | Channel 1 (staking) | Channel 2 (holding) | Channel 3 (voting) |
|-----------|------:|-------------------------|---------------------|---------------------|--------------------|
| **Solana** | 59 | Solana JSON-RPC, Solscan, Helius | per-project staking **Anchor program** (read IDL); native stake = SOL only | `getProgramAccounts` token-account ages | **SPL-Governance / Realms** program (where used) |
| **Tron** | 8 | TronGrid, TronScan API ✅ | `freeze`/stake in account resources ✅; SR-vote = TRX | TRC-20 transfer history | SR votes = TRX, not token |
| **Cosmos** (Osmosis/Cosmos/Kava) | 7 | LCD REST `/cosmos/staking`,`/cosmos/gov` ✅ (`bonded_tokens`, `proposals` returned 200) | native = gas coin; token = **CosmWasm** staking contract | Mintscan/Numia tx history | native gov = gas coin; token = CosmWasm DAO |
| **Cardano** | 1 | Koios ✅ (keyless), Blockfrost | native delegation = ADA; token = project script | Koios address/UTxO history | Catalyst (off-chain-ish) |
| **TON / Sui / Neo / Stellar / XRP / Hedera / Algorand / Theta** | ~15 total | Toncenter / Sui-RPC / NeoTube / Horizon / XRPL-API / Mirror-Node / Indexer | varies; mostly native-coin only | yes via each indexer | rarely on-chain for tokens |
| **EVM-non-Etherscan** | 22 | chain Blockscout / native RPC | **read contract events — identical method to the Etherscan pipeline** | contract `Transfer` log | `DelegateVotesChanged` etc. |

**Key:** for Channels 1 & 3, the chain-level native APIs that *are* easy (Cosmos gov, Tron SR votes, Cardano
delegation) measure the **gas coin**, not our tokens. Token-level lock/vote requires reading the project's
own program — high-effort, per-chain, and (as on EVM) usually absent or off-chain (Snapshot).

---

## 3. Recoverability estimate by channel (the 405)

| Channel | Recoverable | Basis |
|---------|------------:|-------|
| **Channel 2 — holding duration** | **~114** | every identity-bearing token (92 non-EVM-indexed + 22 EVM-other) has a transfer history in its chain's indexer; build a coin-age engine per chain. 284 no-identity + most "obscure" = unrecoverable. |
| **Channel 1 — staking/lock** | **22 cheaply + a low-single-digit % of the 92** | the 22 EVM-other are readable with the *exact* Etherscan method on their own explorer; the 92 non-EVM need a per-project Anchor/CosmWasm read and, by the EVM base rate (≈4/300 genuine), are expected to yield only a handful. |
| **Channel 3 — voting** | **22 cheaply + a low-single-digit % of the 92** | same logic; most token governance here is Snapshot (already in the panel) or off-chain. SPL-Realms / CosmWasm-DAO on-chain cases are rare. |

**Net:** the highest-value, lowest-effort non-EVM extension is the **22 EVM-but-not-Etherscan tokens** — they
drop straight into the existing pipeline by swapping the explorer endpoint (KaiaScan, HyperEVM scan, Blockscout
instances). The **92 true non-EVM** are a Channel-2 opportunity (per-chain coin-age, Solana-dominated) with only
incidental Channel-1/3 yield. The **284 no-identity** are dead — no on-chain recovery on any chain.

---

## 4. Method note / honesty

- This is a **chain-capability assessment grounded by live free-API probes**, not a per-token program read of
  all 92 non-EVM tokens — that is the correct altitude for non-EVM, where staking/gov is chain/standard-level
  rather than per-contract, and where reading 92 heterogeneous Anchor/CosmWasm/Move programs is a multi-session
  effort with low expected Channel-1/3 yield (mechanism base rate ≈1–2% from the EVM pass).
- The per-token classification (`non_evm_lambda_recoverability.csv`) records chain, repository, and per-channel
  status so the deeper per-program pass can start from a scoped list, not from scratch.
- **No λ panel was modified.** Next concrete step is the 22 EVM-other tokens through the existing pipeline
  (highest yield/effort), then a Solana-focused Channel-2 coin-age prototype.
