#!/bin/bash
cd /var/home/Dcs102/lightburn
WINE="/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
export WINEPREFIX=/var/home/Dcs102/lightburn/work/native/prefix
export WINEASLR=0
export WINEDLLOVERRIDES="mscoree,mshtml="

cleanup_lb() {
  for p in /proc/[0-9]*/comm; do
    if [ "$(cat $p 2>/dev/null)" = "LightBurn.exe" ]; then
      kill -9 "$p" 2>/dev/null | sed 's|/proc/||; s|/comm||' >/dev/null
      PIDN=$(echo "$p" | sed 's|/proc/||; s|/comm||'); kill -9 "$PIDN" 2>/dev/null
    fi
  done
}

find_lb() {
  for p in /proc/[0-9]*/comm; do
    if [ "$(cat $p 2>/dev/null)" = "LightBurn.exe" ]; then
      echo "$p" | sed 's|/proc/||; s|/comm||'
      return
    fi
  done
}

for attempt in 1 2 3; do
  cleanup_lb; sleep 1
  "$WINE" "C:\\Program Files\\LightBurn\\LightBurn.exe" > work/unpacked/wineA.log 2>&1 &
  WINEPID=$!
  PID=""
  for i in $(seq 1 6000); do
    PID=$(find_lb)
    [ -n "$PID" ] && break
    sleep 0.005
  done
  if [ -z "$PID" ]; then echo "attempt $attempt: no child found"; kill $WINEPID 2>/dev/null; continue; fi
  echo "attempt $attempt: child pid=$PID"
  timeout 60 gdb -batch -p "$PID" -x work/unpacked/dumpA_cmds.txt > work/unpacked/dumpA.log 2>&1
  echo "gdb exit=$?"
  if grep -q "DUMP A DONE" work/unpacked/dumpA.log; then echo SUCCESS; break; fi
done
kill $WINEPID 2>/dev/null
cleanup_lb
echo done
