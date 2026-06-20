import struct, numpy as np

# ---- target geometry (all mm, base-referenced) ----
LEN, TH = 75.0, 3.0
strpos = np.array([10,21,32,43,54,65], float)          # along length, bass->treble
crest  = np.array([6.42,6.72,6.92,6.83,6.52,5.61])     # base->crest height
qbreak = np.array([3.0,3.0,3.0,3.0,1.83,1.99])         # break dist from BACK face (q=0 back, q=3 front)

# crest height along length: quadratic (radius+tilt) fit, used for all p
A = np.vstack([strpos**2, strpos, np.ones_like(strpos)]).T
ca = np.linalg.lstsq(A, crest, rcond=None)[0]
Hc = lambda p: ca[0]*p*p + ca[1]*p + ca[2]
# break position along length: linear interp between strings, clamped at ends
def qb(p):
    return float(np.interp(p, strpos, qbreak, left=qbreak[0], right=qbreak[-1]))
C = 0.06  # gentle front-to-back crown curvature
def ztop(p,q):
    return Hc(p) - C*(q-qb(p))**2

# ---- grid ----
NP, NQ = 301, 25
ps = np.linspace(0,LEN,NP); qs = np.linspace(0,TH,NQ)
top = np.array([[ (ps[i],qs[j],ztop(ps[i],qs[j])) for j in range(NQ)] for i in range(NP)])
bot = np.array([[ (ps[i],qs[j],0.0)              for j in range(NQ)] for i in range(NP)])

tris=[]
def quad(a,b,c,d): tris.append((a,b,c)); tris.append((a,c,d))
# top (normals up)
for i in range(NP-1):
    for j in range(NQ-1):
        quad(top[i,j],top[i,j+1],top[i+1,j+1],top[i+1,j])
# bottom (normals down -> reverse)
for i in range(NP-1):
    for j in range(NQ-1):
        quad(bot[i,j],bot[i+1,j],bot[i+1,j+1],bot[i,j+1])
# walls
for i in range(NP-1):                      # q=0 (back) and q=TH (front)
    quad(bot[i,0],   bot[i+1,0],   top[i+1,0],   top[i,0])
    quad(bot[i,NQ-1],top[i,NQ-1],  top[i+1,NQ-1],bot[i+1,NQ-1])
for j in range(NQ-1):                      # p=0 (bass end) and p=LEN (treble end)
    quad(bot[0,j],   top[0,j],     top[0,j+1],   bot[0,j+1])
    quad(bot[NP-1,j],bot[NP-1,j+1],top[NP-1,j+1],top[NP-1,j])

# ---- write binary STL ----
def norm(t):
    v1=np.subtract(t[1],t[0]); v2=np.subtract(t[2],t[0]); n=np.cross(v1,v2)
    L=np.linalg.norm(n); return n/L if L else n
out="saddle_reference.stl"  # writes next to this script
with open(out,"wb") as f:
    f.write(b"\0"*80); f.write(struct.pack("<I",len(tris)))
    for t in tris:
        f.write(struct.pack("<3f",*norm(t)))
        for v in t: f.write(struct.pack("<3f",*v))
        f.write(struct.pack("<H",0))
print("triangles:",len(tris))
print("bbox  length %.1f  thick %.1f  height %.2f..%.2f"%(ps[-1],qs[-1],bot.min(),top[...,2].max()))
print("crest fit check (string pos -> model crest):")
for sp,cr in zip(strpos,crest):
    print("  p=%2d  target %.2f  model %.2f"%(sp,cr,Hc(sp)))
import os; print("file kb:", round(os.path.getsize(out)/1024,1))
