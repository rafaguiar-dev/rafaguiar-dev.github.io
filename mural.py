"""Corta os trechos do /reel (v27): cards soltos de 4 s e tres sequencias de cortes de 3 s.

Rodar:  python mural.py   (depois: python build.py)
Troca pontual: python mural.py --cards avatar-7 ugc-8 (preserva as sequências).

· CARDS: 58 trechos de 4 s, mudos, 360 px de largura, cada um na proporcao que
  melhor mostra a cena (9:16, 4:5 ou 1:1). A proporcao diferente e o que faz a
  origem do trecho continuar adequada no monitor. A folha usa fileiras uniformes.
  Formato: (id, origem, proporcao, y[, x[, inicio em segundos]]).
· SEQS: no filtro "Todos", Personagem, Produto e B-roll viram um card so: cortes
  de 3 s emendados (6 de personagem = 18 s, 9 de produto e 9 de B-roll = 27 s). O site
  poe o ASCII roxo em cima de cada troca, entao os cortes TEM que cair de 3 em 3 s
  (24 fps, 72 quadros cada). Cada SEQS diz quantos cortes usa: (id, prop, y, prefixo, cortes).

Trocar um card = trocar a linha aqui e a legenda no template.html.
A origem e videos-reel/ (fora do git), a pasta IMPETUS (caminho comecando com IMP) ou
E:\IA CREATOR (caminho absoluto); a saida e media/reel/. Caminho absoluto vence o SRC (os.path.join)."""
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

# (id, origem, proporção, y, x opcional, início opcional em segundos): posição do recorte (0 início, .5 centro, 1 fim).
E = "E:\\IA CREATOR\\"
EP = E + "2-INSERT\\alimento-preparo\\"
CARDS = [
 # Avatares: escolhidos pessoalmente pelo Rafael
 ("avatar-1", "1-lipsync/ls-16.mp4", "9:16", .5),
 ("avatar-2", IMP + r"11-09\31.mp4", "4:5", .30),
 ("avatar-3", E + r"1-LIPSYNC\exterior\lipsync-180-depo-9-1080p-22s.mp4", "9:16", .5),
 ("avatar-4", "1-lipsync/ls-09.mp4", "9:16", .5),
 ("avatar-5", IMP + r"23-09\UP\TESTE.mp4", "4:5", .5),
 ("avatar-6", IMP + r"23-09\ML1\ML 01\ML01-5-MBB.mp3.mp4", "4:5", .25),
 ("avatar-7", "1-lipsync/ls-17.mp4", "4:5", .1),   # v27b: volta a apresentadora; o homem das oliveiras ficou estranho
 ("avatar-8", IMP + r"22-09\mls\ML 1\ML01-2-MICHELLY.mp3.mp4", "9:16", .5),
 ("avatar-9", E + r"1-LIPSYNC\exterior\lipsync-168-depo-32-1080p-35s.mp4", "4:5", .25),
 ("avatar-10", "1-lipsync/ls-11.mp4", "9:16", .5),
 # UGC
 ("ugc-1", "2-volume/vol-17.mp4", "9:16", .5), ("ugc-2", "2-volume/vol-13.mp4", "4:5", .5),
 ("ugc-3", "2-volume/vol-14.mp4", "9:16", .5), ("ugc-4", "2-volume/vol-15.mp4", "4:5", .3),
 ("ugc-5", "2-volume/vol-16.mp4", "9:16", .5), ("ugc-6", "2-volume/vol-20.mp4", "9:16", .5),
 ("ugc-7", "2-volume/vol-12.mp4", "4:5", .5, .22),
 ("ugc-8", r"E:\IA CREATOR\1-LIPSYNC\exterior\lipsync-083-avatar-ad-4-60s.mp4", "9:16", .3),   # v27b: selfie no parque
 # Inserts 3D
 ("insert-1", E + r"2-INSERT\corpo-anatomia\insert-154-corpo-anatomia-5s.mp4", "4:5", .5),
 ("insert-2", IMP + r"14-09\BROLLS-BLOCO-6-9\11 - BLOCO 7\B7-04_neuronio-3d-BC.mp4", "1:1", .45),
 ("insert-3", "5-insert-vfx/vfx-22.mp4", "9:16", .5),   # v27b: volta o pâncreas
 ("insert-4", IMP + r"VSL MICROSHOT\EDICAO\BROLL_LEAD_5\L5-06B_Termografia-Pernas_IA.mp4", "9:16", .5),   # v27b: volta a termografia
 ("insert-5", E + r"2-INSERT\corpo-anatomia\insert-156-corpo-anatomia-5s.mp4", "1:1", .5),
 ("insert-6", "5-insert-vfx/vfx-10.mp4", "1:1", .5),
 ("insert-7", E + r"2-INSERT\industria-laboratorio\insert-266-industria-5s.mp4", "4:5", .5),
 ("insert-8", IMP + r"VSL MICROSHOT\BANCO_VIDEOS\LEAD_3\Broll6_PlanoA_CapsulaLiberaIntestino_BANCO.mp4", "1:1", .5),
 # Personagem: a mesma apresentadora de suéter amarelo
 ("personagem-1", IMP + r"VSL MOUNJARO\AV-FINAL\11.mp4", "1:1", .5),
 ("personagem-2", IMP + r"VSL MOUNJARO\AV-FINAL\41.mp4", "1:1", .5),
 ("personagem-3", IMP + r"VSL MICROSHOT\APONTANDO\APONTANDODIREITA1.mp4", "1:1", .5),
 ("personagem-4", IMP + r"VSL MOUNJARO\AV-FINAL\31.mp4", "1:1", .5),
 ("personagem-5", IMP + r"VSL MOUNJARO\AV-FINAL\INSERT-2.2.mp4", "1:1", .5),
 ("personagem-6", IMP + r"VSL MOUNJARO\AV-FINAL\71.mp4", "1:1", .5),
 # Produto: os nove primeiros formam a sequência
 ("produto-1", IMP + r"03-09\INSERTS\INSERTS\VIDEO_19_mockup-water-splash.mp4", "4:5", .5),
 ("produto-2", IMP + r"VSLCAIO03\INSERTS-BODY-VSL\INSERTS-PRODUTO\VIDEOS\47_MOCKUP_explosao_ingredientes.mp4", "9:16", .5),
 ("produto-3", IMP + r"loop-video\lab\mockup-videos\testes-28-09\4-camera-parada.mp4", "9:16", .5),
 ("produto-4", E + r"2-INSERT\produto-sozinho\insert-416-mockup-5s.mp4", "9:16", .5),
 ("produto-5", E + r"2-INSERT\produto-sozinho\insert-239-generico-5s.mp4", "4:5", .5),
 ("produto-6", IMP + r"03-09\INSERTS\INSERTS\VIDEO_23_mockup-natural-spring.mp4", "9:16", .5),
 ("produto-7", E + r"2-INSERT\produto-sozinho\insert-329-produto-sozinho-5s.mp4", "9:16", .5),
 ("produto-8", IMP + r"VSLCAIO03\INSERTS-BODY-VSL\INSERTS-PRODUTO\VIDEOS\18_OFFER_C21_hero_produto.mp4", "9:16", .5),
 ("produto-9", E + r"2-INSERT\produto-sozinho\insert-497-sleep-5s.mp4", "4:5", .5),
 ("produto-10", E + r"2-INSERT\produto-sozinho\insert-130-produto-sozinho-5s.mp4", "1:1", .5),
 ("produto-11", E + r"2-INSERT\produto-sozinho\insert-519-sleep-lipo-5s.mp4", "4:5", .5),
 ("produto-12", IMP + r"03-09\INSERTS\INSERTS\VIDEO_15_mockup-bar-marble.mp4", "4:5", .5),   # v27: insert-168 girava e mostrava texto falso no verso
 # B-roll: uma receita de gelatina rosa, na ordem da receita
 ("broll-1", EP + "insert-199-alimento-preparo-5s.mp4", "9:16", .5),
 ("broll-2", EP + "insert-005-alimento-preparo-5s.mp4", "9:16", .5),
 ("broll-3", EP + "insert-290-alimento-preparo-10s.mp4", "9:16", .5),
 ("broll-4", EP + "insert-202-alimento-preparo-5s.mp4", "9:16", .5),
 ("broll-5", EP + "insert-287-alimento-preparo-10s.mp4", "9:16", .5),
 ("broll-6", EP + "insert-292-alimento-preparo-10s.mp4", "9:16", .5),
 ("broll-7", EP + "insert-294-alimento-preparo-10s.mp4", "9:16", .5),
 ("broll-8", EP + "insert-296-alimento-preparo-10s.mp4", "9:16", .5),
 ("broll-9", EP + "insert-298-alimento-preparo-10s.mp4", "9:16", .5),
]
# (id, proporcao, y, prefixo dos cards de onde saem os cortes, quantos cortes)
SEQS = [("seq-personagem", "1:1", .5, "personagem", 6),
        ("seq-produto", "9:16", .5, "produto", 9),
        ("seq-broll", "9:16", .5, "broll", 9)]


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


def ini(c, src):
    """Início do trecho: o sexto item do CARDS, se houver; senão o padrão global."""
    return c[5] if len(c) > 5 else inicio(src)


def card(c):
    cid, rel, ratio, y = c[:4]
    x = c[4] if len(c) > 4 and c[4] is not None else .5
    src = os.path.join(SRC, rel)
    ss = ini(c, src)
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
    sid, ratio, y, pref, cortes = s
    f, h = vf(ratio, y)
    fontes = [c for c in CARDS if c[0].startswith(pref + "-")][:cortes]
    tmp = tempfile.mkdtemp(prefix="seq_")
    partes = []
    for i, fonte in enumerate(fontes):
        cid, rel, _, _ = fonte[:4]
        src = os.path.join(SRC, rel)
        p = os.path.join(tmp, f"{i}.mp4")
        # três segundos centrados no trecho de quatro segundos do card
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini(fonte, src) + .5:.2f}", "-i", src,
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
    return {"id": sid, "src": pref + "-1.." + str(cortes), "ss": 0, "ratio": ratio, "h": h, "dur": round(dur(mp4), 2),
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
