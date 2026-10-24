#!/usr/bin/bash
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work="$root/runs/screening_001"
[ -f "$root/registration.json" ] || exit 65
[ ! -e "$work" ] || exit 66
mkdir -p "$root/launches"
launch=$(/usr/bin/mktemp -d "$root/launches/screening.XXXXXXXX")
/usr/bin/nohup /usr/bin/bash --noprofile --norc -c '
 root=$1; work=$2; launch=$3
 cd "$root" || exit 70
 printf "LAUNCH %s\n" "$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
 /d/MiniConda/python.exe -B -u "$root/run_screening.py" --work-dir "$work"
 rc=$?
 printf "%s\n" "$rc" > "$launch/python.exit"
 printf "EXIT %s %s\n" "$rc" "$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
 exit "$rc"
' _ "$root" "$work" "$launch" >> "$root/../round3/ALL_RUNS.log" 2>&1 </dev/null &
printf '%s\n' "$!" > "$launch/wrapper_msys.pid"
printf 'Dispatched %s\n' "$launch"
