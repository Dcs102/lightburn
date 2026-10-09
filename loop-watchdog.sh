#!/usr/bin/env bash
# Enforce a per-iteration time cap on the LIVE loop without restarting it.
# Kills any 'opencode run' process older than MAX_AGE seconds; loop.sh's
# safety net then commits/pushes and advances to the next iteration.
MAX_AGE=${MAX_AGE:-3600}
echo "watchdog started: killing opencode runs older than ${MAX_AGE}s"
while pgrep -f "opencode run" >/dev/null 2>&1; do
  for pid in $(pgrep -f "opencode run"); do
    start=$(ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^ *//')
    [ -z "$start" ] && continue
    ts=$(date -d "$start" +%s 2>/dev/null) || continue
    now=$(date +%s)
    if (( now - ts > MAX_AGE )); then
      echo "$(date -Is) watchdog: killing opencode pid $pid (age $((now-ts))s)"
      kill -TERM "$pid" 2>/dev/null
    fi
  done
  sleep 30
done
echo "watchdog: no more opencode processes, exiting"
