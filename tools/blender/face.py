# Paints the kid's face/atlas texture (1024x1024). Head UVs use the upper-left quadrant
# as a front projection of the face; the bottom-right 64x64 corner is plain white for
# everything coloured by vertex colours.
import numpy as np, math, sys
from PIL import Image, ImageDraw, ImageFilter
S=1024; H=512   # face quadrant size
SKIN=(250,222,198)
def paint(path):
    img=Image.new('RGBA',(S,S),SKIN+(255,))
    d=ImageDraw.Draw(img,'RGBA')
    # face quadrant: u in [0,0.5], v in [0.5,1]  -> pixel x 0..512, y 0..512 (top)
    # mapping from head coords: u=x/0.34+0.5 over quadrant, v=(z-1.27)/0.34
    def P(x,z):  # head-space metres -> pixel in quadrant
        u=x/0.34+0.5; v=(z-1.27)/0.34
        return (u*H, (1-v)*H)
    # blush
    for sx in(-1,1):
        cx,cy=P(sx*0.068,1.395)
        blush=Image.new('RGBA',(S,S),(0,0,0,0)); bd=ImageDraw.Draw(blush)
        bd.ellipse([cx-26,cy-12,cx+26,cy+12],fill=(255,140,140,110))
        img=Image.alpha_composite(img,blush.filter(ImageFilter.GaussianBlur(7)))
    d=ImageDraw.Draw(img,'RGBA')
    for sx in(-1,1):
        cx,cy=P(sx*0.056,1.437)
        w,h=42,56
        # white of the eye (rounded), iris, pupil, highlights
        d.ellipse([cx-w*0.62,cy-h*0.5,cx+w*0.62,cy+h*0.52],fill=(255,255,255,255))
        iris=Image.new('RGBA',(S,S),(0,0,0,0)); idr=ImageDraw.Draw(iris)
        for k in range(14):
            t=k/13
            c=(int(60+40*t),int(40+28*t),int(36+20*t),255)
            idr.ellipse([cx-w*0.42*(1-t*0.05),cy-h*0.46+h*0.92*t*0.0,cx+w*0.42*(1-t*0.05),cy+h*0.5],fill=c) if k==0 else None
        img=Image.alpha_composite(img,iris); d=ImageDraw.Draw(img,'RGBA')
        # gradient iris: dark top, warm brown bottom
        for i in range(int(h*0.96)):
            t=i/(h*0.96); yy=cy-h*0.46+i
            half=w*0.42*math.sqrt(max(0,1-((yy-cy-h*0.02)/(h*0.49))**2))
            c=(int(45+70*t),int(32+45*t),int(34+30*t),255)
            d.line([(cx-half,yy),(cx+half,yy)],fill=c)
        d.ellipse([cx-w*0.17,cy-h*0.12,cx+w*0.17,cy+h*0.2],fill=(25,18,22,255))
        d.ellipse([cx-w*0.32+sx*2,cy-h*0.36,cx-w*0.02+sx*2,cy-h*0.06],fill=(255,255,255,245))
        d.ellipse([cx+w*0.12,cy+h*0.14,cx+w*0.26,cy+h*0.28],fill=(255,255,255,200))
        # upper lid: a bold dark line with a little flick at the outer corner
        pts=[(cx-w*0.68,cy-h*0.28),(cx-w*0.3,cy-h*0.55),(cx+w*0.3,cy-h*0.55),(cx+w*0.66,cy-h*0.3)]
        if sx<0: pts=[(2*cx-x,y) for x,y in pts][::-1]
        d.line(pts,fill=(40,26,30,255),width=7,joint='curve')
        ox,oy=pts[-1] if sx>0 else pts[0]
        d.line([(ox,oy),(ox+sx*9,oy+5)],fill=(40,26,30,255),width=5)
        # lower lid hint
        d.line([(cx-w*0.25,cy+h*0.56),(cx+w*0.25,cy+h*0.56)],fill=(170,110,105,180),width=3)
        # eyebrow
        bx,by=P(sx*0.058,1.488)
        d.line([(bx-sx*22,by+4),(bx,by-3),(bx+sx*20,by)],fill=(70,48,45,255),width=6,joint='curve')
    # nose: tiny shadow tick; mouth: small soft smile
    nx,ny=P(0.0,1.395); d.line([(nx-2,ny-6),(nx+3,ny+4)],fill=(220,160,145,255),width=3)
    mx,my=P(0.0,1.345); d.arc([mx-16,my-10,mx+16,my+8],20,160,fill=(160,80,80,255),width=4)
    # white swatch for vertex-coloured parts
    d.rectangle([S-64,S-64,S-1,S-1],fill=(255,255,255,255))
    img.convert('RGB').save(path)
if __name__=='__main__': paint(sys.argv[1])
