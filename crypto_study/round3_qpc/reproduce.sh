#!/usr/bin/bash
# Optional fresh reproduction of the frozen corrected run, never overwrite.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
name=${1:?Provide a new run name}
case "$name" in *[!a-zA-Z0-9_-]*|'') exit 64;; esac
work="$root/runs/$name"
[ ! -e "$work" ] || exit 66
python=${PYTHON_EXE:-/d/MiniConda/python.exe}
/usr/bin/nohup /usr/bin/bash --noprofile --norc -c '
 "$1" -B -u "$2/run_screening.py" --work-dir "$3"
 rc=$?
 printf "REPRODUCTION_EXIT %s %s\n" "$3" "$rc"
 exit "$rc"
' _ "$python" "$root" "$work" >> "$root/../round3/ALL_RUNS.log" 2>&1 </dev/null &
printf 'Fresh reproduction dispatched: %s\n' "$work"
