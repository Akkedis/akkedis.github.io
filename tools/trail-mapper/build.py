import os
import json,sys; from lib import *; from segs import DAYS
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import net
ADJ,_=net.load()
def netroute(pts):
    co=[]
    for a,b in zip(pts,pts[1:]):
        crow=hav(a,b)
        p,d,(s0,t0)=net.path(ADJ,a,b)
        cand=[]
        if p is not None: cand.append(("net",d+hav(a,s0)+hav(b,t0),[a]+p+[b]))
        try:
            r=route([a,b]); rc=[(round(y,5),round(x,5)) for x,y in r["routes"][0]["geometry"]["coordinates"]]
            cand.append(("osrm",r["routes"][0]["distance"]+hav(a,rc[0])+hav(b,rc[-1]),[a]+rc+[b]))
        except Exception: pass
        cand.sort(key=lambda c:c[1])
        if cand and cand[0][1] <= max(1.7*crow, crow+800):
            src,d,seg=cand[0]
        else:
            src,d,seg="line",crow,[a,b]; HAND.append((a,b))
        print('   %s %s->%s %.2f km (crow %.2f)'%(src,a,b,d/1000,crow/1000))
        co.append(("h" if src=="line" else "m", seg))
    return co
HAND=[]
def greys():
    g=json.load(open("greys.json"))
    w2=g[1] if g[1][0][0]<g[1][-1][0] else g[1][::-1]
    w1=g[0] if g[0][0][0]<g[0][-1][0] else g[0][::-1]
    return w2+[(-32.6230,18.9530)]+w1
res={}
for d,segs in DAYS.items():
    out=[]; last=None
    for kind,pts in segs:
        pieces=[]
        if kind=="r":
            r=route(pts); pieces=[("m",[(round(y,5),round(x,5)) for x,y in r["routes"][0]["geometry"]["coordinates"]])]
        elif kind=="n": pieces=netroute(pts)
        elif kind=="t": pieces=[("t",list(pts))]
        elif kind=="g": pieces=[("m",greys())]
        else: pieces=[("h",list(pts))]
        for k,co in pieces:
            co=[tuple(p) for p in co]
            if last and hav(last,co[0])>30: out.append({"k":"h","c":[last,co[0]]})
            if out and out[-1]["k"]==k: out[-1]["c"]+= co[1:] if hav(out[-1]["c"][-1],co[0])<30 else co
            else: out.append({"k":k,"c":co})
            last=co[-1]
    tot=sum(hav(a,b) for s in out for a,b in zip(s["c"],s["c"][1:]))
    hand=sum(hav(a,b) for s in out if s["k"]=="h" for a,b in zip(s["c"],s["c"][1:]))
    res[d]=out
    print("Day",d,"%.1f km (hand-drawn %.1f km)"%(tot/1000,hand/1000))
json.dump(res,open("tracks.json","w"))
