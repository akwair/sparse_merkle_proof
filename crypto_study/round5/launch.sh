#!/usr/bin/env bash
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run_name=${1:-linux_001}
[ "$#" -le 1 ] || exit 64
case "$run_name" in
  ""|*[!a-zA-Z0-9_-]*) printf 'Invalid run name\n' >&2; exit 64 ;;
esac
work="$root/runs/$run_name"
python=${PYTHON:-/opt/conda/bin/python}
[ -f "$root/registration.json" ] || exit 65
[ ! -e "$work" ] || exit 66
[ -x "$python" ] || exit 67
[ -x "$root/runner/conditional_runner" ] || exit 68
[ -d "$root/../round3" ] || exit 69
mkdir -p "$root/launches"
launch=$(mktemp -d "$root/launches/linux.XXXXXXXX")
printf '%s\n' "$work" > "$launch/work.path"
printf 'runs/%s\n' "$run_name" > "$launch/work.relative"
export GOMAXPROCS=8
unset GOGC GOMEMLIMIT
nohup /usr/bin/bash --noprofile --norc -c '
 root=$1; work=$2; launch=$3; python=$4
 printf "ROUND5 LAUNCH %s %s\n" "$work" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
 rc=70
 if cd "$root"; then
   "$python" -B -u "$root/run_study.py" --work-dir "$work"
   rc=$?
 fi
 printf "%s\n" "$rc" > "$launch/python.exit"
 printf "ROUND5 EXIT %s %s %s\n" "$work" "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
 exit "$rc"
' _ "$root" "$work" "$launch" "$python" >> "$root/../round3/ALL_RUNS.log" 2>&1 </dev/null &
printf '%s\n' "$!" > "$launch/wrapper.pid"
printf 'Dispatched %s\n' "$launch"
