import ctypes, os, time, sys, glob
def find_pid():
    for d in glob.glob('/proc/[0-9]*/comm'):
        try:
            if open(d).read().strip()=='LightBurn.exe': return int(d.split('/')[2])
        except Exception: pass
    return None
delay=float(sys.argv[1]); tag=sys.argv[2]
pid=None; t0=time.time()
while not pid:
    pid=find_pid()
    if time.time()-t0>30: print("no pid"); sys.exit(1)
print(f"pid={pid} waiting {delay}s",flush=True)
time.sleep(delay)
mem=f"/proc/{pid}/mem"
def rd(va,n):
    with open(mem,'rb') as f:
        f.seek(va); return f.read(n)
G=rd(0x1411D06F2,4)          # P4 target global (3->6)
G2=rd(0x1411D08FE,4)         # P2 zeroed global
t0b=rd(0x140001000,16)       # .text start
print(f"[{tag}] G@0x1411D06F2={G.hex()} G2@0x1411D08FE={G2.hex()} text_start={t0b.hex()}",flush=True)
SECS=[("headers",0x140000000,0x140001000),("text",0x140001000,0x1408d5000),
      ("rdata",0x1408d5000,0x1411c1000),("data",0x1411c1000,0x1412d3000),
      ("pdata",0x1412d3000,0x14132c000),("tls",0x14132c000,0x14132d000),
      ("rdata2",0x14132d000,0x14132e000),("reloc_rsrc",0x143248000,0x14324d000)]
for name,s,e in SECS:
    with open(mem,'rb') as f, open(f"work/unpacked/{tag}_{name}.bin","wb") as o:
        f.seek(s); o.write(f.read(e-s))
print(f"[{tag}] dumped",flush=True)
