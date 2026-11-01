import os
import sys,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ngi import tile, fetch; from lib import hav
cache={}
def img(tx,ty):
    if (tx,ty) not in cache: cache[(tx,ty)]=fetch(15,tx,ty).convert("RGB")
    return cache[(tx,ty)]
def isline(c):
    r,g,b=c
    return max(r,g,b)<110 or (r>150 and g<120 and b<110)
def near_line(lat,lon,R=6):
    x,y=tile(lat,lon,15)
    for dx in range(-R,R+1,1):
        for dy in range(-R,R+1,1):
            if dx*dx+dy*dy>R*R: continue
            X=x*256+dx; Y=y*256+dy; tx,ty=int(X//256),int(Y//256)
            if isline(img(tx,ty).getpixel((int(X%256),int(Y%256)))): return True
    return False
T=json.load(open(sys.argv[1])); out={}
for d,segs in T.items():
    pts=[tuple(p) for s in segs for p in s["c"]]
    runs=[]; cum=0; cur=None
    for a,b in zip(pts,pts[1:]):
        L=hav(a,b); n=max(1,int(L//15))
        for i in range(n):
            p=(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n); c=cum+L*i/n
            if not near_line(*p):
                if cur and c-cur[1]<40: cur[1]=c; cur[3]=p
                else: cur=[c,c,p,p]; runs.append(cur)
        cum+=L
    bad=[(round(r[0]/1000,2),round(r[1]-r[0]),r[2],r[3]) for r in runs if r[1]-r[0]>=120]
    out[d]=bad
    print("Day",d,len(bad),"runs:",[(b[0],b[1]) for b in bad])
json.dump(out,open("offtrack.json","w"))
