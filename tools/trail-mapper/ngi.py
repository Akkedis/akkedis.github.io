import os
import math, sys, os, urllib.request, io
from PIL import Image
D=os.environ.get("TILE_CACHE","tile-cache")
def tile(lat,lon,z):
    n=2**z; x=(lon+180)/360*n
    y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
    return x,y
def fetch(z,x,y):
    f=f"{D}/{z}_{x}_{y}.png"
    if os.path.exists(f): return Image.open(f)
    ty=2**z-1-y
    u=f"https://htonl.dev.openstreetmap.org/ngi-tiles/tiles/50k/{z}/{x}/{ty}.png"
    try:
        data=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"akkedis-trailmap/1.0"}),timeout=30).read()
        open(f,"wb").write(data); return Image.open(io.BytesIO(data))
    except Exception as e:
        return Image.new("RGB",(256,256),(230,230,230))
def mosaic(lat,lon,z=15,r=2,out="m.png",marks=()):
    cx,cy=tile(lat,lon,z); x0,y0=int(cx)-r,int(cy)-r; n=2*r+1
    im=Image.new("RGB",(256*n,256*n))
    for i in range(n):
        for j in range(n):
            im.paste(fetch(z,x0+i,y0+j).convert("RGB"),(256*i,256*j))
    from PIL import ImageDraw; d=ImageDraw.Draw(im)
    for (la,lo,lab) in marks:
        px,py=tile(la,lo,z); px=(px-x0)*256; py=(py-y0)*256
        d.ellipse([px-7,py-7,px+7,py+7],outline=(255,0,255),width=3); d.text((px+9,py-6),lab,fill=(255,0,255))
    im.save(f"{D}/{out}"); return f"{D}/{out}"
if __name__=="__main__":
    la,lo,z,r,out=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
    print(mosaic(la,lo,z,r,out))
def px2ll(clat,clon,z,r,px,py):
    cx,cy=tile(clat,clon,z); x0,y0=int(cx)-r,int(cy)-r
    n=2**z; X=x0+px/256; Y=y0+py/256
    lon=X/n*360-180; lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*Y/n))))
    return round(lat,5),round(lon,5)
