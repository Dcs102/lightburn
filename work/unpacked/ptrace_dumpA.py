import ctypes, os, time, sys, glob

libc = ctypes.CDLL(None, use_errno=True)
PTRACE_SYSCALL=24; PTRACE_ATTACH=16; PTRACE_DETACH=17
NT_PRSTATUS=1; PTRACE_GETREGSET=0x4204

EP = 0x140839f2c
TEXT_LO, TEXT_HI = 0x140001000, 0x1408d5000
OUT = "/var/home/Dcs102/lightburn/work/unpacked"
SECS = [
 ("headers",    0x140000000, 0x140001000),
 ("text",       0x140001000, 0x1408d5000),
 ("rdata",      0x1408d5000, 0x1411c1000),
 ("data",       0x1411c1000, 0x1412d3000),
 ("pdata",      0x1412d3000, 0x14132c000),
 ("tls",        0x14132c000, 0x14132d000),
 ("rdata2",     0x14132d000, 0x14132e000),
 ("reloc_rsrc", 0x143248000, 0x14324d000),
]

class iovec(ctypes.Structure):
    _fields_=[("base",ctypes.c_void_p),("len",ctypes.c_size_t)]

def ptrace(req,pid,addr=0,data=0):
    return libc.ptrace(ctypes.c_long(req),ctypes.c_long(pid),ctypes.c_void_p(addr),ctypes.c_void_p(data))

def get_rip(tid):
    buf=(ctypes.c_ulonglong*27)()
    iov=iovec(ctypes.addressof(buf),ctypes.sizeof(buf))
    if libc.ptrace(ctypes.c_long(PTRACE_GETREGSET),ctypes.c_long(tid),ctypes.c_void_p(NT_PRSTATUS),ctypes.byref(iov))==-1:
        return None
    return buf[16]

def dump_all(pid):
    mem=f"/proc/{pid}/mem"
    for name,s,e in SECS:
        with open(mem,"rb") as f, open(f"{OUT}/liveA_{name}.bin","wb") as o:
            f.seek(s); o.write(f.read(e-s))
        print(f"dumped {name}: {e-s} bytes",flush=True)

def find_pid():
    for d in glob.glob('/proc/[0-9]*/comm'):
        try:
            if open(d).read().strip()=='LightBurn.exe': return int(d.split('/')[2])
        except Exception: pass
    return None

def main():
    pid=None
    while not pid:
        pid=find_pid(); time.sleep(0.005)
    print(f"found pid={pid}",flush=True)
    ptrace(PTRACE_ATTACH,pid); os.waitpid(pid,0)
    print("attached",flush=True)
    ptrace(PTRACE_SYSCALL,pid)
    prev_rip=None; steps=0
    while True:
        try: p,st=os.waitpid(pid,0)
        except ChildProcessError:
            print("process exited before hit",flush=True); break
        rip=get_rip(pid)
        if rip is None:
            ptrace(PTRACE_SYSCALL,pid); continue
        steps+=1
        in_text=TEXT_LO<=rip<TEXT_HI
        prev_in=(prev_rip is not None and TEXT_LO<=prev_rip<TEXT_HI)
        if in_text and not prev_in:
            print(f"TRANSITION to .text rip={hex(rip)} (EP+{rip-EP:#x}) steps={steps}",flush=True)
            dump_all(pid); break
        if steps%5000==0: print(f"  polling rip={hex(rip)} steps={steps}",flush=True)
        prev_rip=rip
        ptrace(PTRACE_SYSCALL,pid)
    ptrace(PTRACE_DETACH,pid,0,0)
    print("detached",flush=True)

main()
