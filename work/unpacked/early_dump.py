import os, time, sys, glob
def find_pid():
    for d in glob.glob('/proc/[0-9]*/comm'):
        try:
            if open(d).read().strip()=='LightBurn.exe': return int(d.split('/')[2])
        except Exception: pass
    return None
pid=None; t0=time.time()
while not pid:
    pid=find_pid(); time.sleep(0.005)
mem=f"/proc/{pid}/mem"
def rd(va,n):
    with open(mem,'rb') as f:
        f.seek(va); return f.read(n)
# probe several .data addresses for first non-zero
probes=[0x1411c1000,0x1411D06F2,0x1411D08FE,0x141200000,0x141250000]
t=time.time()
hit=None
while time.time()-t0 < 15:
    vals=[rd(p,4) for p in probes]
    if any(v!=b'\0\0\0\0' for v in vals):
        hit=time.time()-t0
        print(f"first non-zero .data at t={hit:.4f}s",flush=True)
        break
    time.sleep(0.002)
if hit is None:
    print("no hit"); sys.exit(1)
SECS=[("headers",0x140000000,0x140001000),("text",0x140001000,0x1408d5000),
      ("rdata",0x1408d5000,0x1411c1000),("data",0x1411c1000,0x1412d3000),
      ("pdata",0x1412d3000,0x14132c000),("tls",0x14132c000,0x14132d000),
      ("rdata2",0x14132d000,0x14132e000),("reloc_rsrc",0x143248000,0x14324d000)]
for name,s,e in SECS:
    with open(mem,'rb') as f, open(f"work/unpacked/liveA_{name}.bin","wb") as o:
        f.seek(s); o.write(f.read(e-s))
print("dumped all sections",flush=True)
