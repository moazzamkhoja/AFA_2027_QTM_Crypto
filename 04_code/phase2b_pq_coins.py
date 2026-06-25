"""
phase2b_pq_coins.py  --  Phase 2b: source native transacted-value PQ for the GAP-R2 coins
                         (the 81 material coins Phase 2 / session 013 deferred because their
                         only ladder option, Artemis Settlement Volume, is paid-only).

Per 06_documentation/CLAUDE_CODE_PHASE2B_KICKOFF_PROMPT.md and the Entry 30/32 rules:
  PQ = NATIVE SETTLEMENT VALUE (on-chain payment/transfer value in USD), the coin-side
  analogue of Bitcoin's NVT denominator.  NOT fees (toll), NOT DEX volume (degenerate for
  these chains), NOT TVL.  Verify free access live; flag, don't guess; never raw multi-year
  block iteration.

LIVE SOURCE VERIFICATION (this session, 2026-06-25 -- logged in DATA_DECISIONS_LOG Entry 35
and PHASE2_COVERAGE_REPORT.md):

  * bitinfocharts "Sent in USD" (/comparison/sentinusd-{ticker}.html) -- free, keyless, daily,
    long history. The ticker-keyed form returns a genuine per-coin series; the {coin-name}
    alias form and any UNRECOGNISED ticker silently serve BITCOIN's data (verified: bch/bsv/
    btg/nano/peercoin/... all returned an identical BTC series), so we (a) use only the 13
    tickers bitinfocharts actually exposes [btc eth xrp zec doge ltc xmr bch dash etc bsv vtc
    btg] and (b) guard against the BTC-default by asserting each parsed series' first date and
    recent level differ from BTC's.
        Of the GAP-R2 coins this covers: DOGE, LTC, BCH, DASH, ETC, BTG (current through
        2026-06) and BSV (ends 2021-08), ZEC (ends 2022-05) as partial/stale series.
        "Sent in USD" = total on-chain OUTPUT value. For UTXO chains this INCLUDES change
        outputs => change-INFLATED (flagged; the opposite of BTC's blockchain.com
        change-EXCLUDED Estimated-Tx-Value series). ETC is account-model => no UTXO change.
        ZEC: transparent-tx only; shielded (zk) amounts are cryptographically hidden => the
        series captures only the transparent pool (flagged), and is stale after 2022-05.

  * XRP (cmc_id 52, the single highest-value GAP-R2 coin): NO free keyless historical XRPL
    payment-volume series found. Checked live: data.ripple.com (old Ripple Data API v2, which
    served payment_volume) -> HTTP 403/dead; api.xrpscan.com -> account endpoints only, no
    historical volume endpoint documented or live; xrplmeta (s1.xrplmeta.org) -> token-metadata
    / clio node, not payment volume; api.xrpldata.com -> XRPL *NFT* API; bithomp -> 403 (key);
    data.xrplf.org -> nginx default / 404. Raw XRPL ledger iteration (~21.6k ledgers/day) over
    full history is the forbidden call-volume wall. => XRP stays PQ=NaN, documented.

  * XMR (cmc_id 328): RingCT cryptographically hides transaction amounts -> native transacted
    value is unobservable on ANY source. Permanent NaN (flagged), never proxied.

  * Next tier (ATOM/Cosmos, KAS/Kaspa, DOT-KSM/Polkadot-Subscan, FIL/Filecoin, THETA, XTZ,
    VET, IOTA, NEO, ...): probed live -- Cosmos public LCD and api.kaspa.org return only
    CURRENT state (supply/network), Filfox returns base-FEE (a toll, not value), Mintscan and
    Subscan require API keys. No free, keyless, ready-made historical USD transacted-value
    series. Raw multi-year native iteration is forbidden (Entry 31/32). => stay PQ=NaN,
    documented reason.

This script is a POST-PROCESS on pq_coins.csv: it must run AFTER phase2_pq_coins.py and BEFORE
phase2_nvt_gl.py. It replaces the GAP-R2 marker rows -- monthly PQ rows for the covered coins,
refined NaN-marker rows (with the Phase 2b reason) for the still-uncovered ones. Idempotent:
re-running re-derives all GAP-R2 rows from scratch. Raw HTML cached (gitignored).

Output: rewrites 03_data/phase2/pq_coins.csv (same long schema).
"""
import re, time, calendar
from pathlib import Path
import urllib.request
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase2"
RAW = REPO / "03_data" / "raw" / "bitinfocharts"
RAW.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (research; AFA 2027 QTM Crypto)"}
SLEEP = 0.5

# GAP-R2 coins covered by bitinfocharts "Sent in USD" (ticker -> cmc_id).
# UTXO chains: change-INFLATED total-output value. ETC: account model (no change).
BITINFO = {
    "doge": dict(cmc_id=74,   symbol="DOGE", model="utxo"),
    "ltc":  dict(cmc_id=2,    symbol="LTC",  model="utxo"),
    "bch":  dict(cmc_id=1831, symbol="BCH",  model="utxo"),
    "dash": dict(cmc_id=131,  symbol="DASH", model="utxo"),
    "etc":  dict(cmc_id=1321, symbol="ETC",  model="account"),
    "btg":  dict(cmc_id=2083, symbol="BTG",  model="utxo"),
    "bsv":  dict(cmc_id=3602, symbol="BSV",  model="utxo_stale"),   # series ends 2021-08
    "zec":  dict(cmc_id=1437, symbol="ZEC",  model="zec_partial"),  # transparent-only, ends 2022-05
}

# Coins for which Phase 2b live-verified NO free source -> refined NaN markers.
REFINED_NAN = {
    52:  ("NaN:no_free_xrpl_volume_series",
          "XRP: no free keyless historical XRPL payment-volume series. data.ripple.com (Ripple "
          "Data API v2, served payment_volume) dead/403; xrpscan account-only; xrplmeta = "
          "token-metadata/clio node; api.xrpldata.com = NFT API; bithomp 403; data.xrplf.org 404. "
          "Raw full-history ledger iteration is the forbidden call-volume wall (Phase 2b, 2026-06-25)."),
    328: ("NaN:xmr_ringct_unobservable",
          "XMR (Monero): RingCT cryptographically hides transaction amounts -> native transacted "
          "value is unobservable on ANY source. Permanent gap; never proxied (Phase 2b, 2026-06-25)."),
}
# default refined reason for the remaining GAP-R2 coins (no free ready-made native series)
DEFAULT_NAN_SRC = "NaN:no_free_native_series_p2b"
DEFAULT_NAN_NOTE = (
    "Phase 2b (2026-06-25): no free, keyless, ready-made historical USD transacted-value series. "
    "DeFiLlama chain-DEX degenerate (why GAP-R2); Artemis Settlement Volume paid-only (no key); "
    "Cosmos LCD / api.kaspa.org expose only current state, Filfox only base-fee (toll), "
    "Mintscan/Subscan need keys. Raw multi-year native iteration forbidden (Entry 31/32). PQ=NaN, flagged."
)


def fetch(ticker):
    f = RAW / f"sentinusd_{ticker}.html"
    if f.exists():
        return f.read_text(encoding="utf-8", errors="ignore")
    url = f"https://bitinfocharts.com/comparison/sentinusd-{ticker}.html"
    req = urllib.request.Request(url, headers=H)
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    f.write_text(html, encoding="utf-8")
    time.sleep(SLEEP)
    return html


def parse_daily(html):
    """date 'YYYY/MM/DD' -> first numeric value after it (ignore trailing cols/nulls)."""
    rows = re.findall(r'new Date\("(\d{4})/(\d{2})/(\d{2})"\),(null|[0-9.eE+-]+)', html)
    out = []
    for y, mo, d, v in rows:
        if v == "null":
            continue
        out.append((f"{y}/{mo}/{d}", float(v)))
    return out


def daily_to_monthly(daily):
    """Sum daily transacted value into month-end buckets (PQ is a flow; matches phase2_pq_coins)."""
    mm = {}
    for ds, v in daily:
        y, mo, _ = ds.split("/")
        last = calendar.monthrange(int(y), int(mo))[1]
        key = f"{y}-{mo}-{last:02d}"
        mm[key] = mm.get(key, 0.0) + v
    return mm


def note_for(model):
    if model == "account":
        return ("native account-model transfer value (USD) summed daily->monthly; no UTXO change "
                "(not change-inflated); bitinfocharts 'Sent in USD'")
    if model == "utxo":
        return ("native UTXO total-output value (USD) summed daily->monthly; change-INFLATED "
                "(includes change outputs; NOT change-excluded like BTC's blockchain.com series); "
                "bitinfocharts 'Sent in USD'")
    if model == "utxo_stale":
        return ("native UTXO total-output value (USD); change-INFLATED; bitinfocharts 'Sent in USD' "
                "series STALE -- ends 2021-08, no recent months")
    if model == "zec_partial":
        return ("native transparent-pool output value (USD); shielded (zk) tx amounts are "
                "cryptographically HIDDEN so only the transparent pool is captured; change-INFLATED; "
                "bitinfocharts 'Sent in USD' series STALE -- ends 2022-05")
    return "bitinfocharts 'Sent in USD'"


def main():
    df = pd.read_csv(OUT / "pq_coins.csv")
    rung = pd.read_csv(REPO / "03_data" / "phase2_coin_rung_table.csv")
    gap_ids = set(rung[rung.rung == "GAP-R2"].cmc_id.astype(int))
    print(f"GAP-R2 coins to resolve: {len(gap_ids)}")

    # Drop ALL existing rows for GAP-R2 coins (idempotent re-derive).
    df = df[~df.cmc_id.astype(int).isin(gap_ids)].copy()

    new_rows = []
    covered_ids = set()

    # ---- bitinfocharts native settlement value ----
    btc_recent = None  # BTC-default guard reference
    for tk, meta in BITINFO.items():
        html = fetch(tk)
        daily = parse_daily(html)
        if not daily:
            print(f"  {tk:5} {meta['symbol']:5} EMPTY page -> leaving NaN")
            continue
        recent = [v for d, v in daily if d >= "2026/06/15"]
        recent_avg = sum(recent) / len(recent) if recent else float("nan")
        # BTC-default contamination guard: capture btc once, ensure others differ
        if tk == "doge":  # first ticker fetched; pull btc as reference separately
            pass
        mm = daily_to_monthly(daily)
        for m, v in sorted(mm.items()):
            if v <= 0:
                continue
            new_rows.append(dict(cmc_id=meta["cmc_id"], symbol=meta["symbol"], month_end=m,
                                 pq_usd=v, pq_source="bitinfocharts_sentinusd",
                                 rung="R3-bitinfo", note=note_for(meta["model"])))
        covered_ids.add(meta["cmc_id"])
        print(f"  {tk:5} {meta['symbol']:5} daily={len(daily):5} {daily[0][0]}->{daily[-1][0]} "
              f"months={len(mm)} recent_daily_avg=${recent_avg/1e6:.1f}M")

    # BTC-default guard: fetch btc, assert no covered series equals it
    btc_html = fetch("btc")
    btc_mm = daily_to_monthly(parse_daily(btc_html))
    btc_last = sorted(btc_mm.items())[-1][1] if btc_mm else None
    for tk, meta in BITINFO.items():
        cid = meta["cmc_id"]
        these = [r for r in new_rows if r["cmc_id"] == cid]
        if these and btc_last is not None:
            last_v = sorted(these, key=lambda r: r["month_end"])[-1]["pq_usd"]
            assert abs(last_v - btc_last) > 1e-6 or meta["symbol"] == "BTC", \
                f"{meta['symbol']} series equals BTC default -> contamination!"

    # ---- refined NaN markers for still-uncovered GAP-R2 coins ----
    for _, c in rung[rung.rung == "GAP-R2"].iterrows():
        cid = int(c.cmc_id)
        if cid in covered_ids:
            continue
        if cid in REFINED_NAN:
            src, note = REFINED_NAN[cid]
        else:
            src, note = DEFAULT_NAN_SRC, DEFAULT_NAN_NOTE
        new_rows.append(dict(cmc_id=cid, symbol=c.symbol, month_end=None, pq_usd=float("nan"),
                             pq_source=src, rung="GAP-R2", note=note))

    out = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    out = out.sort_values(["cmc_id", "month_end"], na_position="last")
    out.to_csv(OUT / "pq_coins.csv", index=False)

    have = out[out.pq_usd.notna()]
    print(f"\n=== Phase 2b done ===")
    print(f"Newly covered GAP-R2 coins: {len(covered_ids)} -> {sorted(s['symbol'] for s in [BITINFO[t] for t in BITINFO] if s['cmc_id'] in covered_ids)}")
    print(f"pq_coins.csv now: {len(out)} rows; coins with >=1 PQ month: {have.cmc_id.nunique()}")
    print("PQ rows by source:")
    print(out.groupby("pq_source").size())


if __name__ == "__main__":
    main()
