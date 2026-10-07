"""Corta os trechos do /reel (v24): cards soltos de 4 s e tres sequencias de cortes de 3 s.

Rodar:  python mural.py   (depois: python build.py)
Troca pontual: python mural.py --cards avatar-7 ugc-8 (preserva as sequências).

· CARDS: 44 trechos de 4 s, mudos, 360 px de largura, cada um na proporcao que
  melhor mostra a cena (9:16, 4:5 ou 1:1). A proporcao diferente e o que faz a
  origem do trecho continuar adequada no monitor. A folha usa fileiras uniformes.
· SEQS: no filtro "Todos", Personagem, Produto e B-roll viram um card so: seis
  cortes de 3 s emendados (18 s). O site poe o ASCII roxo em cima de cada troca,
  entao os cortes TEM que cair em 3, 6, 9, 12 e 15 s (24 fps, 72 quadros cada).

Trocar um card = trocar a linha aqui e a legenda no template.html.
A origem e videos-reel/ (fora do git) ou a pasta IMPETUS (caminho comecando com IMP);
a saida e media/reel/. Caminho absoluto vence o SRC (os.path.join)."""
import subprocess, json, os, glob, tempfile, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
SRC = r"D:\PROJETOS\PORTIFOLIO\videos-reel"
IMP = "C:\\Users\\Rafek\\Desktop\\IMPETUS\\"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "reel")
FPS = 24
QUADROS_CORTE = 72
W = 360
RATIO = {"9:16": 16 / 9, "4:5": 5 / 4, "1:1": 1.0}     # altura / largura

# (id, origem, proporção, y, x opcional): posição do recorte (0 início, .5 centro, 1 fim).
CARDS = [
 ("avatar-1", "1-lipsync/ls-16.mp4", "9:16", .5), ("avatar-2", "1-lipsync/ls-04.mp4", "9:16", .5),
 ("avatar-3", "1-lipsync/ls-09.mp4", "9:16", .5), ("avatar-4", "1-lipsync/ls-11.mp4", "9:16", .5),
 ("avatar-5", "1-lipsync/ls-15.mp4", "9:16", .5),
 # v24: o ls-18 saiu (o careca do escritorio lembra um ator conhecido); entrou a da cozinha
 ("avatar-6", "1-lipsync/ls-17.mp4", "4:5", .1),   # 4:5 por cima: a caixa com cara de marca fica fora
 ("avatar-7", "1-lipsync/ls-08.mp4", "4:5", .5),
 ("avatar-8", "1-lipsync/ls-02.mp4", "4:5", .5),
 ("ugc-1", "2-volume/vol-17.mp4", "9:16", .5), ("ugc-2", "2-volume/vol-13.mp4", "4:5", .5),
 ("ugc-3", "2-volume/vol-14.mp4", "9:16", .5), ("ugc-4", "2-volume/vol-15.mp4", "4:5", .3),
 ("ugc-5", "2-volume/vol-16.mp4", "9:16", .5), ("ugc-6", "2-volume/vol-20.mp4", "9:16", .5),
 ("ugc-7", "2-volume/vol-12.mp4", "4:5", .5, .22),
 ("ugc-8", "1-lipsync/ls-06.mp4", "4:5", .5),
 ("insert-1", "5-insert-vfx/vfx-15.mp4", "4:5", .5),
 ("insert-2", IMP + r"14-09\BROLLS-BLOCO-6-9\11 - BLOCO 7\B7-04_neuronio-3d-BC.mp4", "1:1", .45),
 ("insert-3", IMP + r"14-09\BROLLS-BLOCO-6-9\10 - BLOCO 6\B6-05_gota-vinagre-separacao-po-dourado-IA.mp4", "4:5", .4),
 ("insert-4", "5-insert-vfx/vfx-22.mp4", "9:16", .5),
 ("insert-5", IMP + r"VSL MICROSHOT\EDICAO\BROLL_LEAD_5\L5-06B_Termografia-Pernas_IA.mp4", "9:16", .5),
 ("insert-6", IMP + r"VSL MICROSHOT\BANCO_VIDEOS\LEAD_3\Broll5_CapsulaNeon_BANCO.mp4", "4:5", .5),
 ("insert-7", "5-insert-vfx/vfx-04.mp4", "1:1", .5),
 ("insert-8", "5-insert-vfx/vfx-10.mp4", "1:1", .5),
 ("personagem-1", "6-consistencia/A-mulher-cozinha-03.mp4", "9:16", .5),
 ("personagem-2", "6-consistencia/A-mulher-cozinha-07.mp4", "9:16", .5),
 ("personagem-3", "6-consistencia/A-mulher-cozinha-10.mp4", "9:16", .5),
 ("personagem-4", "6-consistencia/A-mulher-cozinha-13.mp4", "9:16", .5),
 ("personagem-5", IMP + r"VSL MOUNJARO\AV-FINAL\INSERT-2.1.mp4", "9:16", .5),
 ("personagem-6", IMP + r"VSL MOUNJARO\AV-FINAL\INSERT-ALTERNATIVO-2.mp4", "9:16", .5),
 ("produto-1", "4-produto/prod-06.mp4", "9:16", .5), ("produto-2", "4-produto/prod-07.mp4", "9:16", .5),
 ("produto-3", "4-produto/prod-10.mp4", "4:5", .5), ("produto-4", "4-produto/prod-12.mp4", "4:5", .5),
 ("produto-5", "4-produto/prod-17.mp4", "9:16", .5), ("produto-6", "4-produto/prod-20.mp4", "4:5", .5),
 ("produto-7", "4-produto/prod-04.mp4", "1:1", .5),
 ("produto-8", "4-produto/prod-02.mp4", "1:1", .5),
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


def vf(ratio, y, x=.5):
    """Recorta na proporção e posição pedidas e escala para 360 de largura."""
    k = RATIO[ratio]
    h = round(W * k / 2) * 2
    crop = (f"crop='trunc(min(iw,ih/{k})/2)*2':'trunc(min(ih,iw*{k})/2)*2':"
            f"'(iw-ow)*{x}':'(ih-oh)*{y}'")
    return crop + f",scale={W}:{h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p", h


def inicio(src):
    d = dur(src)
    return 0.6 if d < 6 else max(0.0, min(d - 4.3, d * 0.3))


ENC = ["-an", "-c:v", "libx264", "-profile:v", "main", "-preset", "slow", "-crf", "29", "-movflags", "+faststart"]


def card(c):
    cid, rel, ratio, y = c[:4]
    x = c[4] if len(c) > 4 else .5
    src = os.path.join(SRC, rel)
    ss = inicio(src)
    # Fontes curtas repetem o movimento para entregar os quatro segundos do card.
    repetir = ["-stream_loop", "-1"] if dur(src) - ss < 4 else []
    f, h = vf(ratio, y, x)
    mp4 = os.path.join(OUT, cid + ".mp4"); jpg = os.path.join(OUT, cid + ".jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *repetir, "-ss", f"{ss:.2f}", "-i", src,
                    "-frames:v", str(FPS * 4), "-vf", f, *ENC, mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-frames:v", "1", "-q:v", "6", jpg], check=True)
    return {"id": cid, "src": rel.replace(IMP, "IMPETUS/"), "ss": round(ss, 1), "ratio": ratio, "x": x, "y": y, "h": h,
            "kb": (os.path.getsize(mp4) + os.path.getsize(jpg)) // 1024}


def seq(s):
    sid, ratio, y, pref = s
    f, h = vf(ratio, y)
    fontes = [c for c in CARDS if c[0].startswith(pref + "-")][:6]  # sequências mantêm os seis cortes originais
    tmp = tempfile.mkdtemp(prefix="seq_")
    partes = []
    for i, fonte in enumerate(fontes):
        cid, rel, _, _ = fonte[:4]
        src = os.path.join(SRC, rel)
        p = os.path.join(tmp, f"{i}.mp4")
        # três segundos centrados no trecho de quatro segundos do card
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{inicio(src) + .5:.2f}", "-i", src,
                        "-frames:v", str(QUADROS_CORTE), "-vf", f, *ENC[:-2], p], check=True)
        partes.append(p)
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w", encoding="utf-8") as fh:
        fh.writelines(f"file '{p.replace(os.sep, '/')}'\n" for p in partes)
    mp4 = os.path.join(OUT, sid + ".mp4"); jpg = os.path.join(OUT, sid + ".jpg")
    # GOP fixo: um keyframe em cada corte de três segundos
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista,
                    "-r", str(FPS), "-g", str(QUADROS_CORTE), "-keyint_min", str(QUADROS_CORTE), "-sc_threshold", "0", *ENC, mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-frames:v", "1", "-q:v", "6", jpg], check=True)
    for p in partes + [lista]:
        os.remove(p)
    os.rmdir(tmp)
    return {"id": sid, "src": pref + "-1..6", "ss": 0, "ratio": ratio, "h": h, "dur": round(dur(mp4), 2),
            "kb": (os.path.getsize(mp4) + os.path.getsize(jpg)) // 1024}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera os cards e as sequências do /reel.")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--so-seq", action="store_true", help="Refaz somente as três sequências.")
    modo.add_argument("--cards", nargs="+", metavar="ID", help="Refaz somente os cards indicados, sem alterar sequências.")
    args = parser.parse_args()
    if args.cards and set(args.cards) - {c[0] for c in CARDS}:
        parser.error("Card desconhecido: " + ", ".join(sorted(set(args.cards) - {c[0] for c in CARDS})))
    os.makedirs(OUT, exist_ok=True)
    # a pasta e so saida deste script: o que nao esta mais nas listas sai (nada de copia sobrando)
    nomes = {c[0] for c in CARDS} | {s[0] for s in SEQS}
    for p in glob.glob(os.path.join(OUT, "*.mp4")) + glob.glob(os.path.join(OUT, "*.jpg")):
        if not args.so_seq and not args.cards and os.path.splitext(os.path.basename(p))[0] not in nomes:
            os.remove(p)
    with ThreadPoolExecutor(6) as ex:
        escolhidos = [c for c in CARDS if not args.cards or c[0] in args.cards]
        rows = ([] if args.so_seq else list(ex.map(card, escolhidos))) + ([] if args.cards else list(ex.map(seq, SEQS)))
    tot = 0
    for r in rows:
        print("%-16s %-5s %4s px  %5d KB  %s" % (r["id"], r["ratio"], r["h"], r["kb"], r.get("dur", "")))
        tot += r["kb"]
    print("total", tot, "KB")
    if args.so_seq or args.cards:
        origem = os.path.join(OUT, "_origem.json")
        if os.path.exists(origem):
            anteriores = json.loads(Path(origem).read_text(encoding="utf-8"))
            atualizados = {r["id"] for r in rows}
            rows = [r for r in anteriores if r["id"] not in atualizados] + rows
    json.dump(rows, open(os.path.join(OUT, "_origem.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
