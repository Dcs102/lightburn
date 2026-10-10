import os, time, sys, glob
def find_pid():
    for d in glob.glob('/proc/[0-9]*/comm'):
        try:
            if open(d).read().strip()=='LightBurn.exe': return int(d.split('/')[2])
        except Exception: pass
    return None
pid=None; t0=time.time()
while not pid:
    pid=find_pid(); time.sleep(0.01)
mem=f"/proc/{pid}/mem"
def rd(va,n):
    with open(mem,'rb') as f:
        f.seek(va); return f.read(n)
last=None
t=time.time()
while time.time()-t0 < 12:
    G=rd(0x1411D06F2,4).hex()
    G2=rd(0x1411D08FE,4).hex()
    ts=rd(0x140001000,4).hex()
    cur=(G,G2)
    el=time.time()-t0
    if cur!=last:
        print(f"t={el:.3f} G={G} G2={G2} text={ts}",flush=True)
        last=cur
    time.sleep(0.02)
