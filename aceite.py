# -*- coding: utf-8 -*-
"""Bateria de aceite do briefing de conteudo (v21; parede de trabalhos, telas do /stack na v24).

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
    ok(pg.evaluate("document.querySelector('.wall img').alt").startswith("Vídeo gerado por IA"), "alt traduzido")
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
    ok(ordem == "reel,work,do,career,contact", "ordem das secoes", ordem)
    nav = pg.evaluate("[...document.querySelectorAll('.nav-links a')].map(a=>a.getAttribute('href')).join(',')")
    ok(nav == "#reel,#work,#do,#career,#contact", "ordem da nav", nav)

    print("\n-- indicadores --")
    ok(pg.evaluate("!!document.querySelector('#reel .stats')"), "indicadores dentro do /reel")
    ok(pg.evaluate("document.querySelectorAll('.stats').length") == 1, "nao duplicados em outra secao")
    pg.evaluate("document.querySelector('#reel .stats').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(1900)
    fim = pg.evaluate("[...document.querySelectorAll('[data-count]')].map(e=>e.textContent)")
    ok(fim == ["1500+", "12", "9", "3+"], "terminam nos valores certos", fim)
    ok(pg.evaluate("[...document.querySelectorAll('[data-count]')].every(e=>e.getAttribute('aria-hidden')==='true')"),
       "contagem escondida do leitor de tela")
    sr = pg.evaluate("[...document.querySelectorAll('.stat .sr')].map(e=>e.textContent).join(',')")
    ok(sr == "1500+,12,9,3+", "leitor de tela recebe o valor final", sr)

    print("\n-- /reel: a parede --")
    ok(pg.evaluate("document.querySelector('#reel h2').textContent") == "Trabalhos.", "titulo Trabalhos.")
    ok(pg.evaluate("document.querySelectorAll('.wall figure.clip').length") == 39, "39 cards (36 trechos + 3 sequencias)")
    todos = pg.evaluate("[...document.querySelectorAll('.wall .clip')].filter(c=>!c.hidden).length")
    ok(todos == 21, "Todos: 21 cards, sem repetir personagem/produto/B-roll", todos)
    ok(pg.evaluate("[...document.querySelectorAll('.wall .clip.seq')].filter(c=>!c.hidden).length") == 3, "3 cards de cortes em Todos")
    ok(pg.evaluate("[...document.querySelectorAll('.clip.seq')].every(c=>c.querySelectorAll('.segs i').length===6)"), "barra de 6 cortes nos cards de sequencia")
    ok(pg.evaluate("document.querySelectorAll('.wall .wcol').length") == 4, "4 colunas a 1280", pg.evaluate("document.querySelectorAll('.wall .wcol').length"))
    ok(pg.evaluate("new Set([...document.querySelectorAll('.wall .clip')].map(c=>c.style.getPropertyValue('--r'))).size") == 3, "3 proporcoes (9:16, 4:5, 1:1)")
    ok(pg.evaluate("document.querySelectorAll('.wall a').length") == 0, "card sem destino nao finge ser link")
    ok(pg.evaluate("[...document.querySelectorAll('.wall img')].every(i=>i.alt.trim().length>20)"), "todo poster tem alt")
    ok(pg.evaluate("[...document.querySelectorAll('.wall figcaption b')].every(b=>b.textContent.trim())"), "todo card tem tipo no rotulo")
    ok(pg.evaluate("document.querySelectorAll('.chip').length") == 7, "7 filtros")
    pg.evaluate("scrollTo({top:0,behavior:'instant'})")
    pg.wait_for_timeout(500)
    ok(pg.evaluate("[...document.querySelectorAll('.wall video')].every(v=>v.paused)"), "longe da parede: nenhum video tocando")
    pg.evaluate("document.getElementById('mural').scrollIntoView({block:'start',behavior:'instant'})")
    pg.wait_for_timeout(2600)
    tocando = pg.evaluate("[...document.querySelectorAll('.wall video')].filter(v=>!v.paused).length")
    ok(tocando >= 4, "na parede: os cards da tela tocam sozinhos", tocando)
    y0 = pg.evaluate("[...document.querySelectorAll('.wcol')].map(c=>c.style.transform)")
    pg.evaluate("scrollBy({top:300,behavior:'instant'})")
    pg.wait_for_timeout(900)
    y1 = pg.evaluate("[...document.querySelectorAll('.wcol')].map(c=>c.style.transform)")
    ok(y0 != y1 and len(set(y1)) > 1, "as colunas deslizam, cada uma num ritmo", y1[:2])
    pg.evaluate("document.querySelector('.clip.seq').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_function("(()=>{const v=document.querySelector('.clip.seq video');return v&&!v.paused&&(v.currentTime%3)>2.82&&(v.currentTime%3)<2.95})()", timeout=9000, polling=10)
    ok(pg.evaluate("(()=>{const x=document.querySelector('.clip.seq .xf');return !!x&&x.style.display==='block'})()"), "ASCII entra perto do corte de 3 s")
    pg.click(".chip[data-f=personagem]")
    pg.wait_for_timeout(1200)
    vis = pg.evaluate("[...document.querySelectorAll('.wall .clip')].filter(c=>!c.hidden).map(c=>c.dataset.src.split('/').pop()).sort().join(',')")
    ok(vis == ",".join(f"personagem-{i}.mp4" for i in range(1, 7)), "filtro Personagem abre as 6 cenas soltas", vis[:60])
    ok(pg.evaluate("[...document.querySelectorAll('.trab-desc p')].filter(p=>!p.hidden).map(p=>p.dataset.f).join()") == "personagem", "a frase acompanha o filtro")
    pg.click(".chip[data-f=avatar]")
    pg.wait_for_timeout(1200)
    ok(pg.evaluate("[...document.querySelectorAll('.wall .clip')].filter(c=>!c.hidden).every(c=>c.dataset.cat==='avatar')"), "filtro Avatares so mostra avatar")
    pg.click(".chip[data-f=all]")
    pg.wait_for_timeout(1200)
    ok(pg.evaluate("[...document.querySelectorAll('.wall .clip')].filter(c=>!c.hidden).length") == 21, "Todos volta os 21")

    print("\n-- /work: os dois apps --")
    ok(pg.evaluate("[...document.querySelectorAll('.app h3')].map(h=>h.textContent).join(',')") == "LoopVideo,Avatarize", "LoopVideo e Avatarize em destaque")
    hrefs = pg.evaluate("[...document.querySelectorAll('.app-cta a')].map(a=>a.getAttribute('href')).join(' ')")
    ok(hrefs.count("github.com/rafaguiar-dev/") == 4 and hrefs.count("releases/latest") == 2, "baixar + GitHub nos dois", hrefs[:60])
    ok(pg.evaluate("document.querySelectorAll('#app-loop .app-tabs button').length") == 4, "4 abas no palco do LoopVideo")
    ok(pg.evaluate("document.querySelectorAll('#app-avatar .call').length") == 6, "6 etapas no holofote do Avatarize")
    ok(pg.evaluate("document.querySelectorAll('.ax').length") == 3, "3 itens em 'tambem construi'")
    ok(pg.evaluate("[...document.querySelectorAll('.ax-flow')].every(o=>o.children.length>=4)"), "cada um com o fluxo em etapas")
    pg.evaluate("document.getElementById('app-loop').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(2500)
    ok(pg.evaluate("!document.querySelector('#app-loop .app-vid').paused"), "o video-guia toca com o app na tela")
    pg.click("#app-loop .app-tabs button[data-t='20']")
    pg.wait_for_timeout(800)
    ok(pg.evaluate("document.querySelector('#app-loop .app-tabs button.on').dataset.t") == "20", "clique na aba pula para ela")
    ok(not pg.evaluate("!!document.getElementById('decisions')"), "/decisions saiu")

    print("\n-- /stack: as tres telas --")
    ok(pg.evaluate("[...document.querySelectorAll('.stg h3')].map(h=>h.textContent).join(',')") == "Gero,Integro,Construo", "Gero, Integro, Construo")
    ok(pg.evaluate("document.querySelectorAll('.stg .stg-tools li').length") == 17, "17 ferramentas, as do perfil do GitHub")
    pg.evaluate("document.querySelector('.pipe').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(1500)
    acesos = pg.evaluate("""[...document.querySelectorAll('.scr canvas')].map(c=>{const g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<d.length;i+=16)if(d[i]+d[i+1]+d[i+2]>200)n++;return n})""")
    ok(all(n > 30 for n in acesos), "as tres telas desenham", acesos)
    ok(pg.evaluate("document.querySelectorAll('.stg.hot').length") == 1, "o pulso acende uma etapa por vez")

    print("\n-- links --")
    ok(pg.evaluate("document.querySelectorAll('a[href=\"#\"]').length") == 0, "nenhum href vazio")
    ok(pg.evaluate("document.querySelectorAll('a[href^=\"mailto\"]').length") == 1, "mailto preservado")
    ext = pg.evaluate("[...document.querySelectorAll('a[target=_blank]')].map(a=>a.rel).join('|')")
    ok(set(ext.split("|")) == {"noopener noreferrer"}, "rel completo nos externos", ext[:40])
    ok(pg.evaluate("document.querySelectorAll('.socials a').length") == 2, "so GitHub e LinkedIn (os que tem URL) aparecem")
    ok(pg.evaluate("document.querySelector('.big-mail').href") == "mailto:rafaguiar.dev@gmail.com", "e-mail que existe")

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
    pg.evaluate("document.querySelector('#reel .stats').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(400)
    print("\n-- reduced motion --")
    vals = pg.evaluate("[...document.querySelectorAll('[data-count]')].map(e=>e.textContent)")
    ok(vals == ["1500+", "12", "9", "3+"], "valor final imediato", vals)
    pg.evaluate("document.getElementById('mural').scrollIntoView({block:'start',behavior:'instant'})")
    pg.wait_for_timeout(900)
    ok(pg.evaluate("document.querySelectorAll('.wall video').length") == 0, "nenhum video criado sozinho")
    ok(pg.evaluate("[...document.querySelectorAll('.wcol')].every(c=>!c.style.transform)"), "a parede nao desliza")
    pg.evaluate("document.getElementById('app-loop').scrollIntoView({block:'center',behavior:'instant'})")
    pg.wait_for_timeout(900)
    ok(pg.evaluate("document.querySelector('#app-loop .app-vid').paused"), "video-guia parado")
    ok(pg.evaluate("[...document.querySelectorAll('.clip')].every(c=>!c.classList.contains('asc-on'))"), "sem camada ASCII")
    ok(pg.evaluate("[...document.querySelectorAll('.ax-flow li')].every(l=>l.classList.contains('lit'))"), "fluxos acesos e parados")
    ok(len(e3) == 0, "sem erro de pagina", e3[:2])
    b.close()

print("\n" + "=" * 54)
print("TUDO PASSOU" if not falhas else "FALHOU:\n  - " + "\n  - ".join(falhas))

sys.exit(1 if falhas else 0)
