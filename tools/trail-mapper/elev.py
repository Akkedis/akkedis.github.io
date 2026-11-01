import json,time,urllib.request; from lib import *
T=json.load(open("tracks.json")); out={}
for d,segs in T.items():
    co=[tuple(p) for s in segs for p in s["c"]]
    # resample every 100 m
    pts=[(0,co[0])]; cum=0; nxt=100
    for a,b in zip(co,co[1:]):
        seg=hav(a,b)
        while cum+seg>=nxt and seg>0:
            f=(nxt-cum)/seg; pts.append((nxt,(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f))); nxt+=100
        cum+=seg
    pts.append((cum,co[-1]))
    el=[]
    for i in range(0,len(pts),100):
        chunk=pts[i:i+100]; loc="|".join("%.5f,%.5f"%p for _,p in chunk)
        for t in range(5):
            try:
                r=json.load(urllib.request.urlopen(urllib.request.Request("https://api.opentopodata.org/v1/srtm30m?locations="+loc,headers=UA),timeout=60)); break
            except Exception as e: time.sleep(3*(t+1))
        el+=[x["elevation"] for x in r["results"]]; time.sleep(1.2)
    prof=[[round(dd/1000,2),round(e)] for (dd,_),e in zip(pts,el) if e is not None]
    # ascent with smoothing (5-pt moving average)
    es=[e for _,e in prof]; sm=[sum(es[max(0,i-2):i+3])/len(es[max(0,i-2):i+3]) for i in range(len(es))]
    up=sum(max(0,b-a) for a,b in zip(sm,sm[1:])); dn=sum(max(0,a-b) for a,b in zip(sm,sm[1:]))
    out[d]={"profile":prof,"km":round(cum/1000,1),"up":round(up),"down":round(dn),"min":min(es),"max":max(es)}
    print("Day",d,out[d]["km"],"km  +%d / -%d m  range %d–%d m"%(up,dn,min(es),max(es)))
json.dump(out,open("elev.json","w"))
