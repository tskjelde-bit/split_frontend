import sys
from PIL import Image
from rembg import remove, new_session

name = sys.argv[1]; model = sys.argv[2]
fx0,fy0,fx1,fy1 = map(float, sys.argv[3:7])
master = Image.open("00-master.png").convert("RGBA")
W,H = master.size
sess = new_session(model, providers=["CPUExecutionProvider"])
x0,y0,x1,y1 = int(fx0*W),int(fy0*H),int(fx1*W),int(fy1*H)
crop = master.crop((x0,y0,x1,y1))
cw,ch = crop.size
scale = min(1.0, 1024/max(cw,ch))
small = crop.resize((int(cw*scale),int(ch*scale)), Image.LANCZOS)
alpha = remove(small, session=sess, only_mask=True).resize((cw,ch), Image.LANCZOS)
cut = crop.copy(); cut.putalpha(alpha)
canvas = Image.new("RGBA",(W,H),(0,0,0,0))
canvas.paste(cut,(x0,y0),cut)
canvas.resize((1920,int(1920*H/W)),Image.LANCZOS).save(f"{name}.png")
print("OK", name)
