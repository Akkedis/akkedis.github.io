import json; from lib import *
T=json.load(open("tracks.json"))
for d,segs in T.items():
    pts=[(tuple(p),s["k"]) for s in segs for p in s["c"]]
    cum=[0]
    for (a,_),(b,_) in zip(pts,pts[1:]): cum.append(cum[-1]+hav(a,b))
    found=[]
    i=0
    while i<len(pts):
        for j in range(i+2,len(pts)):
            along=cum[j]-cum[i]
            if along>3000: break
            if along>200 and hav(pts[i][0],pts[j][0])<25:
                found.append((round(cum[i]/1000,2),round(along),pts[i][0])); i=j; break
        i+=1
    print("Day",d,"spurs:",found)
