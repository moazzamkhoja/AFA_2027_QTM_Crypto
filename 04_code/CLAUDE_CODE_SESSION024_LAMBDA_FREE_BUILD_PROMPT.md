# Claude Code Kickoff Prompt — Session 024: BUILD λ Channels 1/2/3 from FREE sources (all chains)

Paste the prompt below as the first message of a new Claude Code session, working directory
`C:\AFA_2027_QTM_Crypto`. This is the **build** continuation of session 022's full-universe
identification map (`06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md`, Decisions Log Entry 53),
which read verified contract code and confirmed mechanisms live via `getLogs`. Session 022 produced an
identification map but built nothing. This session turns the **free-source-confirmed** rows into actual λ
series.

**This is PHASE 1 of a two-phase build: PHASE 1 = every FREE source on every chain identified as free
(not just Etherscan). PHASE 2 (a later session) = paid services.** Do not sign up for or use any paid tier
this session — Phase 2 is explicitly out of scope here.

**Dependency — DONE:** session 023 (`CLAUDE_CODE_HEX_AKRO_RECONCILIATION_AND_SURVIVORSHIP_PROMPT.md`) has
already run (commit `b7ecb73`, Entries 54/55/56). Its verdicts are **final**: **HEX = BUILD (already shipped —
this is NOT a rebuild target)** — `03_data/phase1/channel1_hex_stake.csv` via `04_code/phase1_channel1_hex_stake.py`,
already in the assembler glob; **AKRO = REJECT** (its `Locked()` is an owner-only admin pause switch, not a
stake — do NOT attempt it). Read `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md` + Entries 54/55/56 before
building Channel 1 so you don't re-derive or duplicate HEX. **Current λ baseline going into this session:
2,130 observed asset-months / 68 distinct assets** — measure your deltas from there.

---

```
You're working in the AFA 2027 QTM Crypto research repo. This session BUILDS λ series from free on-chain
sources across ALL chains identified as free in session 022 — Etherscan-free EVM chains, EVM-but-not-
Etherscan chains via their own free explorers, and non-EVM free indexers. Read everything in "Required
reading" before building anything.

## Required reading (full text, not summaries)
1. 04_code/DATA_DECISIONS_LOG.md — Entry 21 (logs not eth_call; the no-archive rule), Entry 23 (ETH
   beacon-deposit getLogs event-replay — the Channel-1 reconstruction template), Entry 24 (Channel 2
   unbuilt = "highest-value addition"), Entry 25 (Channel 3 = Snapshot + token-weight guard), Entry 26
   (single-escrow custody standard + cross-check-to-balanceOf at ~0.00% drift), Entry 49 (the
   circulating_supply staked-token double-count artifact), Entry 53 (session 022 feasibility), and
   **Entries 54 (HEX BUILD — a THIRD Channel-1 template: non-custodial burn-and-track, reconstructed from
   StakeStart(+)/StakeEnd(−) decoded-event amounts, no escrow; see `phase1_channel1_hex_stake.py`), 55
   (AKRO REJECT — the "an event named Locked() is not necessarily a lock" lesson), 56 (the 284 dead-listing
   survivorship-bias note)** from session 023. **Next free log entry number = 57.**
2. 03_data/ETHERSCAN_LAMBDA_CHANNEL_EMPIRICAL.md and 03_data/NON_EVM_LAMBDA_CHANNEL_ASSESSMENT.md — the
   per-channel findings and the measured free/paid chain gate.
3. The three maps, joined on cmc_id, are your build worklist:
   - 03_data/phase1/universe_lambda_channel_map.csv (1,306 rows; ch1/ch2/ch3 verdict + event signature)
   - 03_data/phase1/non_evm_lambda_recoverability.csv (405 rows; chain, repository, per-channel status)
   - 04_code/_universe_lambda_findings.csv (per-event topic0, log counts, first block)
4. The existing build scripts you will EXTEND (do not rebuild): phase1_channel1_eth_staking.py,
   phase1_channel1_evm_locks*.py, phase1_channel3_voting.py, phase1_assemble_lambda.py. New Channel-1
   batches land as a new 03_data/phase1/channel1_*.csv (the assembler globs channel1_*.csv); Channel 3
   appends to channel3_voting.csv. There is NO channel2_*.csv yet — you are creating that pipeline.
5. 03_data/phase1/snapshot_space_map.csv and channel3_voting.csv — the EXISTING Channel-3 panel, needed
   for the dedup in Task A.

## FREE-source inventory (from session 022 — what "free" means per chain)
- Etherscan V2 free key (04_code/.api_keys.json): getsourcecode on ALL chains; getLogs/tokentx FREE only
  on Ethereum(1)/Polygon(137)/Arbitrum(42161)/Blast(81457). BSC/Base/Avalanche getLogs are PAID -> PHASE 2.
- EVM-but-not-Etherscan (22 tokens: KAIA/Klaytn, HyperEVM, Manta, X Layer, EOS-EVM, IOTA-EVM, Velas,
  Viction, Flare, PulseChain, smartBCH, Chiliz, ...): free via each chain's own Blockscout/native JSON-RPC
  eth_getLogs — same contract-read+event-replay method, different endpoint.
- Non-EVM free indexers (live-verified session 022): Solana JSON-RPC (api.mainnet-beta.solana.com) +
  Solscan; Tron TronGrid/TronScan; Cosmos LCD (lcd.osmosis.zone etc. /cosmos/staking, /cosmos/gov);
  Cardano Koios. Keyless where session 022 confirmed it.

## Build tasks, in priority order (highest value / lowest effort first)

### Task A — Channel 3: dedup the 34 active ERC20Votes tokens vs the Snapshot panel, then build net-new
The 34 getLogs-CONFIRMED active-voting tokens (universe_lambda_channel_map.csv, ch3=='ERC20Votes-ACTIVE':
COMP, MET, DDX, FORTH, CVP, RAD, DMG, FLUID, ETHDYDX, BIT, EUL, T, ONDO, BONE, CYBER, PEAK, W, EIGEN, WLFI,
BLAST, UNI, ENS, SUSHI, GTC, KP3R, BTRST, RGT, HFT, STRK, MNT, BLUR, RAIN, TOMI, UXLINK).
1. Join on cmc_id against snapshot_space_map.csv + channel3_voting.csv. Split into (i) already-have-a-
   Snapshot-Channel-3-series (cross-check only) and (ii) NET-NEW (no Snapshot turnout in the panel).
2. For the NET-NEW set, build a monthly Channel-3 series from on-chain `DelegateVotesChanged` event replay:
   delegated voting weight outstanding at each month-end / circulating supply (the same token-weighted
   turnout definition as Entry 25, but sourced on-chain). All are on free chains (ETH + Blast).
   - Token-weight validity guard (Entry 25): null spaces where weight isn't token-denominated; flag.
   - Decide & document: is on-chain delegated-weight the same construct as Snapshot voter-turnout, or a
     distinct sub-channel? State it; do not silently merge two different measures into channel3_voting.csv.
3. Append to channel3_voting.csv (or a clearly-named channel3_onchain_*.csv if the construct differs),
   re-run phase1_assemble_lambda.py, report the λ asset-month / asset-count delta.

### Task B — Channel 1: build the free-chain confirmed locks
Confirmed genuine, amount-bearing (build via getLogs event-replay -> monthly locked / total-or-circulating
supply, cross-checked to a live contract balanceOf/global read at ~0.00% drift, Entry 26): **NMR, stkAAVE,
XAN.** (**HEX is already BUILT in session 023 — do NOT rebuild it; AKRO is REJECT — do NOT attempt it.**)
- **Before reconstructing ANY token, read its verified source and confirm the event is a genuine holder
  lock/stake — not an admin/pause/vesting flag.** Session 023's AKRO finding is the cautionary case: its
  `Locked()` was an owner-only `Lockable.lock()` pause switch that fired once with no amount, and session
  022's name-matching classifier wrongly flagged it "GENUINE." **Apply this directly to VSL below** — its
  `Locked()` may be the same false positive; verify the mechanism before building.
- VSL: bare `Locked()` (no amount in event) -> ONLY if the source confirms it's a real lock, reconstruct
  from the lock contract's balanceOf at each month-end block, not event amounts; flag as the weaker
  construction. If `Locked()` is an admin/pause flag (the AKRO pattern), REJECT it with the contract reason.
- Apply the Entry-49 denominator check per token: does CMC circulating_supply already exclude the staked
  amount (ratio can exceed 1)? State per token; keep un-capped + flagged, use z-scored rank not level.
  (HEX is the worked example — its contract NatSpec exposed `allocatedSupply = totalSupply + locked`, so the
  clean `locked/(locked+circ)` fraction was written alongside `locked/circ`; do the same where a token's
  contract exposes a staked-inclusive supply.)
- For high-event-count tokens, Dune's **free** decoded-event tables (`<project>_<chain>.<CONTRACT>_evt_<Event>`,
  `small` engine) are an acceptable getLogs substitute and were used for HEX (Entry 54) and the Bucket-1/3
  builds (Entries 48/51) — same "logs not eth_call" rule, far fewer calls than windowed Etherscan getLogs.
- Land as a new 03_data/phase1/channel1_freebuild.csv (picked up by the assembler glob). Extend
  phase1_channel1_evm_locks*.py, don't rewrite. Re-run the assembler; report the delta.

### Task C — Channel 2: holding-duration, the Entry-24 gap — PROTOTYPE then scale on free chains
This is the single highest-value addition (Entry 24) and the most-recoverable channel (793 free EVM + ~114
non-EVM). Build it carefully:
1. Prototype on ONE Ethereum token's FULL Transfer-log history (free tier): build a FIFO per-address
   coin-age engine (acquisition-lot tracking), then compute the Channel-2 metric at each month-end —
   share of supply unmoved > a threshold window (state the window; HODL-wave style). Validate on a token
   with known behavior.
2. MEASURE the call budget: full Transfer history windowed by block vs the free 100k-calls/day cap. Report
   the per-token call count and extrapolate to the free-chain EVM population BEFORE scaling — if it blows
   the free cap, that is itself the Phase-2 (paid) trigger; document it, don't silently stall.
3. Address-class hygiene: exclude exchange/contract/LP wallets from "holder conviction" where identifiable
   (Etherscan labels are incomplete — document the filter as a judgment call per Entry-24/spec §0).
4. Scale across free-chain EVM tokens as budget allows; new pipeline phase1_channel2_holding.py ->
   03_data/phase1/channel2_holding.csv; wire it into phase1_assemble_lambda.py (Channel 2 currently always
   NaN — adding it changes the channel-availability counts; report them).

### Task D — EVM-but-not-Etherscan (22 tokens): same method, free chain explorers
Run the session-022 contract-read+getLogs method against each chain's free Blockscout/native RPC
eth_getLogs for the 22 tokens (non_evm_lambda_recoverability.csv class=='EVM-non-Etherscan'). Recover any
genuine Ch1 lock / active Ch3 voting the same way; fold into the channel1_*/channel3_* outputs.

### Task E — Non-EVM free indexers: scoped, low-expected-yield, time-boxed
For the 92 non-EVM-indexed tokens (Solana 59 dominant), Channel 2 is the realistic target via free indexers
(Solana getProgramAccounts token-account ages; Tron/Cosmos/Cardano transfer history). Channel 1/3 require
per-project program reads (Anchor/Realms/CosmWasm) and are low-yield — time-box this; build only what a
free indexer cleanly supports, flag the rest for Phase 2. Do NOT chase the 284 no-identity tokens (dead;
session 023 documents them as survivorship bias).

## Method rules (unchanged from the project standard)
- Reconstruct numerators from real events/balances; NEVER guess or interpolate. Flag gaps (spec §0).
- Channel 1 must clear the Entry-26 bar: a specific contract/event reconstructs a monthly locked-quantity
  series cross-checked to a live on-chain balance (~0.00% drift) — not just "a mechanism exists."
- Join everything on cmc_id, never symbol (the Entry-20/39 collision landmine).
- Logs not historical eth_call (Entry 21). Respect each asset's staking_start; pre-start months = NaN not 0.
- NO paid tier, no purchase, no signup — Etherscan Pro and paid indexers are PHASE 2. Flag, don't act.
- DATA_DECISIONS_LOG.md is append-only — continue at the next free entry number; never edit prior entries.
- Standardize/assemble exactly as phase1_assemble_lambda.py already does (z-score per channel per month,
  equal-weight available channels, record channel count) — extend, don't change its logic.
- KNOWN GOTCHA (session 023): `phase1_assemble_lambda.py` writes `lambda_panel.csv` correctly, then can
  throw a cosmetic `UnicodeEncodeError` on a `→` in its final `print` under the Windows cp1252 console — the
  CSV is already written when it throws. Run it with `PYTHONUTF8=1` (or read the file to confirm the counts)
  rather than assuming the assembly failed. A one-char fix to that print is fine if you touch it.

## CONTEXT-WINDOW DISCIPLINE (required)
Track your context usage as you work. **When you reach ~2/3 (about 66%) of the context window**, STOP
starting new build work and instead, before you run out:
1. Write a session report of what was built vs. left (counts, λ delta, which tasks A–E are done/partial).
2. Write a transition document capturing exact state (which CSVs written, which scripts extended, what was
   mid-flight, any cross-check still pending).
3. Write the NEXT-session prompt to continue THIS build from where you stopped (same two-phase framing),
   as a new numbered session.
4. Commit and push everything before the window closes — a clean checkpoint beats a lost in-flight build.
If you finish all free-source tasks before 2/3, proceed to write the PHASE 2 (paid) kickoff prompt as the
next session (see below), then log + commit.

## PHASE 2 preview (for the transition / next prompt, NOT this session)
Phase 2 builds from paid services: Etherscan Pro for getLogs on BSC/Base/Avalanche (the 16 paid-gated
candidates: ALT, AWE, BAKE, BNX, CHEEL, EDG, ESPORTS, FORM, LINEA, MCT, MDX, OP, PONKE, TKO, ZORA, TNC),
panel-scale Channel-2 throughput if the free 100k/day cap binds (Task C2), and paid non-EVM indexers for
the Channel-1/3 gaps Task E flagged. Phase 2 requires explicit human purchase approval — do not pre-empt it.

## Close-out (every session)
Update 06_documentation/time_log.md and log this session as
06_documentation/ai_conversations/session_024_*.md. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end (or at the 2/3 checkpoint).

Stop when either (a) all free-source tasks A–E are built/flagged and the Phase-2 prompt is written, or
(b) you hit the 2/3 context checkpoint and have written the report + transition + next-session prompt and
committed. Either way, end with the λ panel re-assembled and the asset-month/asset-count delta reported.
```
