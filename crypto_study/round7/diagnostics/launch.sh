#!/usr/bin/env bash
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ "$#" -eq 0 ] || exit 64
[ -f "$root/registration.json" ] || exit 65
[ ! -e "$root/runs/allocation_001" ] || exit 66
mkdir -p "$root/launches"
dispatch=$(mktemp -d "$root/launches/allocation.XXXXXXXX")
export GOMAXPROCS=8
unset GOGC GOMEMLIMIT GODEBUG
nohup /usr/bin/bash --noprofile --norc -c '
  root=$1; dispatch=$2
  /usr/bin/python3 -B -u "$root/controller.py" --execute "$dispatch"
  rc=$?
  printf "%s\n" "$rc" > "$dispatch/controller.exit"
  printf "ROUND7 DIAGNOSTIC EXIT %s %s\n" "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit "$rc"
' _ "$root" "$dispatch" >> "$root/../../round3/ALL_RUNS.log" 2>&1 </dev/null &
printf '%s\n' "$!" > "$dispatch/wrapper.pid"
printf 'Dispatched %s\n' "$dispatch"
