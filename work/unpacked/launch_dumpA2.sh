#!/bin/bash
# Launch app, attach gdb (holds process), scan for PEB while stopped, write phase2, let gdb continue.
cd /var/home/Dcs102/lightburn
WINE="/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
export WINEPREFIX=/var/home/Dcs102/lightburn/work/native/prefix WINEASLR=0 WINEDLLOVERRIDES="mscoree,mshtml="
rm -f work/unpacked/liveA_*.bin work/unpacked/peb_found.txt
for attempt in 1 2 3; do
  for p in /proc/[0-9]*/comm; do [ "$(cat $p 2>/dev/null)" = "LightBurn.exe" ] && kill -9 $(echo "$p" | sed 's|/proc/||; s|/comm||') 2>/dev/null; done
  sleep 1
  "$WINE" "C:\\Program Files\\LightBurn\\LightBurn.exe" > work/unpacked/wineA.log 2>&1 &
  PID=""
  for i in $(seq 1 400); do
    for p in /proc/[0-9]*/comm; do [ "$(cat $p 2>/dev/null)" = "LightBurn.exe" ] && PID=$(echo "$p" | sed 's|/proc/||; s|/comm||'); done
    [ -n "$PID" ] && break
    sleep 0.02
  done
  [ -z "$PID" ] && { echo "attempt $attempt: no child"; continue; }
  echo "attempt $attempt: child pid=$PID"
  gdb -batch -p "$PID" -x work/unpacked/phase1.txt > work/unpacked/dumpA.log 2>&1 &
  GDBPID=$!
  sleep 3
  python3 work/unpacked/find_peb2.py "$PID" > work/unpacked/peb_found.txt 2>&1
  PEB=$(grep -oP 'PEB=\K0x[0-9a-f]+' work/unpacked/peb_found.txt | head -1)
  if [ -z "$PEB" ]; then echo "attempt $attempt: no PEB found"; cat work/unpacked/peb_found.txt; kill $GDBPID 2>/dev/null; wait $GDBPID 2>/dev/null; continue; fi
  echo "attempt $attempt: PEB=$PEB"
  cat > work/unpacked/phase2.txt <<PGDB
set *(unsigned char*)($pebvar + 2) = 0
set *(int*)($pebvar + 0xbc) = 0
echo === PEB CLEARED @ $PEB ===
hbreak *0x140839f2c
commands 1
silent
echo \n=== EP HIT ===\n
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_headers.bin 0x140000000 0x140001000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_text.bin 0x140001000 0x1408d5000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_rdata.bin 0x1408d5000 0x1411c1000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_data.bin 0x1411c1000 0x1412d3000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_pdata.bin 0x1412d3000 0x14132c000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_tls.bin 0x14132c000 0x14132d000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_rdata2.bin 0x14132d000 0x14132e000
dump memory /var/home/Dcs102/lightburn/work/unpacked/liveA_reloc_rsrc.bin 0x143248000 0x14324d000
echo \n=== DUMP A DONE ===\n
detach
quit
end
continue
PGDB
  sed -i "1i set \$pebvar = $PEB" work/unpacked/phase2.txt
  wait $GDBPID
  echo "gdb exit=$?"
  if grep -q "DUMP A DONE" work/unpacked/dumpA.log; then echo SUCCESS; break; fi
done
