import mmap
from collections import Counter

TOR = "LightBurn 1.1.03 (x64) Multilingual/LightBurn 1.1.03 (x64) Multilingual/LightBurn-v1.1.03.exe"
REF = "bin/LightBurn-v1.1.03.exe"
with open(TOR,'rb') as f: t = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
with open(REF,'rb') as f: r = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
n = min(len(t),len(r))

# 1) verify all diffs are zero in torrent; count diff bytes
diff=0; nonzero_diff=0
CH=1<<20
for base in range(0,n,CH):
    e=min(base+CH,n); tb=t[base:e]; rb=r[base:e]
    for i in range(len(tb)):
        if tb[i]!=rb[i]:
            diff+=1
            if tb[i]!=0: nonzero_diff+=1
print("diff bytes:",diff,"  of which torrent!=0:",nonzero_diff)

# 2) build diff mask as bytearray (n bits -> use bytes for simplicity, n=47MB ok in mem)
mask=bytearray(n)
for base in range(0,n,CH):
    e=min(base+CH,n); tb=t[base:e]; rb=r[base:e]
    m=mask[base:e]
    for i in range(len(tb)):
        if tb[i]!=rb[i]: m[i]=1

# 3) runs of 1s
runs=[]; i=0
while i<n:
    if mask[i]:
        s=i
        while i<n and mask[i]: i+=1
        runs.append((s,i))
    else:
        i+=1
lens=[e-s for s,e in runs]
print("num runs:",len(runs)," total zeroed:",sum(lens))
import statistics
print("run len mean %.2f median %d min %d max %d"%(statistics.fmean(lens),statistics.median(lens),min(lens),max(lens)))
# percentiles
sl=sorted(lens)
def pct(p): return sl[int(p*len(sl))]
for p in (0.5,0.9,0.99,0.999,0.9999):
    print("  p%d = %d"%(int(p*100),pct(p)))

# 4) quantization: GCD of all run lengths (cap to avoid huge); and mod-small histogram
g=0
for L in lens[:20000]:
    import math; g=math.gcd(g,L)
print("gcd of first 20000 run lengths:",g)
for unit in (8,16,32,64,128,256,512):
    mult=sum(1 for L in lens if L%unit==0)
    print("  run len %% %d ==0 : %.2f%%"%(unit,100.0*mult/len(lens)))

# 5) structured vs independent-per-byte null model (p=diff/n)
p=diff/n
exp_run_mean=1.0/(1-p)
print("independent-per-byte expected run mean: %.3f  (observed %.2f)"%(exp_run_mean,statistics.fmean(lens)))
# autocorrelation at lags 1..8: fraction of i with mask[i]&mask[i+lag], vs p^2 baseline
for lag in (1,2,4,8,16,32):
    c=0; tot=0
    step=97  # sample to keep fast
    for i in range(0,n-lag,step):
        if mask[i]:
            tot+=1
            if mask[i+lag]: c+=1
    frac=c/tot if tot else 0
    print("  lag %2d: P(next|this)=%.4f   (independent baseline p=%.4f)"%(lag,frac,p))

# 6) run-start offset concentration at small grids
for grid in (4096,16384,65536):
    off=Counter(s%grid for s,e in runs)
    top=off.most_common(5)
    exp=len(runs)/grid
    print("mod %d: expected/bucket=%.1f  top=%s"%(grid,exp,top))
