#!/usr/bin/bash
set -eu
# Make MSYS2 utilities available to both this shell and its detached child.
export PATH="/usr/bin:$PATH"
root=$(CDPATH= cd -- "$(/usr/bin/dirname -- "$0")" && pwd)
name=${1:?supply a new run name}
case "$name" in *[!a-zA-Z0-9_-]*|'') printf 'Invalid run name\n' >&2; exit 64;; esac
python_bin=${PYTHON:-/d/MiniConda/python.exe}
command -v "$python_bin" >/dev/null 2>&1 || { printf 'Python executable not found: %s\n' "$python_bin" >&2; exit 67; }
work="$root/runs/$name"
[ -f "$root/registration.json" ] || { printf 'Missing registration.json\n' >&2; exit 65; }
[ ! -e "$work" ] || { printf 'Work directory already exists: %s\n' "$work" >&2; exit 66; }
/usr/bin/mkdir -p "$root/launches"
launch=$(/usr/bin/mktemp -d "$root/launches/reproduction.XXXXXXXX")
/usr/bin/nohup /usr/bin/bash --noprofile --norc -c '
 root=$1; work=$2; launch=$3; python_bin=$4
 cd "$root" || exit 70
 printf "ROUND4 REPRODUCTION %s\n" "$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)"
 "$python_bin" -B -u "$root/run_study.py" --work-dir "$work"
 rc=$?
 printf "%s\n" "$rc" > "$launch/python.exit"
 printf "ROUND4 REPRODUCTION EXIT %s\n" "$rc"
 exit "$rc"
' _ "$root" "$work" "$launch" "$python_bin" >> "$root/../round3/ALL_RUNS.log" 2>&1 </dev/null &
printf '%s\n' "$!" > "$launch/wrapper_msys.pid"
printf 'Dispatched %s\n' "$launch"
printf 'Completion requires %s/python.exit = 0 and %s/completion.json\n' "$launch" "$work"
