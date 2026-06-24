#!/usr/bin/env bash
# Resilient runner: resume ETH staking reconstruction until all month-ends are done.
# Re-invokes the resumable script after any crash/early-exit; stops when complete.
cd /c/AFA_2027_QTM_Crypto || exit 1
CK=03_data/raw/phase1_onchain/eth_staking_monthly.json
for i in $(seq 1 60); do
  done=$(python -c "import json;d=json.load(open('$CK'));print('2026-05-31' in d['monthly'])" 2>/dev/null)
  if [ "$done" = "True" ]; then echo "ETH_STAKING_COMPLETE after $i passes"; break; fi
  echo "pass $i: resuming..."
  python 04_code/phase1_channel1_eth_staking.py >/dev/null 2>&1
  sleep 3
done
