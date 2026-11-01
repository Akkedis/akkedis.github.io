import os
import sys,os,io,math,json,urllib.request
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ngi import tile, D
from PIL import Image, ImageDraw
def fetch(z,x,y):
    f=f"{D}/sat_{z}_{x}_{y}.jpg"
    if not os.path.exists(f):
        u=f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        open(f,"wb").write(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"akkedis-trailmap/1.0"}),timeout=30).read())
    return Image.open(f).convert("RGB")
def mosaic(lat,lon,z,r,out,day=None,marks=()):
    cx,cy=tile(lat,lon,z); x0,y0=int(cx)-r,int(cy)-r; n=2*r+1
    im=Image.new("RGB",(256*n,256*n))
    for i in range(n):
        for j in range(n): im.paste(fetch(z,x0+i,y0+j),(256*i,256*j))
    d=ImageDraw.Draw(im)
    P=lambda a,b:((tile(a,b,z)[0]-x0)*256,(tile(a,b,z)[1]-y0)*256)
    if day:
        T=json.load(open('tracks.json'))
        for s in T[str(day)]: d.line([P(a,b) for a,b in s["c"]],fill=(255,0,200),width=3)
    for a,b,l in marks:
        x,y=P(a,b); d.ellipse([x-6,y-6,x+6,y+6],outline=(0,255,255),width=2); d.text((x+8,y-6),l,fill=(0,255,255))
    im.save(f"{D}/{out}"); return f"{D}/{out}"
def px2ll(lat,lon,z,r,px,py):
    cx,cy=tile(lat,lon,z); x0,y0=int(cx)-r,int(cy)-r; n=2**z
    X=x0+px/256; Y=y0+py/256
    return round(math.degrees(math.atan(math.sinh(math.pi*(1-2*Y/n)))),5), round(X/n*360-180,5)
