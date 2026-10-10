import ctypes, os, time, glob, struct
libc = ctypes.CDLL(None, use_errno=True)
PTRACE_ATTACH=16; PTRACE_DETACH=17; PTRACE_CONT=7; PTRACE_GETREGS=12
NT_PRSTATUS=1; PTRACE_GETREGSET=0x4204

def find_pid():
    for d in glob.glob('/proc/[0-9]*/comm'):
        try:
            if open(d).read().strip() == 'LightBurn.exe': return int(d.split('/')[2])
        except Exception: pass
    return None
pid=None
while not pid:
    pid=find_pid(); time.sleep(0.005)
print("pid",pid,flush=True)
libc.ptrace(ctypes.c_long(PTRACE_ATTACH),ctypes.c_long(pid),0,0)
os.waitpid(pid,0)
# try GETREGS with errno
regs=(ctypes.c_ulonglong*27)()
r=libc.ptrace(ctypes.c_long(PTRACE_GETREGS),ctypes.c_long(pid),0,ctypes.addressof(regs))
print("GETREGS ret",r,"errno",ctypes.get_errno(),flush=True)
# try GETREGSET NT_PRSTATUS
class iovec(ctypes.Structure):
    _fields_=[("base",ctypes.c_void_p),("len",ctypes.c_size_t)]
buf=(ctypes.c_ulonglong*27)()
iov=iovec(ctypes.addressof(buf),ctypes.sizeof(buf))
r2=libc.ptrace(ctypes.c_long(PTRACE_GETREGSET),ctypes.c_long(pid),ctypes.c_void_p(NT_PRSTATUS),ctypes.byref(iov))
print("GETREGSET ret",r2,"errno",ctypes.get_errno(),"rip",hex(buf[16]) if r2!=-1 else None,flush=True)
libc.ptrace(ctypes.c_long(PTRACE_DETACH),ctypes.c_long(pid),0,0)
print("done",flush=True)
