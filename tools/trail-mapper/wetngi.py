import os
import sys, json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ngi import *; from lib import hav
cache={}
def px(lat,lon,z=15):
    x,y=tile(lat,lon,z); tx,ty=int(x),int(y)
    if (tx,ty) not in cache: cache[(tx,ty)]=fetch(z,tx,ty).convert("RGB")
    return cache[(tx,ty)], int((x-tx)*256), int((y-ty)*256)
def iswater(c): r,g,b=c; return 190<=r<=222 and 212<=g<=236 and b>=236
def wet(lat,lon):
    im,x,y=px(lat,lon); n=0
    for dx in (-2,0,2):
        for dy in (-2,0,2):
            xx=min(255,max(0,x+dx)); yy=min(255,max(0,y+dy)); n+=iswater(im.getpixel((xx,yy)))
    return n>=6
T=json.load(open(sys.argv[1]))
for d,segs in T.items():
    pts=[tuple(p) for s in segs for p in s["c"]]
    runs=[]; cum=0; cur=None
    for a,b in zip(pts,pts[1:]):
        L=hav(a,b); n=max(1,int(L//8))
        for i in range(n):
            p=(a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n); c=cum+L*i/n
            if wet(*p):
                if cur and c-cur[1]<25: cur[1]=c; cur[3]=p
                else: cur=[c,c,p,p]; runs.append(cur)
        cum+=L
    print("Day",d,[(round(r[0]/1000,2),round(r[1]-r[0]),(round(r[2][0],5),round(r[2][1],5)),(round(r[3][0],5),round(r[3][1],5))) for r in runs if r[1]-r[0]>=15])
