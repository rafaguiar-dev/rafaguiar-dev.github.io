"""Corta os trechos do /reel (v24): cards soltos de 4 s e tres sequencias de cortes de 2 s.

Rodar:  python mural.py   (depois: python build.py)

· CARDS: 36 trechos de 4 s, mudos, 360 px de largura, cada um na proporcao que
  melhor mostra a cena (9:16, 4:5 ou 1:1). A proporcao diferente e o que faz a
  parede do /reel parecer montada, e nao uma grade de figurinhas iguais.
· SEQS: no filtro "Todos", Personagem, Produto e B-roll viram um card so: seis
  cortes de 2 s emendados (12 s). O site poe o ASCII roxo em cima de cada troca,
  entao os cortes TEM que cair em 2, 4, 6, 8 e 10 s (24 fps, 48 quadros cada).

Trocar um card = trocar a linha aqui e a legenda no template.html.
A origem e videos-reel/ (fora do git) ou a pasta IMPETUS (caminho comecando com IMP);
a saida e media/reel/. Caminho absoluto vence o SRC (os.path.join)."""
import subprocess, json, os, glob, tempfile
from concurrent.futures import ThreadPoolExecutor
SRC = r"D:\PROJETOS\PORTIFOLIO\videos-reel"
IMP = "C:\\Users\\Rafek\\Desktop\\IMPETUS\\"
OUT = r"D:\PROJETOS\PORTIFOLIO\media\reel"
W = 360
RATIO = {"9:16": 16 / 9, "4:5": 5 / 4, "1:1": 1.0}     # altura / largura

# (id, origem, proporcao, y)  y = onde fica o recorte na vertical quando sobra altura (0 topo, .5 meio)
CARDS = [
 ("avatar-1", "1-lipsync/ls-16.mp4", "9:16", .5), ("avatar-2", "1-lipsync/ls-04.mp4", "9:16", .5),
 ("avatar-3", "1-lipsync/ls-09.mp4", "9:16", .5), ("avatar-4", "1-lipsync/ls-11.mp4", "9:16", .5),
 ("avatar-5", "1-lipsync/ls-15.mp4", "9:16", .5),
 # v24: o ls-18 saiu (o careca do escritorio lembra um ator conhecido); entrou a da cozinha
 ("avatar-6", "1-lipsync/ls-17.mp4", "4:5", .1),   # 4:5 por cima: a caixa com cara de marca fica fora
 ("ugc-1", "2-volume/vol-17.mp4", "9:16", .5), ("ugc-2", "2-volume/vol-13.mp4", "4:5", .5),
 ("ugc-3", "2-volume/vol-14.mp4", "9:16", .5), ("ugc-4", "2-volume/vol-15.mp4", "4:5", .3),
 ("ugc-5", "2-volume/vol-16.mp4", "9:16", .5), ("ugc-6", "2-volume/vol-20.mp4", "9:16", .5),
 ("insert-1", "5-insert-vfx/vfx-15.mp4", "4:5", .5),
 ("insert-2", IMP + r"14-09\BROLLS-BLOCO-6-9\11 - BLOCO 7\B7-04_neuronio-3d-BC.mp4", "1:1", .45),
 ("insert-3", IMP + r"14-09\BROLLS-BLOCO-6-9\10 - BLOCO 6\B6-05_gota-vinagre-separacao-po-dourado-IA.mp4", "4:5", .4),
 ("insert-4", "5-insert-vfx/vfx-22.mp4", "9:16", .5),
 ("insert-5", IMP + r"VSL MICROSHOT\EDICAO\BROLL_LEAD_5\L5-06B_Termografia-Pernas_IA.mp4", "9:16", .5),
 ("insert-6", IMP + r"VSL MICROSHOT\BANCO_VIDEOS\LEAD_3\Broll5_CapsulaNeon_BANCO.mp4", "4:5", .5),
 ("personagem-1", "6-consistencia/A-mulher-cozinha-03.mp4", "9:16", .5),
 ("personagem-2", "6-consistencia/A-mulher-cozinha-07.mp4", "9:16", .5),
 ("personagem-3", "6-consistencia/A-mulher-cozinha-10.mp4", "9:16", .5),
 ("personagem-4", "6-consistencia/A-mulher-cozinha-13.mp4", "9:16", .5),
 ("personagem-5", IMP + r"VSL MOUNJARO\AV-FINAL\INSERT-2.1.mp4", "9:16", .5),
 ("personagem-6", IMP + r"VSL MOUNJARO\AV-FINAL\INSERT-ALTERNATIVO-2.mp4", "9:16", .5),
 ("produto-1", "4-produto/prod-06.mp4", "9:16", .5), ("produto-2", "4-produto/prod-07.mp4", "9:16", .5),
 ("produto-3", "4-produto/prod-10.mp4", "4:5", .5), ("produto-4", "4-produto/prod-12.mp4", "4:5", .5),
 ("produto-5", "4-produto/prod-17.mp4", "9:16", .5), ("produto-6", "4-produto/prod-20.mp4", "4:5", .5),
 ("broll-1", "3-fidelidade/fid-02.mp4", "9:16", .5), ("broll-2", "3-fidelidade/fid-04.mp4", "9:16", .5),
 ("broll-3", "3-fidelidade/fid-05.mp4", "9:16", .5), ("broll-4", "3-fidelidade/fid-11.mp4", "9:16", .5),
 ("broll-5", "3-fidelidade/fid-16.mp4", "9:16", .5), ("broll-6", "3-fidelidade/fid-19.mp4", "9:16", .5),
]
# (id, proporcao, y, prefixo dos cards de onde saem os seis cortes)
SEQS = [("seq-personagem", "4:5", .35, "personagem"), ("seq-produto", "4:5", .5, "produto"),
        ("seq-broll", "9:16", .5, "broll")]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def vf(ratio, y):
    """recorte na proporcao pedida (centro na horizontal, y na vertical) e escala para 360 de largura"""
    k = RATIO[ratio]
    h = round(W * k / 2) * 2
    crop = (f"crop='trunc(min(iw,ih/{k})/2)*2':'trunc(min(ih,iw*{k})/2)*2':"
            f"'(iw-ow)/2':'(ih-oh)*{y}'")
    return crop + f",scale={W}:{h}:flags=lanczos,setsar=1,fps=24,format=yuv420p", h


def inicio(src):
    d = dur(src)
    return 0.6 if d < 6 else max(0.0, min(d - 4.3, d * 0.3))


ENC = ["-an", "-c:v", "libx264", "-profile:v", "main", "-preset", "slow", "-crf", "29", "-movflags", "+faststart"]


def card(c):
    cid, rel, ratio, y = c
    src = os.path.join(SRC, rel)
    ss = inicio(src)
    f, h = vf(ratio, y)
    mp4 = os.path.join(OUT, cid + ".mp4"); jpg = os.path.join(OUT, cid + ".jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.2f}", "-i", src, "-t", "4", "-vf", f, *ENC, mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-frames:v", "1", "-q:v", "6", jpg], check=True)
    return {"id": cid, "src": rel.replace(IMP, "IMPETUS/"), "ss": round(ss, 1), "ratio": ratio, "h": h,
            "kb": (os.path.getsize(mp4) + os.path.getsize(jpg)) // 1024}


def seq(s):
    sid, ratio, y, pref = s
    f, h = vf(ratio, y)
    fontes = [c for c in CARDS if c[0].startswith(pref + "-")]
    tmp = tempfile.mkdtemp(prefix="seq_")
    partes = []
    for i, (cid, rel, _, _) in enumerate(fontes):
        src = os.path.join(SRC, rel)
        p = os.path.join(tmp, f"{i}.mp4")
        # o meio do trecho de 4 s do card: o corte de 2 s pega a parte que mais se mexe
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{inicio(src) + 1:.2f}", "-i", src,
                        "-frames:v", "48", "-vf", f, *ENC[:-2], p], check=True)
        partes.append(p)
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w", encoding="utf-8") as fh:
        fh.writelines(f"file '{p.replace(os.sep, '/')}'\n" for p in partes)
    mp4 = os.path.join(OUT, sid + ".mp4"); jpg = os.path.join(OUT, sid + ".jpg")
    # reencoda no concat para os cortes cairem exatos em 2 s (GOP de 48 = um keyframe por corte)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista,
                    "-r", "24", "-g", "48", *ENC, mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-frames:v", "1", "-q:v", "6", jpg], check=True)
    for p in partes + [lista]:
        os.remove(p)
    os.rmdir(tmp)
    return {"id": sid, "src": pref + "-1..6", "ss": 0, "ratio": ratio, "h": h, "dur": round(dur(mp4), 2),
            "kb": (os.path.getsize(mp4) + os.path.getsize(jpg)) // 1024}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    # a pasta e so saida deste script: o que nao esta mais nas listas sai (nada de copia sobrando)
    nomes = {c[0] for c in CARDS} | {s[0] for s in SEQS}
    for p in glob.glob(os.path.join(OUT, "*.mp4")) + glob.glob(os.path.join(OUT, "*.jpg")):
        if os.path.splitext(os.path.basename(p))[0] not in nomes:
            os.remove(p)
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(card, CARDS)) + list(ex.map(seq, SEQS))
    tot = 0
    for r in rows:
        print("%-16s %-5s %4s px  %5d KB  %s" % (r["id"], r["ratio"], r["h"], r["kb"], r.get("dur", "")))
        tot += r["kb"]
    print("total", tot, "KB")
    json.dump(rows, open(os.path.join(OUT, "_origem.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
