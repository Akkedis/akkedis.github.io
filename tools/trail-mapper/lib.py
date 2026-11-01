import json, urllib.request, math, time
UA={"User-Agent":"akkedis-trailmap/1.0 (github.com/akkedis)"}
def hav(a,b):
    R=6371000; la1,lo1=map(math.radians,a); la2,lo2=map(math.radians,b)
    d=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*R*math.asin(math.sqrt(d))
def route(pts, profile="foot"):
    c=";".join("%f,%f"%(lo,la) for la,lo in pts)
    u="https://routing.openstreetmap.de/routed-%s/route/v1/driving/%s?overview=full&geometries=geojson&steps=true&continue_straight=false"%(profile,c)
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=90))
        except Exception as e: err=e; time.sleep(2*(i+1))
    raise err
def sample(coords, every=1000):
    out=[(0,coords[0])]; cum=0; nxt=every
    for a,b in zip(coords,coords[1:]):
        cum+=hav(a,b)
        if cum>=nxt: out.append((cum,b)); nxt+=every
    return out, cum
