import os
import json, sys, time
from router import Grid, route_day
from segs import DAYS
from lib import hav
EXPORT=os.environ.get("OSM_EXPORT","osm-export.geojson")
HW={"track","path","footway","cycleway","bridleway","unclassified","residential","service","tertiary","secondary","primary","trunk"}
osm=[]
for f in json.load(open(EXPORT))["features"]:
    if f["properties"].get("highway") in HW and f["geometry"]["type"]=="LineString":
        osm.append([(c[1],c[0]) for c in f["geometry"]["coordinates"]])
osm+= [[tuple(p) for p in l] for l in json.load(open("roads.json"))]
osm+= [[tuple(p) for p in l] for l in json.load(open("greys.json"))]
old=json.load(open("tracks_old.json"))
def waypoints(segs, with_straight=False):
    w=[]; straight=set()
    for k,pts in segs:
        if k=="g":
            pts=[(-32.64797,18.94474),(-32.60619,18.98961)]
        pts=[tuple(p) for p in pts]
        if k in ("r","n","l"): sel=pts
        else:
            sel=[pts[0]]; acc=0
            for a,b in zip(pts,pts[1:]):
                acc+=hav(a,b)
                if acc>=700: sel.append(b); acc=0
            sel.append(pts[-1])
        for i,p in enumerate(sel):
            if not w or hav(w[-1],p)>40:
                w.append(p)
                if k=="l" and i>0: straight.add(len(w)-2)
    return (w,straight) if with_straight else w
days=sys.argv[1:] or [str(d) for d in DAYS]
res=json.load(open("tracks_new.json")) if len(sys.argv)>1 else {}
for d in days:
    t=time.time()
    REGUIDE={"8"}          # days whose waypoints changed a lot: use the waypoints as guide, wider corridor
    if d in REGUIDE:
        guide=waypoints(DAYS[int(d)]); G=Grid(guide,osm,buffer_m=900)
    else:
        guide=[tuple(p) for s in old[d] for p in s["c"]]; G=Grid(guide,osm)
    wps,st=waypoints(DAYS[int(d)],True); pieces=route_day(G,wps,st)
    res[d]=pieces
    L={k:0 for k in "onh"}
    for p in pieces: L[p["k"]]+=sum(hav(a,b) for a,b in zip(p["c"],p["c"][1:]))
    print("Day",d,"%.1f km  OSM %.1f  NGI %.1f  open %.1f  (%.0fs)"%(sum(L.values())/1000,L['o']/1000,L['n']/1000,L['h']/1000,time.time()-t),flush=True)
    json.dump(res,open("tracks_new.json","w"))
