# -*- coding: utf-8 -*-
"""Bancada de navegadores: Firefox, WebKit (Safari) e Chromium.

Roda:  python navegadores.py            (testa o mockup.html local)
       python navegadores.py --no-ar    (testa o site publicado)

Motivo desta bancada: uma visitante em Firefox relatou o hero "parado",
sem progressao e com rastro de mouse que nao apagava. A causa era o loop
do hero contar QUADROS em vez de TEMPO — `t += .016` supunha 60 fps, e o
Firefox entrega bem menos com este canvas. Tudo rodava em camera lenta.

O que se mede aqui, entao, nao e fps: e se a animacao anda na MESMA
velocidade apesar do fps ser diferente.

  · esteira  px/s da faixa rolante — tem que bater entre os motores
  · rastro   pixels de rastro acima do fundo, ao longo de 3,2 s
  · erros    console e pageerror

Instalar os motores uma vez:  python -m playwright install firefox webkit
Sai com codigo 1 se algum motor falhar.
"""
import sys
from playwright.sync_api import sync_playwright

LOCAL = "file:///D:/PROJETOS/PORTIFOLIO/mockup.html"
NO_AR = "https://rafaguiar-dev.github.io/"
URL = NO_AR if "--no-ar" in sys.argv else LOCAL

FPS = """() => new Promise(r => {
  let n = 0; const t0 = performance.now();
  const passo = () => { n++; if (performance.now() - t0 < 1000) requestAnimationFrame(passo); else r(n); };
  requestAnimationFrame(passo); })"""

ESTEIRA = """() => new Promise(r => {
  const el = document.getElementById('t1');
  const ler = () => { const m = getComputedStyle(el).transform;
                      return m === 'none' ? 0 : parseFloat(m.split(',')[4]); };
  const a = ler(), t0 = performance.now();
  setTimeout(() => { const b = ler(), dt = (performance.now() - t0) / 1000;
                     let d = a - b; if (d < 0) d += el.scrollWidth / 2;
                     r(d / dt); }, 2000); })"""

RASTRO = """() => { const cv = document.getElementById('ascii');
  const d = cv.getContext('2d').getImageData(240, 330, 720, 200).data;
  let n = 0;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], g = d[i+1], b = d[i+2];
    if (b > 90 && b > g * 1.5 && r > 60) n++;
  }
  return n; }"""

LIMITE_VELOCIDADE = 1.25   # entre o motor mais rapido e o mais lento
LIMITE_RASTRO = 0.35       # tem que cair a 35% do pico em ~1,2 s


def medir(nome, motor):
    b = motor.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    erros = []
    pg.on("pageerror", lambda e: erros.append("pageerror: " + str(e)))
    pg.on("console", lambda m: erros.append("console: " + m.text) if m.type == "error" else None)
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2800)

    fps = pg.evaluate(FPS)
    vel = pg.evaluate(ESTEIRA)

    pg.evaluate("() => scrollTo(0, 0)")
    pg.wait_for_timeout(500)
    fundo = min(pg.evaluate(RASTRO) for _ in range(4))
    for x in range(300, 900, 22):
        pg.mouse.move(x, 430)
        pg.wait_for_timeout(16)
    pg.mouse.move(1350, 870)
    serie = []
    for _ in range(4):
        serie.append(max(0, pg.evaluate(RASTRO) - fundo))
        pg.wait_for_timeout(400)
    pico = max(serie[0], 1)
    queda = serie[3] / pico

    b.close()
    print("  %-9s fps %3d   esteira %5.1f px/s   rastro %s   erros %d"
          % (nome, fps, vel, serie, len(erros)))
    for e in erros[:4]:
        print("       " + e[:140])
    return {"fps": fps, "vel": vel, "queda": queda, "erros": len(erros)}


with sync_playwright() as p:
    print("\nalvo: " + URL)
    print("a animacao tem que andar na mesma velocidade apesar do fps\n")
    r = {}
    for nome, motor in (("chromium", p.chromium), ("firefox", p.firefox), ("webkit", p.webkit)):
        try:
            r[nome] = medir(nome, motor)
        except Exception as e:
            print("  %-9s NAO RODOU: %s" % (nome, str(e)[:120]))
            print("       falta instalar? python -m playwright install firefox webkit")

falhas = []
if len(r) > 1:
    vels = [v["vel"] for v in r.values()]
    raz = max(vels) / max(0.001, min(vels))
    print("\n  diferenca de velocidade entre motores: %.2fx (limite %.2f)" % (raz, LIMITE_VELOCIDADE))
    if raz > LIMITE_VELOCIDADE:
        falhas.append("a animacao ainda depende do fps (%.2fx)" % raz)

for nome, v in r.items():
    if v["queda"] > LIMITE_RASTRO:
        falhas.append("%s: o rastro nao apaga (ainda em %.0f%% do pico apos 1,2s)"
                      % (nome, v["queda"] * 100))
    if v["erros"]:
        falhas.append("%s: %d erro(s)" % (nome, v["erros"]))

print("\n" + "=" * 58)
print("TUDO PASSOU" if not falhas else "FALHOU:\n  - " + "\n  - ".join(falhas))
sys.exit(1 if falhas else 0)
