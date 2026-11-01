import json; from lib import *
T=json.load(open("tracks.json")); E=json.load(open("elev.json"))
def dp(pts,eps):
    # Douglas-Peucker in metres (equirectangular)
    import math
    if len(pts)<3: return pts
    k=111320; c=math.cos(math.radians(pts[0][0]))
    def dist(p,a,b):
        ax,ay=(a[1])*k*c,a[0]*k; bx,by=b[1]*k*c,b[0]*k; px,py=p[1]*k*c,p[0]*k
        dx,dy=bx-ax,by-ay
        if dx==dy==0: return math.hypot(px-ax,py-ay)
        t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
        return math.hypot(px-ax-t*dx,py-ay-t*dy)
    stack=[(0,len(pts)-1)]; keep={0,len(pts)-1}
    while stack:
        i,j=stack.pop(); m,idx=0,None
        for x in range(i+1,j):
            d=dist(pts[x],pts[i],pts[j])
            if d>m: m,idx=d,x
        if idx and m>eps: keep.add(idx); stack+= [(i,idx),(idx,j)]
    return [pts[i] for i in sorted(keep)]
# Landmarks: day, name, lat, lon, src ('osm' = position from OpenStreetMap, 'est' = estimated from booklet)
L=[
(1,"Start: old Piekenierskloof Pass (Grey's Pass)","Begin: ou Piekenierskloofpas (Grey’s Pass)",-32.64797,18.94474,"osm"),
(1,"Grey's Pass meets the tar road","Grey’s Pass sluit by die teerpad aan",-32.60619,18.98961,"osm"),
(1,"Citrusdal – main road through town / 4-way crossing","Citrusdal – hoofpad deur die dorp / 4-rigting-kruising",-32.5939,19.0166,"osm"),
(1,"Allandale turn-off (R303)","Allandale-afdraai (R303)",-32.6316,19.0798,"ngi"),
(1,"Fairview","Fairview",-32.64983,19.09029,"ngi"),
(1,"Allandale – overnight huts (≈4 km from the road)","Allandale – oornag-kothuise (±4 km van die pad)",-32.66268,19.1061,"sat"),
(2,"Tuinskloof","Tuinskloof",-32.64409,19.18013,"ngi"),
(2,"Ysterplaat – turn left","Ysterplaat – draai links",-32.6555,19.2111,"ngi"),
(2,"Ysterplaat – Ouma se Huis","Ysterplaat – Ouma se Huis",-32.65325,19.21233,"ngi"),
(3,"Kunje (Keunje) – turn right at the entrance","Kunje – draai regs by die ingang",-32.6721,19.2110,"ngi"),
(3,"Die Hoek – T-junction, turn right onto the tar","Die Hoek – T-aansluiting, draai regs in die teer",-32.70491,19.21904,"ngi"),
(3,"Die Straadt – turn left, after 500 m right","De Straadt – draai links, na 500 m regs",-32.71787,19.23553,"ngi"),
(3,"Destraadt Dam","Destraadt-dam",-32.7212,19.2414,"ngi"),
(3,"Turn right, after 350 m left","Draai regs, na 350 m links",-32.7491,19.25285,"est"),
(3,"Cross the old dam wall, then left at the sign","Stap oor die ou damwal, dan links by die bordjie",-32.74946,19.25594,"sat"),
(3,"Orchard / Tandfontein homestead","Boord / Tandfontein-opstal",-32.76418,19.25358,"ngi"),
(3,"Tandfontein entrance – left onto the tar for 4.5 km","Tandfontein se ingang – links in die teer vir 4,5 km",-32.7767,19.2419,"ngi"),
(3,"Schoongezicht turn-off (R303)","Schoongezicht-afdraai (R303)",-32.8151,19.2616,"osm"),
(3,"Schoongezicht / Skoongesig campsite – overnight","Schoongezicht / Skoongesig-kampterrein – oornag",-32.81739,19.21719,"osm"),
(4,"Bokfontein turn-off – turn left, gravel road downhill","Bokfontein-afdraai – draai links, grondpad bult af",-32.8196,19.2663,"ngi"),
(4,"Wall between the two dams","Damwal tussen die twee damme",-32.82161,19.27534,"ngi"),
(4,"Heldersig","Heldersig",-32.82906,19.29052,"ngi"),
(4,"Langrivier (river) – walk downstream","Langrivier (rivier) – stap rivier-af",-32.83406,19.30281,"ngi"),
(4,"Langrivier (farm)","Langrivier (plaas)",-32.84794,19.31965,"ngi"),
(4,"Libertas (farm)","Libertas (plaas)",-32.85351,19.32875,"osm"),
(4,"De Meul","De Meul",-32.89625,19.35252,"osm"),
(4,"Gate on the left – follow the fence","Hek aan die linkerkant – volg die draadheining",-32.89573,19.33113,"ngi"),
(4,"Menoegaa campsite (farm Kalifornië)","Menoegaa-kampterrein (plaas Kalifornië)",-32.92067,19.32483,"web"),
(6,"Gate – go straight, follow the power lines","Hek – stap reguit, volg die kraglyne",-32.90575,19.33993,"ngi"),
(6,"Tweefontein (farm)","Tweefontein (plaas)",-32.90814,19.36464,"ngi"),
(6,"Cycle path – steep zig-zag climb (approx.)","Fietspad – stywe zig-zag-klim (ongeveer)",-32.9400,19.3790,"est"),
(6,"Tar road near Môrester","Teerpad by Môrester",-32.9751,19.3869,"ngi"),
(6,"Boplaas (Boerneef's farm) – on your right","Boplaas (Boerneef se plaas) – aan jou regterkant",-32.9761,19.36536,"ngi"),
(6,"Uitkyk – left in, then right","Uitkyk – links in, dan regs",-32.98309,19.36482,"ngi"),
(6,"Bronaar – offices and packhouse","Bronaar – kantore en pakstoor",-32.99301,19.36452,"ngi"),
(6,"Straatdrif – cross the Houdenbeksrivier","Straatdrif – oor die Hou-den-Bek-rivier",-33.01219,19.35624,"ngi"),
(6,"T-junction – right onto the gravel road","T-aansluiting – regs op die grondpad",-33.02155,19.35988,"ngi"),
(6,"Rotstuin","Rotstuin",-33.02176,19.35173,"ngi"),
(6,"Welbedag","Welbedag",-33.02414,19.34187,"ngi"),
(6,"Wadrift (Wadrif)","Wadrift (Wadrif)",-33.02799,19.32869,"ngi"),
(7,"Gravel road joins the R303","Grondpad sluit by die R303 aan",-33.0546,19.3289,"ngi"),
(7,"Wood Yard","Wood Yard",-33.0627,19.33079,"ngi"),
(7,"De Hoek – pedestrian gate","De Hoek – voetgangerhek",-33.0739,19.3435,"ngi"),
(7,"De Hoek dams – keep to the right-hand wall","De Hoek-damme – hou op die regterkantse wal",-33.0767,19.3482,"ngi"),
(7,"Rocklands Groot Dam","Rocklands Groot-dam",-33.09542,19.34692,"osm"),
(7,"Kaleo guest farm (Malabar)","Kaleo-gasteplaas (Malabar)",-33.14493,19.37084,"osm"),
(8,"T-junction with the R303 – cross straight over","T-aansluiting met die R303 – stap reguit oor",-33.18422,19.33139,"ngi"),
(8,"Bokveldskloof – corner of the orchard, climb through the fence","Bokveldskloof – punt van die boord, klim deur die draad",-33.18483,19.33053,"ngi"),
(8,"Vlei Dam (Groot) on your right, orchard on your left","Vlei-dam (Groot) aan jou regterkant, boord aan jou linkerkant",-33.18871,19.33044,"ngi"),
(8,"Left at the end of the orchard, onto the dam wall","Links aan die einde van die boord, op die damwal",-33.19363,19.3286,"ngi"),
(8,"Witzenberg substation – do NOT take the path around it","Witzenberg-kragstasie – MOENIE die pad rondom dit neem nie",-33.2285,19.3179,"osm"),
(8,"Slagboom – Sip Café","Slagboom – Sip Café",-33.24261,19.28218,"osm"),
(9,"Ouplaas – left at the gate","Ouplaas – links by die hek",-33.26212,19.22935,"ngi"),
(9,"Big dam at the foot of the mountain (Hartbeesvlei)","Groot dam aan die voet van die berg (Hartbeesvlei)",-33.2651,19.2209,"ngi"),
(9,"Crest (≈1,030 m) – path splits, keep left downhill","Kruin (±1 030 m) – pad verdeel, hou links berg-af",-33.26672,19.21607,"ngi"),
(9,"Old wagon road west – Tulbagh in view","Ou wapad wes – Tulbagh in sig",-33.26998,19.20073,"ngi"),
(9,"Witzenberg (farm) – bottom of the pass","Witzenberg (plaas) – onderkant van die pas",-33.27249,19.19044,"ngi"),
(9,"Dennelaan – farm buildings, left onto gravel","Dennelaan – plaasgeboue, links op grondpad",-33.27043,19.16599,"ngi"),
(9,"Kruisvallei","Kruisvallei",-33.27331,19.15835,"ngi"),
(9,"Obiqua prison","Obiqua-gevangenis",-33.27508,19.14694,"ngi"),
(9,"T-junction – left onto the tar road","T-aansluiting – links in die teerpad",-33.2745,19.1440,"ngi"),
(9,"NG Kerk Tulbagh – THE END","NG Kerk Tulbagh – DIE EINDE",-33.2822,19.1408,"ngi"),
]
out={"days":{},"marks":[]}
for d,segs in T.items():
    full=[tuple(p) for s in segs for p in s["c"]]
    out["days"][d]={"segs":[{"k":s["k"],"c":[[round(a,5),round(b,5)] for a,b in dp([tuple(p) for p in s["c"]],6)]} for s in segs],
                    "km":E[d]["km"],"up":E[d]["up"],"down":E[d]["down"],"min":E[d]["min"],"max":E[d]["max"],
                    "prof":E[d]["profile"]}
    # cumulative distances for landmark snapping
    cum=[0]
    for a,b in zip(full,full[1:]): cum.append(cum[-1]+hav(a,b))
    for m in L:
        if str(m[0])!=d: continue
        i=min(range(len(full)),key=lambda i:hav(full[i],(m[3],m[4])))
        off=hav(full[i],(m[3],m[4]))
        out["marks"].append({"d":m[0],"n":m[1],"na":m[2],"ll":[m[3],m[4]],"src":m[5],"km":round(cum[i]/1000,1),"off":round(off)})
# Day 2 pass top
p=max(E["2"]["profile"],key=lambda x:x[1]); print("Day2 top",p)
json.dump(out,open("data.json","w"),separators=(",",":"))
import os; print(os.path.getsize("data.json"),"bytes")
for m in out["marks"]: print(m["d"],m["km"],m["off"],m["n"])
