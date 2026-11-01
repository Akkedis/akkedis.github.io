import sys,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ngi import *
from PIL import ImageDraw
def ov(lat,lon,z,r,out,day):
    import os; T=json.load(open(os.environ.get('TRK','tracks.json')))
    f=mosaic(lat,lon,z,r,out); im=Image.open(f).convert("RGB"); d=ImageDraw.Draw(im)
    cx,cy=tile(lat,lon,z); x0,y0=int(cx)-r,int(cy)-r
    pts=[]
    for s in T[str(day)]:
        pp=[((tile(a,b,z)[0]-x0)*256,(tile(a,b,z)[1]-y0)*256) for a,b in s["c"]]
        d.line(pp,fill=(255,0,200),width=3)
    im.save(f); return f
if __name__=="__main__":
    print(ov(float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],sys.argv[6]))
