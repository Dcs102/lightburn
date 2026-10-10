#!/bin/bash
cd /var/home/Dcs102/lightburn
WINE="/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
export WINEPREFIX=/var/home/Dcs102/lightburn/work/native/prefix WINEASLR=0 WINEDLLOVERRIDES="mscoree,mshtml="
rm -f work/unpacked/liveA_*.bin
for p in /proc/[0-9]*/comm; do [ "$(cat $p 2>/dev/null)" = "LightBurn.exe" ] && kill -9 $(echo "$p" | sed 's|/proc/||; s|/comm||') 2>/dev/null; done
sleep 1
python3 work/unpacked/ptrace_dumpA.py > work/unpacked/dumpA.log 2>&1 &
PYPID=$!
sleep 0.3
"$WINE" "C:\\Program Files\\LightBurn\\LightBurn.exe" > work/unpacked/wineA.log 2>&1 &
wait $PYPID
echo "poller exit=$?"
