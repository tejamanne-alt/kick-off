# Paints the faces of the two playable teens (Ghibli-style: simple shapes, dark round irises
# with one big highlight, a firm upper lid line, light brows, a small nose with a shadow tick
# and a small mouth). Same atlas layout as face.py: the face is a front projection in the
# upper-left quadrant (u = x/0.34 + 0.5, v = (z - 1.27)/0.34 in head space), the bottom-right
# corner is plain white for vertex-coloured parts.
import math, sys
from PIL import Image, ImageDraw, ImageFilter
S=1024; H=512
def paint(path, girl):
    skin=(250,224,200) if girl else (244,210,180)
    img=Image.new('RGBA',(S,S),skin+(255,))
    def P(x,z):
        u=x/0.34+0.5; v=(z-1.27)/0.34
        return (u*H,(1-v)*H)
    # soft cheek colour
    glow=Image.new('RGBA',(S,S),(0,0,0,0)); g=ImageDraw.Draw(glow)
    for sx in(-1,1):
        cx,cy=P(sx*0.066,1.392)
        g.ellipse([cx-24,cy-10,cx+24,cy+10],fill=(255,150,140,70 if girl else 35))
    img=Image.alpha_composite(img,glow.filter(ImageFilter.GaussianBlur(8)))
    d=ImageDraw.Draw(img,'RGBA')
    ink=(52,34,34,255)
    for sx in(-1,1):
        cx,cy=P(sx*(0.054 if girl else 0.056),1.43)
        w,h=(40,50) if girl else (38,46)
        # white of the eye: a rounded almond
        d.ellipse([cx-w*0.62,cy-h*0.48,cx+w*0.62,cy+h*0.5],fill=(255,255,255,255))
        # iris: near-black brown, round, touching the upper lid
        r=w*0.42
        d.ellipse([cx-r,cy-h*0.42,cx+r,cy-h*0.42+2*r],fill=(38,26,26,255))
        d.ellipse([cx-r*0.55,cy-h*0.42+r*0.45,cx+r*0.55,cy-h*0.42+r*1.55],fill=(18,12,14,255))
        # one big highlight
        hx=cx+sx*r*0.3; hy=cy-h*0.42+r*0.55
        d.ellipse([hx-r*0.32,hy-r*0.32,hx+r*0.32,hy+r*0.32],fill=(255,255,255,255))
        # upper lid: a firm curved line, heavier at the outer corner
        pts=[(cx-sx*w*0.7,cy-h*0.12),(cx-sx*w*0.35,cy-h*0.48),(cx+sx*w*0.25,cy-h*0.56),(cx+sx*w*0.72,cy-h*0.28)]
        d.line(pts,fill=ink,width=6,joint='curve')
        d.line(pts[2:],fill=ink,width=8,joint='curve')
        if girl:   # a couple of short lashes at the outer corner
            ox,oy=pts[-1]
            d.line([(ox,oy),(ox+sx*8,oy-5)],fill=ink,width=4)
        # a faint lower line
        d.line([(cx-w*0.3,cy+h*0.52),(cx+w*0.3,cy+h*0.52)],fill=(150,100,90,170),width=3)
        # brows: thin and arched for her; straighter and bolder for him
        bx,by=P(sx*0.058,1.49 if girl else 1.478)
        if girl:
            d.line([(bx-sx*20,by+5),(bx,by-3),(bx+sx*22,by+2)],fill=(110,52,34,255),width=5,joint='curve')
        else:
            d.line([(bx-sx*24,by+2),(bx-sx*4,by-3),(bx+sx*22,by-1)],fill=(45,30,28,255),width=7,joint='curve')
    # nose: a small line with a shadow tick on one side
    nx,ny=P(0.006,1.392)
    d.line([(nx-2,ny-14),(nx+4,ny+2),(nx-3,ny+5)],fill=(200,140,120,255),width=3,joint='curve')
    # mouth: a small, gentle smile
    mx,my=P(0.004,1.345)
    d.arc([mx-15,my-8,mx+15,my+6],25,155,fill=(150,85,80,255),width=3)
    if not girl:
        d.line([(mx-6,my+14),(mx+6,my+14)],fill=(215,165,145,200),width=2)   # chin shadow hint
    d.rectangle([S-64,S-64,S-1,S-1],fill=(255,255,255,255))
    img.convert('RGB').save(path)
if __name__=='__main__': paint(sys.argv[1], '--girl' in sys.argv)
