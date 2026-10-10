#!/bin/bash
set -u
WINE="/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
PREFIX="/var/home/Dcs102/lightburn/work/native/prefix"
EXE="$PREFIX/drive_c/Program Files/LightBurn/LightBurn.exe"
LOGDIR="/var/home/Dcs102/lightburn/work/native/vmp_dialog"
export WINEPREFIX="$PREFIX"
export DISPLAY=:0
export XAUTHORITY=/run/user/1000/xauth_smhqjo
export WINEDEBUG=-all
rm -f "$LOGDIR/hook.log"
# LD_PRELOAD + VMP_HOOK_LOG scoped to ONLY the wine process
env LD_PRELOAD="$LOGDIR/hook.so" VMP_HOOK_LOG="$LOGDIR/hook.log" \
  "$WINE" "$EXE" > "$LOGDIR/wine_stdout.log" 2>&1 &
WPID=$!
echo "launched wine pid=$WPID"
for i in $(seq 1 90); do
  sleep 0.5
  if [ -f "$LOGDIR/hook.log" ] && grep -qE "MessageBox|TaskDialog|DrawTextW|ExtTextOutW|TextOutW" "$LOGDIR/hook.log"; then
    echo "hook fired at ~$((i/2))s"; break
  fi
done
sleep 3
echo "=== windows ==="
wmctrl -lG 2>/dev/null | grep -iE "lightburn|dialog|error|#" || wmctrl -lG 2>/dev/null
echo "=== non-ctor hook.log lines ==="
grep -vE "SHIM LOADED" "$LOGDIR/hook.log" 2>/dev/null | head -80
echo "=== ctor count ==="; grep -c "SHIM LOADED" "$LOGDIR/hook.log" 2>/dev/null
echo "=== wine pid alive? ==="; kill -0 $WPID 2>/dev/null && echo "alive" || echo "dead"
