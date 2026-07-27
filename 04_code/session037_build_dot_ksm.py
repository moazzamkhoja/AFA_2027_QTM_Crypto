"""Session 037: DOT + KSM channel-1 (staked) via archive-RPC state queries.

Subscan's era_stat endpoint turned out to be per-address (network-wide bonded
history is not exposed on the free API plan, and the daily/Bonded chart
category returns zeros with a ~2-month history window). Instead we read
Staking.ErasTotalStake (fallback Staking.SlotStake for pre-2020 Kusama
runtimes) directly from public archive nodes at month-end blocks, using raw
storage keys so no per-runtime metadata decoding is needed.

Both chains migrated staking to their Asset Hub (AHM): relay-chain staking
storage is cleared after migration, so months where the relay returns no
staking state are read from the Asset Hub at the same timestamp.
"""
import calendar
import csv
import datetime as dt
import json
import time

import xxhash
from websocket import create_connection, WebSocketException

DOT_PLANCK = 1e10
KSM_PLANCK = 1e12

CHAINS = [
    {
        "cmc_id": 6636, "symbol": "DOT", "planck": DOT_PLANCK,
        "start_ym": "2020-08", "end_ym": "2026-06",
        "relay": "wss://polkadot.api.onfinality.io/public-ws",
        "assethub": ["wss://polkadot-asset-hub-rpc.polkadot.io",
                     "wss://rpc-asset-hub-polkadot.luckyfriday.io"],
        "source": "archiveRPC polkadot(+assethub post-AHM):Staking.ErasTotalStake / 1e10",
    },
    {
        "cmc_id": 5034, "symbol": "KSM", "planck": KSM_PLANCK,
        "start_ym": "2019-09", "end_ym": "2026-06",
        "relay": "wss://kusama.api.onfinality.io/public-ws",
        "assethub": ["wss://kusama-asset-hub-rpc.polkadot.io",
                     "wss://rpc-asset-hub-kusama.luckyfriday.io"],
        "source": "archiveRPC kusama(+assethub post-AHM):Staking.ErasTotalStake / 1e12",
    },
]


def twox64(data: bytes) -> bytes:
    return xxhash.xxh64(data, seed=0).intdigest().to_bytes(8, "little")


def twox128(data: bytes) -> bytes:
    return (xxhash.xxh64(data, seed=0).intdigest().to_bytes(8, "little")
            + xxhash.xxh64(data, seed=1).intdigest().to_bytes(8, "little"))


KEY_TS_NOW = "0x" + (twox128(b"Timestamp") + twox128(b"Now")).hex()
KEY_ACTIVE_ERA = "0x" + (twox128(b"Staking") + twox128(b"ActiveEra")).hex()
KEY_SLOT_STAKE = "0x" + (twox128(b"Staking") + twox128(b"SlotStake")).hex()


def key_eras_total_stake(era: int) -> str:
    enc = era.to_bytes(4, "little")
    return "0x" + (twox128(b"Staking") + twox128(b"ErasTotalStake")
                   + twox64(enc) + enc).hex()


class Node:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.req_id = 0
        self.ts_cache = {}      # block_num -> ts_ms
        self.hash_cache = {}    # block_num -> hash
        self.connect()
        self.head_num = self.block_number(self.rpc("chain_getFinalizedHead", []))
        self.head_ts = self.ts_at(self.head_num)
        # Earliest block with readable state (pruned/snapshot nodes lack early state)
        self.anchor_num, self.anchor_ts = self._find_anchor()

    def _readable(self, num):
        try:
            self.ts_at(num)
            return True
        except Exception:
            return False

    def _find_anchor(self):
        if self._readable(1):
            return 1, self.ts_at(1)
        lo, hi = 1, self.head_num  # lo unreadable, hi readable
        while hi - lo > 1000:
            mid = (lo + hi) // 2
            if self._readable(mid):
                hi = mid
            else:
                lo = mid
        return hi, self.ts_at(hi)

    def connect(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = create_connection(self.url, timeout=30)

    def rpc(self, method, params):
        for attempt in range(4):
            try:
                self.req_id += 1
                self.ws.send(json.dumps({"jsonrpc": "2.0", "id": self.req_id,
                                         "method": method, "params": params}))
                while True:
                    resp = json.loads(self.ws.recv())
                    if resp.get("id") == self.req_id:
                        if "error" in resp:
                            raise RuntimeError(f"{method}: {resp['error']}")
                        return resp["result"]
            except (WebSocketException, OSError, TimeoutError) as ex:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
                self.connect()

    def block_number(self, block_hash):
        header = self.rpc("chain_getHeader", [block_hash])
        return int(header["number"], 16)

    def block_hash(self, num):
        if num not in self.hash_cache:
            self.hash_cache[num] = self.rpc("chain_getBlockHash", [num])
        return self.hash_cache[num]

    def storage(self, key, block_hash):
        return self.rpc("state_getStorage", [key, block_hash])

    def ts_at(self, num):
        if num not in self.ts_cache:
            raw = self.storage(KEY_TS_NOW, self.block_hash(num))
            if raw is None:
                raise RuntimeError(f"no timestamp at block {num}")
            self.ts_cache[num] = int.from_bytes(bytes.fromhex(raw[2:]), "little")
        return self.ts_cache[num]

    def block_at_ts(self, target_ms):
        """Last block with timestamp <= target_ms (within ~50 blocks)."""
        if target_ms <= self.anchor_ts:
            return None
        if target_ms >= self.head_ts:
            return self.head_num
        lo, lo_ts = self.anchor_num, self.anchor_ts
        hi, hi_ts = self.head_num, self.head_ts
        while hi - lo > 50:
            frac = (target_ms - lo_ts) / (hi_ts - lo_ts)
            guess = lo + max(1, min(hi - lo - 1, int(frac * (hi - lo))))
            g_ts = self.ts_at(guess)
            if g_ts <= target_ms:
                lo, lo_ts = guess, g_ts
            else:
                hi, hi_ts = guess, g_ts
        return lo

    def staked_at(self, block_num):
        """Return (planck, storage_item) or None if staking state absent."""
        h = self.block_hash(block_num)
        ae = self.storage(KEY_ACTIVE_ERA, h)
        if ae is not None:
            era = int.from_bytes(bytes.fromhex(ae[2:])[:4], "little")
            v = self.storage(key_eras_total_stake(era), h)
            if v is not None:
                return int.from_bytes(bytes.fromhex(v[2:]), "little"), f"ErasTotalStake[{era}]"
        v = self.storage(KEY_SLOT_STAKE, h)
        if v is not None:
            return int.from_bytes(bytes.fromhex(v[2:]), "little"), "SlotStake"
        return None


def month_ends(start_ym, end_ym):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    while (y, m) <= (ey, em):
        last = calendar.monthrange(y, m)[1]
        ts = dt.datetime(y, m, last, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp() * 1000
        yield f"{y:04d}-{m:02d}-{last:02d}", int(ts)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def connect_first(urls):
    for u in urls:
        try:
            return Node(u)
        except Exception as ex:
            print(f"    connect fail {u}: {str(ex)[:100]}")
    raise RuntimeError(f"no endpoint reachable: {urls}")


def build_chain(cfg):
    print(f"\n=== {cfg['symbol']} ===")
    relay = Node(cfg["relay"])
    print(f"  relay head {relay.head_num}, state from "
          f"{dt.datetime.fromtimestamp(relay.anchor_ts/1000, dt.timezone.utc):%Y-%m-%d}")
    ah = None
    rows = []
    for month_end, target in month_ends(cfg["start_ym"], cfg["end_ym"]):
        res, via = None, "relay"
        bn = relay.block_at_ts(target)
        if bn:
            res = relay.staked_at(bn)
        if res is None:
            if ah is None:
                ah = connect_first(cfg["assethub"])
                print(f"  assethub head {ah.head_num}, state from "
                      f"{dt.datetime.fromtimestamp(ah.anchor_ts/1000, dt.timezone.utc):%Y-%m-%d}")
            abn = ah.block_at_ts(target)
            if abn:
                res = ah.staked_at(abn)
                via = "assethub"
        if res is None:
            print(f"  {month_end}: no staking state (relay block {bn}) -- skipped")
            continue
        planck, item = res
        native = planck / cfg["planck"]
        rows.append((month_end, native, via, item))
        print(f"  {month_end}: {native:,.0f} {cfg['symbol']} ({via} {item})")
    # fresh cross-check at head (assethub if migrated, else relay)
    src = ah if ah else relay
    fresh = src.staked_at(src.head_num)
    fresh_native = fresh[0] / cfg["planck"] if fresh else None
    return rows, fresh_native


def main():
    with open("03_data/universe_panel.csv", encoding="utf-8") as f:
        supply = {(r["cmc_id"], r["month_end"][:7]): r["circulating_supply"]
                  for r in csv.DictReader(f)}

    out_rows = []
    summary = {}
    for cfg in CHAINS:
        rows, fresh = build_chain(cfg)
        latest_me, latest_val = rows[-1][0], rows[-1][1]
        drift = (latest_val - fresh) / fresh if fresh else None
        summary[cfg["symbol"]] = {
            "months": len(rows), "first": rows[0][0], "last": latest_me,
            "latest_staked": latest_val, "fresh": fresh, "drift": drift,
        }
        print(f"  {cfg['symbol']} cross-check: ours={latest_val:,.0f} fresh={fresh:,.0f} "
              f"drift={drift:+.2%}" if fresh else "  cross-check unavailable")
        for month_end, native, via, item in rows:
            cs = supply.get((str(cfg["cmc_id"]), month_end[:7]), "")
            ratio = ""
            if cs:
                try:
                    csf = float(cs)
                    if csf > 0:
                        ratio = native / csf
                except ValueError:
                    cs = ""
            out_rows.append({
                "cmc_id": cfg["cmc_id"], "symbol": cfg["symbol"],
                "month_end": month_end, "staked_native": native,
                "circulating_supply": cs, "staking_ratio": ratio,
                "source": cfg["source"],
                "flag": f"read via {via}:{item}; active-era total stake (excludes inactive bonded)",
            })

    with open("03_data/phase1/channel1_dot_ksm.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cmc_id", "symbol", "month_end", "staked_native",
                                          "circulating_supply", "staking_ratio", "source", "flag"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nWrote {len(out_rows)} rows to 03_data/phase1/channel1_dot_ksm.csv")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
