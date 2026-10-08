import subprocess, glob, os, json
from PIL import Image, ImageDraw
OUT = "media/reel"; T = "tmp/v27"; fr = T + "/frames"; os.makedirs(fr, exist_ok=True)
ids = [f[len(OUT)+1:-4] for f in sorted(glob.glob(OUT + "/*.mp4"))]
def key(i):
    g = i.split("-")[0]; n = i.split("-")[1] if i.split("-")[1].isdigit() else 0
    return (["avatar","ugc","insert","personagem","produto","broll","seq"].index(g), int(n) if str(n).isdigit() else 0, i)
ids.sort(key=key)
def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
TH = 200
rows = []
for i in ids:
    p = f"{OUT}/{i}.mp4"; d = dur(p)
    ts = [0.1, d/2, d-0.2] if not i.startswith("seq-") else [k*3+0.1 for k in range(int(round(d/3)))] + []
    if i.startswith("seq-"):
        ts = [t for k in range(int(round(d/3))) for t in (k*3+0.15,)]
    ims = []
    for n, t in enumerate(ts):
        f = f"{fr}/{i}_{n}.jpg"
        subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t:.2f}","-i",p,"-frames:v","1","-vf",f"scale=-2:{TH}","-q:v","3",f],check=True)
        ims.append(Image.open(f))
    rows.append((i, ims))
def sheet(sel, name):
    W = 1900
    # cada linha: rótulo + frames
    ys = []; imgs = []
    for i, ims in sel:
        w = sum(im.width for im in ims) + 6*len(ims) + 120
        imgs.append((i, ims, w))
    # empacota linhas em colunas
    maxw = max(w for _,_,w in imgs)
    cols = max(1, W // maxw)
    colw = W // cols
    H = ((len(imgs) + cols - 1)//cols) * (TH + 6) + 4
    sh = Image.new("RGB", (W, H), (20,20,24)); dr = ImageDraw.Draw(sh)
    for k, (i, ims, w) in enumerate(imgs):
        cx = (k % cols) * colw; cy = (k // cols) * (TH + 6) + 2
        dr.text((cx+2, cy+4), i, fill=(255,255,255))
        x = cx + 120
        for im in ims:
            sh.paste(im, (x, cy)); x += im.width + 6
    sh.save(f"{T}/{name}.jpg", quality=88)
grupos = {"avatar":[], "ugc":[], "insert":[], "personagem":[], "produto":[], "broll":[], "seq":[]}
for r in rows: grupos[r[0].split("-")[0]].append(r)
for g, sel in grupos.items(): sheet(sel, "cortes-" + g)
sheet(rows, "cortes")
