# Session 041 — 2026-07-30 — HXRO moot; SXP ch2; OSMO ch1; gap closures

**Model:** Claude Fable 5 (Claude Code desktop)
**Prompt:** `04_code/CLAUDE_CODE_SESSION041_HXRO_SXP_OSMO_PROMPT.md`
**Mode:** fully autonomous, no check-ins.
**Keys:** `.api_keys.json` "etherscan" (SXP probe + build) — last day of the
Etherscan Pro subscription. OSMO keyless.

## Course of the session

1. Pre-flight: sleep was set to 20 min → set to Never (AC/DC 0); Windows
   Update pause confirmed through 2026-08-03.
2. **Task A (HXRO) launched first** (Etherscan-critical) — stream engine
   skipped it: "already complete". Investigation found the prompt premise
   wrong twice:
   - Streamed checkpoints store `rows`/`mblocks` (24 months intact), not
     `monthly`/`last_block` — the "empty checkpoint" reading was a schema
     misread.
   - Deeper: HXRO panel months are `carried_forward` from 2022-10 (CMC
     top-1000 visibility lost) while TVL starts 2023-02, and
     `phase1_assemble_lambda.py` computes λ on `status='observed'` rows only.
     Observed window ∩ TVL window = ∅ → **no ch2 rebuild can ever make HXRO
     regression-ready under the current spec.** Task A closed moot, 0 quota
     spent. Reopen only via a Phase-3 λ-on-observed rule change.
3. **Task B (SXP):** Ethereum probe PASS (ABI OK, supply 285.4M, getLogs
   clean). Root cause of the stale `non-EVM` flag: unprefixed Multi-Chain
   address in identity. Fixed identity (+`ethereum:` prefix) and
   universe_lambda_channel_map.csv (Ethereum/reachable/Transfer-log), ran
   ch2: 569,311 tf, 1,886 gl, 77 λ months 2019-09→2026-02, B2 clean,
   B4 HODL med 27.0% pass. λ∩TVL 60 months → complete. BSC fallback unused.
4. **Task C (OSMO):** prompt's 3 LCDs pruned at 365d. Swept all 16
   chain-registry REST endpoints + extras: osmosis.api.pocket.network is a
   FAKE ARCHIVE (height header ignored — SEI landmine family); only
   osmosis-api.noders.services is real. Wrote `session041_osmo_ch1.py`
   (session-040 pattern + binary-search earliest-block fallback). Built 2
   months (2026-04, 2026-05), drift 1.77% PASS. Investigation of the shallow
   result: prompt's 15,000 blocks/day is stale — Osmosis runs ~73,300
   blocks/day (~1.2 s/block, epochs-module anchors), so the apparent "598-day
   retention" was ~122 days; every public node's state+block floor sits at
   2026-04-02/03 (chain-wide post-upgrade state-sync point). Nothing keyless
   goes deeper; 2021-06→2026-03 reopens only on a paid indexer (Numia/
   Mintscan). Both built months overlap TVL → complete. coin_staking_type
   NaN → pos (inert for a `token`-class asset, recorded per prompt).
5. **Task D:** CASINO (Fantom not in Etherscan V2), RUNE (THORChain custom
   indexer), SUN (Tron engine gap) documented as permanent gaps in Entry 92.
6. **Task E:** assemble + coverage rebuild. λ 13,547→13,626 / 465→467.
   Coverage 193/310/1,436. Regression-ready semantics recorded explicitly
   (complete AND λ>0, excluding 11 pow_only NVT-only coins):
   **180 → 182** (coins 24 unchanged; tokens/other 156→158 = SXP + OSMO).
7. Entry 92, SESSION041_HXRO_SXP_OSMO_REPORT.md, this log, time_log;
   commit f9cc64b pushed mid-session (data), record-keeping committed at
   session end.

## Deviations from the prompt

- Task A not run at all (moot, see above) — the expected "HXRO partial →
  complete" outcome is unreachable by construction.
- OSMO built 2 months, not the hoped ~53 — archive reality, method unchanged.
- Session prompt's OSMO blocks/day constant corrected in the record.

## Guards / landmines confirmed

- Fake-archive guard (old-bonded == live-bonded) caught pocket.network again.
- `.gitignore *.log` — session logs force-added.
- PYTHONUTF8=1 used on all builder/assemble runs.
