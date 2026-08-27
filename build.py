"""Injeta as imagens (comprimidas, em base64) no template e escreve mockup.html.

Rodar:  python build.py
Editar: template.html  (nunca mockup.html — ele e' gerado)
"""
import base64, io, os, re, shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CD = r"D:\PROJETOS\canal-dark\remotion\public"
LOCAL_ASSETS = os.path.join(HERE, "assets")

# chave no template -> (caminho, largura alvo, qualidade webp)
# se voce salvar a foto oficial de fundo preto como PORTIFOLIO/hero.png,
# o build usa ela; senao usa a versao gerada por recorte (hero-preto.png).
HERO_SRC = os.path.join(HERE, "hero.png")
if not os.path.exists(HERO_SRC):
    HERO_SRC = os.path.join(HERE, "hero-preto.png")
ASCII_ROBOT_SRC = os.path.join(HERE, "hero-ascii-robot.png")

ASSETS = {
    "HERO": (HERO_SRC, 1100, 88),
    "ASCII_ROBOT": (ASCII_ROBOT_SRC, 1100, 90),
    # Cópias locais: o build não pode depender de Downloads/Desktop.
    "W1":   (os.path.join(LOCAL_ASSETS, "reel-avatar-01.png"), 560, 72),
    "W2":   (os.path.join(LOCAL_ASSETS, "reel-avatar-02.png"), 560, 72),
    "W3":   (os.path.join(LOCAL_ASSETS, "reel-avatar-03.png"), 560, 72),
    "W4":   (os.path.join(LOCAL_ASSETS, "reel-grade-01.png"),  700, 76),
    "W5":   (os.path.join(CD, "test", "scene4k.jpg"),              980, 74),
    "W6":   (os.path.join(CD, "parallax", "plano-0.webp"),         980, 74),
}


_last_mode = ""


def encode(path, width, quality):
    im = Image.open(path)
    # se a foto vier em PNG com fundo transparente, o alfa TEM que sobreviver:
    # e' ele que diz ao canvas o que e' sujeito e o que e' campo de ASCII
    im = im.convert("RGBA") if (im.mode in ("RGBA", "LA", "P") and "transparency" in im.info)          or im.mode in ("RGBA", "LA") else im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    global _last_mode
    _last_mode = im.mode
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6, exact=(im.mode == "RGBA"))
    raw = buf.getvalue()
    return "data:image/webp;base64," + base64.b64encode(raw).decode(), len(raw)


def main():
    tpl = io.open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    total = 0
    for key, (path, w, q) in ASSETS.items():
        if not os.path.exists(path):
            print(f"  !! faltando: {path}")
            continue
        uri, size = encode(path, w, q)
        total += size
        if key in ("HERO", "ASCII_ROBOT"):
            print("        (alfa preservado)" if "RGBA" in _last_mode else "        (sem alfa: fundo preto)")
        # No template de desenvolvimento, os dois retratos apontam para arquivos
        # locais. No mockup, os pares src/data-embed viram WebP autocontido.
        if key in ("HERO", "ASCII_ROBOT"):
            local_name = "hero.png" if key == "HERO" else "hero-ascii-robot.png"
            preview = f'src="{local_name}" data-embed="{{{{{key}}}}}"'
            tpl = tpl.replace(preview, f'src="{uri}"')
        else:
            tpl = tpl.replace("{{" + key + "}}", uri)
        print(f"  {key:5s} {size/1024:7.1f} KB  <- {os.path.basename(path)}")
    faltando = re.findall(r"\{\{(\w+)\}\}", tpl)
    if faltando:
        # Nunca substituir um mockup válido por uma página quebrada.
        raise RuntimeError(f"placeholders nao substituidos: {sorted(set(faltando))}")
    out = os.path.join(HERE, "mockup.html")
    tmp = out + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(tpl)
    os.replace(tmp, out)
    print(f"\n  imagens: {total/1024:.0f} KB   pagina: {len(tpl.encode('utf-8'))/1024:.0f} KB")
    print(f"  -> {out}")
    publicar(tpl)


def publicar(html):
    """Escreve a mesma pagina em docs/index.html — a pasta que o GitHub Pages serve.

    O Pages so aceita duas origens numa branch: a raiz ou /docs. A raiz aqui esta
    cheia de PNG de origem, previas e versoes/, que nao devem ir para o ar; entao
    docs/ existe para conter EXATAMENTE o que o mundo ve.

    O .nojekyll desliga o Jekyll no GitHub. Sem ele o Pages ignora qualquer
    arquivo ou pasta que comece com _ e as vezes reescreve o HTML.
    robots.txt so e escrito se ainda nao existir — regra de robo e decisao do dono.
    """
    docs = os.path.join(HERE, "docs")
    os.makedirs(docs, exist_ok=True)
    idx = os.path.join(docs, "index.html")
    tmp = idx + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(html)
    os.replace(tmp, idx)
    io.open(os.path.join(docs, ".nojekyll"), "w", encoding="utf-8").write("")
    robots = os.path.join(docs, "robots.txt")
    if not os.path.exists(robots):
        io.open(robots, "w", encoding="utf-8").write(ROBOTS)
    copiar_media(docs)
    print(f"  -> {idx}   (isto e o que o GitHub Pages publica)")


def copiar_media(docs):
    """Espelha PORTIFOLIO/media/ em docs/media/ — os videos do /reel.

    Video nao pode entrar em base64: a pagina inteira tem 900 KB e um unico
    MP4 vertical de 6 s ja passa disso. Entao ele viaja como arquivo solto, e
    o tile aponta para "media/<nome>". O caminho e relativo, entao funciona
    igual no mockup.html da raiz e no docs/index.html publicado.
    """
    src = os.path.join(HERE, "media")
    if not os.path.isdir(src):
        return
    dst = os.path.join(docs, "media")
    os.makedirs(dst, exist_ok=True)
    n = total = 0
    for nome in sorted(os.listdir(src)):
        a = os.path.join(src, nome)
        if not os.path.isfile(a):
            continue
        # o LEIA-ME e para voce, nao para o mundo: so midia atravessa
        if os.path.splitext(nome)[1].lower() not in (".mp4", ".webm", ".mov", ".gif"):
            continue
        b = os.path.join(dst, nome)
        # so copia o que mudou: video grande nao precisa ser reescrito a cada build
        if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
            shutil.copy2(a, b)
        n += 1
        total += os.path.getsize(a)
    if n:
        print(f"  media: {n} arquivo(s), {total/1024/1024:.1f} MB -> docs/media/")


ROBOTS = """# Buscadores normais: entrem.
User-agent: *
Allow: /

# Raspadores de treino de IA: nao. Isto nao tem forca de lei — e um pedido que
# as empresas serias respeitam. O LICENSE e o que tem valor juridico.
User-agent: GPTBot
Disallow: /
User-agent: CCBot
Disallow: /
User-agent: Google-Extended
Disallow: /
User-agent: anthropic-ai
Disallow: /
User-agent: ClaudeBot
Disallow: /
User-agent: PerplexityBot
Disallow: /
User-agent: Bytespider
Disallow: /
"""


if __name__ == "__main__":
    main()
