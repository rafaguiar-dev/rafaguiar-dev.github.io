# -*- coding: utf-8 -*-
"""Bateria de aceite do briefing de conteudo (v21).

Roda:  python aceite.py
Complementa o verificar.py — aquele cuida do hero, fps e areas protegidas;
este cuida do CONTEUDO: idioma padrao, ordem das secoes, indicadores,
estrutura dos cases, decisoes, links e responsividade em 4 larguras.

Sai com codigo 1 se alguma checagem falhar.
"""
import sys
from playwright.sync_api import sync_playwright
F = "file:///D:/PROJETOS/PORTIFOLIO/mockup.html"
falhas = []


def ok(cond, msg, extra=""):
    print(("  OK  " if cond else "  XX  ") + msg + ("   " + str(extra) if extra != "" else ""))
    if not cond:
        falhas.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(F)
    pg.wait_for_timeout(2600)
    pg.mouse.move(700, 300)

    print("\n-- idioma --")
    ok(pg.evaluate("document.documentElement.lang") == "pt-BR", "portugues e o padrao")
    ok(pg.evaluate("document.getElementById('lang').textContent.trim()") == "EN", "botao oferece EN")
    ok("Transformo copy" in pg.evaluate("document.querySelector('.one-line').textContent"), "hero em PT")
    ok(pg.evaluate("document.querySelector('.wall img').alt").startswith("Apresentador"), "alt traduzido")
    vazio = pg.evaluate("[...document.querySelectorAll('[data-pt]')].filter(n=>!n.dataset.pt.trim()).length")
    ok(vazio == 0, "nenhum data-pt vazio", vazio)
    pg.click("#lang")
    pg.wait_for_timeout(500)
    ok(pg.evaluate("document.documentElement.lang") == "en", "botao troca para EN")
    ok("I turn copy" in pg.evaluate("document.querySelector('.one-line').textContent"), "hero volta ao EN")
    ok(pg.evaluate("document.querySelector('.wall img').alt").startswith("AI-generated"), "alt volta ao EN")
    pg.click("#lang")
    pg.wait_for_timeout(500)

    print("\n-- ordem e navegacao --")
    ordem = pg.evaluate("[...document.querySelectorAll('section.sec')].map(s=>s.id||'track').join(',')")
    ok(ordem == "reel,work,do,decisions,track,contact", "ordem das secoes", ordem)
    nav = pg.evaluate("[...document.querySelectorAll('.nav-links a')].map(a=>a.getAttribute('href')).join(',')")
    ok(nav == "#reel,#work,#do,#decisions,#contact", "ordem da nav", nav)

    print("\n-- indicadores --")
    ok(pg.evaluate("!!document.querySelector('#reel .stats')"), "indicadores dentro do /reel")
    ok(pg.evaluate("document.querySelectorAll('.stats').length") == 1, "nao duplicados em outra secao")
    pg.evaluate("document.querySelector('#reel .stats').scrollIntoView({block:'center'})")
    pg.wait_for_timeout(1900)
    fim = pg.evaluate("[...document.querySelectorAll('[data-count]')].map(e=>e.textContent)")
    ok(fim == ["1500+", "12", "9", "3+"], "terminam nos valores certos", fim)
    ok(pg.evaluate("[...document.querySelectorAll('[data-count]')].every(e=>e.getAttribute('aria-hidden')==='true')"),
       "contagem escondida do leitor de tela")
    sr = pg.evaluate("[...document.querySelectorAll('.stat .sr')].map(e=>e.textContent).join(',')")
    ok(sr == "1500+,12,9,3+", "leitor de tela recebe o valor final", sr)

    print("\n-- /reel --")
    ok(pg.evaluate("document.querySelectorAll('.wall figure.tile').length") == 6, "6 itens")
    ok(pg.evaluate("document.querySelectorAll('.wall a').length") == 0, "card sem destino nao finge ser link")
    ok(pg.evaluate("document.querySelectorAll('.wall video').length") == 0, "sem video: nenhum player criado")
    ok(pg.evaluate("[...document.querySelectorAll('.wall img')].every(i=>i.alt.trim().length>12)"), "todo poster tem alt")
    ok(pg.evaluate("typeof REEL==='object' && Object.keys(REEL).length===6"), "dados centralizados em REEL")

    print("\n-- /work --")
    ordem_case = pg.evaluate("[...document.querySelectorAll('.w-body.on > *')].map(e=>e.tagName+'.'+e.className).join(' ')")
    ok(ordem_case.startswith("H3. P.lead DIV.case"), "nome -> resultado -> problema", ordem_case[:44])
    rot = pg.evaluate("[...document.querySelectorAll('.w-body.on .ci b')].map(e=>e.textContent).join('/')")
    ok(rot == "problema/construído", "rotulos em PT", rot)
    ok(pg.evaluate("document.querySelectorAll('.w-media .prev').length") == 5, "todo demo marcado como previa")
    ok(pg.evaluate("document.querySelectorAll('.w-item').length") == 5, "5 cases no painel")
    ok(pg.evaluate("document.querySelectorAll('.w-item.minor').length") == 2, "2 secundarios")

    print("\n-- /decisions --")
    viz = pg.evaluate("[...document.querySelectorAll('.trade')].filter(t=>!t.classList.contains('hid')).map(t=>t.querySelector('.pick').textContent)")
    ok(len(viz) == 3, "3 visiveis", len(viz))
    ok(len(viz) == 3 and "n8n" in viz[0] and "Playwright" in viz[1] and "aprova" in viz[2],
       "as tres que voce priorizou", viz)
    ok(pg.evaluate("document.getElementById('moreBtn').tagName") == "BUTTON", "expandir e um button")
    pg.evaluate("document.getElementById('moreBtn').click()")
    pg.wait_for_timeout(400)
    ok(pg.evaluate("document.querySelectorAll('.trade:not(.hid)').length") == 6, "expande para 6")

    print("\n-- links --")
    ok(pg.evaluate("document.querySelectorAll('a[href=\"#\"]').length") == 0, "nenhum href vazio")
    ok(pg.evaluate("document.querySelectorAll('a[href^=\"mailto\"]').length") == 1, "mailto preservado")
    ext = pg.evaluate("[...document.querySelectorAll('a[target=_blank]')].map(a=>a.rel).join('|')")
    ok(ext == "noopener noreferrer", "rel completo nos externos", ext)
    ok(pg.evaluate("document.querySelectorAll('.socials a').length") == 1, "so o CTA com URL real aparece")

    print("\n-- console --")
    ok(len(errs) == 0, "zero erro de console", errs[:3])
    pg.close()

    for W, H in [(360, 780), (768, 1024), (1280, 800), (1440, 700)]:
        pg = b.new_page(viewport={"width": W, "height": H})
        e2 = []
        pg.on("pageerror", lambda e: e2.append(str(e)))
        pg.goto(F)
        pg.wait_for_timeout(2200)
        over = pg.evaluate("document.documentElement.scrollWidth-innerWidth")
        cols = pg.evaluate("getComputedStyle(document.querySelector('.stats')).gridTemplateColumns.split(' ').length")
        print("\n-- %dx%d --" % (W, H))
        ok(over <= 0, "sem rolagem horizontal", over)
        ok(cols == (2 if W < 760 else 4), "indicadores 2x2 no mobile / 4 no desktop", cols)
        ok(len(e2) == 0, "sem erro de pagina", e2[:2])
        pg.close()

    pg = b.new_page(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    e3 = []
    pg.on("pageerror", lambda e: e3.append(str(e)))
    pg.goto(F)
    pg.wait_for_timeout(1800)
    pg.evaluate("document.querySelector('#reel .stats').scrollIntoView({block:'center'})")
    pg.wait_for_timeout(400)
    print("\n-- reduced motion --")
    vals = pg.evaluate("[...document.querySelectorAll('[data-count]')].map(e=>e.textContent)")
    ok(vals == ["1500+", "12", "9", "3+"], "valor final imediato", vals)
    ok(pg.evaluate("document.querySelectorAll('.wall video').length") == 0, "nenhum video criado sozinho")
    ok(len(e3) == 0, "sem erro de pagina", e3[:2])
    b.close()

print("\n" + "=" * 54)
print("TUDO PASSOU" if not falhas else "FALHOU:\n  - " + "\n  - ".join(falhas))

sys.exit(1 if falhas else 0)
