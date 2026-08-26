"""Bancada de verificação do site. Roda TUDO que precisa passar antes de entregar.

    python verificar.py            # bateria completa
    python verificar.py sintaxe    # só a sintaxe dos blocos <script>
    python verificar.py guarda     # só a proteção das áreas de texto
    python verificar.py hero       # recibos, revelação e chuva
    python verificar.py contato    # o pulso do /contact
    python verificar.py geral      # erros/fps/cliques em todos os viewports

Por que existe: o painel do navegador do app fica oculto e o `requestAnimationFrame`
não roda lá — captura sai vazia. Tem que ser Playwright headless de verdade.
"""
import io, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "file:///" + os.path.join(HERE, "mockup.html").replace("\\", "/")
VIEWPORTS = [(1920, 1080), (1440, 900), (1280, 800), (390, 844)]
falhas = []


def erro(msg):
    falhas.append(msg)
    print("   !! " + msg)


# ══════════════════════════════════════════════════════════════════════
def sintaxe():
    """Todo bloco <script> tem que passar no `node --check`."""
    print("\n== sintaxe dos blocos JavaScript ==")
    for nome in ("template.html", "mockup.html"):
        s = io.open(os.path.join(HERE, nome), encoding="utf-8").read()
        blocos = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", s, re.S)
        for i, b in enumerate(blocos):
            if not b.strip():
                continue
            fn = os.path.join(tempfile.gettempdir(), "blk%d.js" % i)
            io.open(fn, "w", encoding="utf-8").write(b)
            r = subprocess.run(["node", "--check", fn], capture_output=True, text=True)
            if r.returncode:
                erro("%s bloco %d: %s" % (nome, i, r.stderr[:300]))
            else:
                print("   %-14s bloco %d  %6d chars  OK" % (nome, i, len(b)))
        if "{{" in s and nome == "mockup.html":
            erro("mockup.html ainda tem placeholder {{...}}")


# ══════════════════════════════════════════════════════════════════════
GUARDA_JS = """() => {
  const out = [];
  const medir = (nome, host, rc) => {
    const cv = host === 'hero' ? document.getElementById('ascii')
                               : document.getElementById('ping');
    if (!cv) return;
    const base = (host === 'hero' ? document.getElementById('stage')
                                  : document.querySelector('.contact')).getBoundingClientRect();
    const d = Math.min(devicePixelRatio || 1, 2);
    const x = ((rc.left - base.left) * d) | 0, y = ((rc.top - base.top) * d) | 0;
    const w = (rc.width * d) | 0, h = (rc.height * d) | 0;
    if (w < 4 || h < 4 || x < 0 || y < 0) return;
    const im = cv.getContext('2d').getImageData(x, y, w, h).data;
    let lit = 0;
    for (let i = 0; i < im.length; i += 4)
      if (im[i] + im[i+1] + im[i+2] > 105) lit++;
    out.push([host + ':' + nome, +(100 * lit / (im.length / 4)).toFixed(3)]);
  };
  const varrer = (host, raiz) => {
    if (!raiz) return;
    const tw = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
    let i = 0;
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      if (!n.nodeValue.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const rc of rg.getClientRects()) if (rc.width > 4) medir('texto' + (i++), host, rc);
    }
    for (const q of raiz.querySelectorAll('.btn')) medir('botao', host, q.getBoundingClientRect());
  };
  varrer('hero', document.querySelector('.hero-copy'));
  varrer('contato', document.querySelector('.contact .wrap'));
  return out;
}"""


def guarda(pw):
    """Nenhum glifo do canvas pode cair em cima de linha de texto ou botão."""
    print("\n== areas protegidas (texto e botoes) ==")
    # No mobile o corpo do retrato se dissolve DE PROPOSITO na direcao do
    # texto (o `fade` do buildLuma) — isso e' design do hero, nao vazamento
    # de conduto. Referencia: o estado anterior aos condutos marcava 4,18%
    # no mobile e 1,68% em 1280; hoje esta em 1,97% e 0,55%.
    LIMITE_DESKTOP, LIMITE_MOBILE = 1.2, 2.6
    b = pw.chromium.launch()
    for W, H in VIEWPORTS:
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(URL)
        pg.wait_for_timeout(1500)
        pg.evaluate("() => document.getElementById('contact').scrollIntoView({block:'center'})")
        pg.wait_for_timeout(900)
        pior, alvo = 0.0, "-"
        for _ in range(6):
            for nome, pct in pg.evaluate(GUARDA_JS):
                if pct > pior:
                    pior, alvo = pct, nome
            pg.wait_for_timeout(420)
        limite = LIMITE_MOBILE if W < 900 else LIMITE_DESKTOP
        marca = "OK" if pior < limite else "ACIMA DO LIMITE"
        print("   %4dx%-5d pior: %.3f%%  (limite %.1f%%, %s)  %s"
              % (W, H, pior, limite, alvo, marca))
        if pior >= limite:
            erro("%dx%d: %s com %.3f%% de pixels acesos" % (W, H, alvo, pior))
        pg.close()
    b.close()


# ══════════════════════════════════════════════════════════════════════
RECIBO_JS = """() => {
  const g = document.getElementById('ascii').getContext('2d');
  const d = Math.min(devicePixelRatio || 1, 2);
  const st = document.getElementById('stage').getBoundingClientRect();
  const r = document.getElementById('photo').getBoundingClientRect();
  const im = g.getImageData(((r.left-st.left)*d)|0, ((r.top-st.top)*d)|0,
                            (r.width*d)|0, (r.height*d)|0).data;
  let roxo = 0, ciano = 0, branco = 0;
  for (let i = 0; i < im.length; i += 4) {
    const R = im[i], G = im[i+1], B = im[i+2];
    if (R + G + B < 90) continue;
    if (B > 200 && R > 150 && G < 170) roxo++;
    if (G > 190 && B > 190 && R < 150) ciano++;
    if (R > 225 && G > 225 && B > 225) branco++;
  }
  return [roxo, ciano, branco];
}"""


def hero(pw):
    """Resposta de cor no personagem, revelação de 2 s e as gotas de chuva."""
    print("\n== hero: recibos, revelacao e chuva ==")
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL)
    pg.wait_for_timeout(1500)

    serie = [pg.evaluate(RECIBO_JS) for _ in _tick(pg, 28, 250)]
    roxo = [v[0] for v in serie]
    ciano = [v[1] for v in serie]
    branco = [v[2] for v in serie]
    print("   roxo claro  %d -> %d" % (min(roxo), max(roxo)))
    print("   ciano       %d -> %d" % (min(ciano), max(ciano)))
    print("   branco puro %d -> %d  (tem que ficar perto de zero)" % (min(branco), max(branco)))
    if max(roxo) < min(roxo) * 1.4:
        erro("a resposta de cor no personagem nao esta pulsando")
    if max(branco) > 40:
        erro("branco demais no personagem: %d px" % max(branco))

    # revelacao: CORE SYNC tem que ficar em 000% ate o ASCII voltar
    pg.mouse.move(1080, 460)
    pg.mouse.down(); pg.mouse.up()
    zerado = 0
    for _ in range(14):
        pg.wait_for_timeout(300)
        if pg.inner_text("#corePct") == "000%":
            zerado += 1
    print("   CORE SYNC em 000%% por %d de 14 amostras (esperado ~12)" % zerado)
    if zerado < 9:
        erro("CORE SYNC voltou a carregar cedo demais durante a revelacao")
    if errs:
        erro("erros de pagina no hero: %s" % errs)
    b.close()


def _tick(pg, n, ms):
    for i in range(n):
        yield i
        pg.wait_for_timeout(ms)


# ══════════════════════════════════════════════════════════════════════
PING_JS = """() => {
  const cv = document.getElementById('ping');
  if (!cv) return -1;
  const im = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
  let lit = 0;
  for (let i = 0; i < im.length; i += 4) if (im[i+3] > 24) lit++;
  return +(100 * lit / (im.length / 4)).toFixed(3);
}"""


def contato(pw):
    """O pulso do /contact anima, e o hover no e-mail dispara um anel extra."""
    print("\n== /contact: o pulso ==")
    b = pw.chromium.launch()
    for W, H in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL)
        pg.wait_for_timeout(900)
        pg.evaluate("() => document.getElementById('contact').scrollIntoView({block:'center'})")
        pg.wait_for_timeout(1400)
        serie = []
        for _ in range(8):
            serie.append(pg.evaluate(PING_JS))
            pg.wait_for_timeout(420)
        pg.hover(".big-mail")
        pg.wait_for_timeout(600)
        apos = pg.evaluate(PING_JS)
        print("   %4dx%-5d densidade %.3f%%-%.3f%%   apos hover %.3f%%"
              % (W, H, min(serie), max(serie), apos))
        if max(serie) < .05:
            erro("%dx%d: o pulso do /contact nao esta desenhando" % (W, H))
        if max(serie) > 1.2:
            erro("%dx%d: o pulso do /contact esta denso demais" % (W, H))
        if errs:
            erro("erros no /contact: %s" % errs)
        pg.close()
    b.close()


# ══════════════════════════════════════════════════════════════════════
FPS_JS = """() => new Promise(r => { let n = 0; const s = performance.now();
  const t = () => { if (++n < 120) requestAnimationFrame(t);
    else r(Math.round(120000 / (performance.now() - s))); };
  requestAnimationFrame(t); })"""


def geral(pw):
    """Erros de console, fps e os links do /contact continuando clicaveis."""
    print("\n== geral: erros, fps e cliques ==")
    b = pw.chromium.launch()
    for W, H in VIEWPORTS:
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append("page: " + str(e)))
        pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type == "error" else None)
        pg.goto(URL)
        pg.wait_for_timeout(1500)
        f1 = pg.evaluate(FPS_JS)
        pg.evaluate("() => document.getElementById('contact').scrollIntoView({block:'center'})")
        pg.wait_for_timeout(1200)
        f2 = pg.evaluate(FPS_JS)
        alvo = pg.evaluate("""() => {
          const a = document.querySelector('.big-mail'), r = a.getBoundingClientRect();
          const e1 = document.elementFromPoint(r.left + 20, r.top + r.height/2);
          const btn = document.querySelector('.socials .btn'), rb = btn.getBoundingClientRect();
          const e2 = document.elementFromPoint(rb.left + rb.width/2, rb.top + rb.height/2);
          return [e1 && e1.tagName, e2 && e2.tagName];
        }""")
        print("   %4dx%-5d fps hero %2d / contato %2d   e-mail:%s botao:%s   erros:%s"
              % (W, H, f1, f2, alvo[0], alvo[1], errs if errs else "0"))
        if f1 < 40 or f2 < 40:
            erro("%dx%d: fps baixo (%d / %d)" % (W, H, f1, f2))
        if alvo != ["A", "A"]:
            erro("%dx%d: o canvas esta roubando o clique do /contact" % (W, H))
        if errs:
            erro("%dx%d: %s" % (W, H, errs))
        pg.close()

    ctx = b.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL)
    pg.wait_for_timeout(1400)
    pg.evaluate("() => document.getElementById('contact').scrollIntoView({block:'center'})")
    pg.wait_for_timeout(700)
    print("   reduced-motion: CORE SYNC = %s   erros: %s"
          % (pg.inner_text("#corePct"), errs if errs else "0"))
    if errs:
        erro("reduced-motion: %s" % errs)
    b.close()


# ══════════════════════════════════════════════════════════════════════
def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if alvo in ("tudo", "sintaxe"):
        sintaxe()
    if alvo in ("tudo", "guarda", "hero", "contato", "geral"):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            if alvo in ("tudo", "guarda"):
                guarda(pw)
            if alvo in ("tudo", "hero"):
                hero(pw)
            if alvo in ("tudo", "contato"):
                contato(pw)
            if alvo in ("tudo", "geral"):
                geral(pw)
    print("\n" + "=" * 60)
    if falhas:
        print("FALHOU — %d problema(s):" % len(falhas))
        for f in falhas:
            print("  - " + f)
        sys.exit(1)
    print("TUDO PASSOU")


if __name__ == "__main__":
    main()
