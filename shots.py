# captura o hero em headless: o painel do navegador do app fica oculto,
# entao rAF nao roda la e a captura sai vazia (armadilha da secao 2 do CONTINUAR.md)
import os
from playwright.sync_api import sync_playwright

OUT = os.path.dirname(os.path.abspath(__file__))
URL = "file:///D:/PROJETOS/PORTIFOLIO/mockup.html"


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL)
        clip = {"x": 0, "y": 56, "width": 1440, "height": 844}
        t0 = [0]

        def shot(name):
            pg.screenshot(path=os.path.join(OUT, name), clip=clip)
            now = pg.evaluate("performance.now()")
            print("  %-24s %6.0f ms  (+%.0f)" % (name, now, now - t0[0]))
            return now

        pg.wait_for_timeout(900)
        shot("11-idle.png")

        # rastro: arrasta o cursor pelo rosto
        for x, y in [(700, 700), (780, 630), (860, 560), (940, 500), (1010, 455), (1075, 425)]:
            pg.mouse.move(x, y); pg.wait_for_timeout(30)
        shot("12-rastro.png")

        # clique: onda curta + revelacao
        pg.mouse.down(); pg.mouse.up()
        t0[0] = pg.evaluate("performance.now()")
        shot("13-onda.png")
        shot("14-revelando.png")
        pg.wait_for_timeout(500)
        shot("15-foto-limpa.png")
        pg.wait_for_timeout(1800)
        shot("16-voltando.png")
        pg.wait_for_timeout(900)
        fim = shot("17-idle-de-novo.png")

        # a chamada dos 20 s (conta a partir do fim da revelacao)
        pg.wait_for_timeout(max(0, int(20000 - (pg.evaluate("performance.now()") - fim)) - 200))
        t0[0] = pg.evaluate("performance.now()")
        for n in range(6):
            shot("18-chamada-%d.png" % n)

        fps = pg.evaluate("""() => new Promise(res => {
            let n = 0; const s = performance.now();
            const tick = () => { if (++n < 60) requestAnimationFrame(tick);
              else res(Math.round(60000 / (performance.now() - s))); };
            requestAnimationFrame(tick); })""")
        b.close()
        print("fps:", fps, " erros:", errs if errs else "nenhum")


main()
