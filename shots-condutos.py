# captura o hero em headless para conferir os condutos (Data Gravity reduzido).
# headless de verdade: o painel do app fica oculto e o rAF nao roda la.
import os, sys
from playwright.sync_api import sync_playwright

OUT = os.path.dirname(os.path.abspath(__file__))
URL = "file:///D:/PROJETOS/PORTIFOLIO/mockup.html"
W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1440, 900)
TAG = sys.argv[3] if len(sys.argv) > 3 else "%d" % W


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console." + m.type + ": " + m.text)
              if m.type == "error" else None)
        pg.goto(URL)
        pg.wait_for_timeout(1200)

        # o ciclo do pacote e' 5,6 s: seis quadros cobrem viagem, absorcao e pausa
        for i in range(8):
            pg.screenshot(path=os.path.join(OUT, "c%s-%d.png" % (TAG, i)),
                          clip={"x": 0, "y": 0, "width": W, "height": min(H, 900)})
            pg.wait_for_timeout(700)

        # a area do texto tem que ficar limpa: conta pixels acesos dentro dela
        probe = pg.evaluate("""() => {
          const st = document.getElementById('stage');
          const cv = document.getElementById('ascii');
          const el = document.querySelector('.hero-copy');
          const b = st.getBoundingClientRect(), r = el.getBoundingClientRect();
          const d = Math.min(devicePixelRatio || 1, 2);
          const g = cv.getContext('2d');
          const box = { x: (r.left-b.left)*d, y: (r.top-b.top)*d,
                        w: r.width*d, h: r.height*d };
          const im = g.getImageData(box.x|0, box.y|0, box.w|0, box.h|0).data;
          let lit = 0;
          for (let i = 0; i < im.length; i += 4)
            if (im[i] + im[i+1] + im[i+2] > 108) lit++;
          return { stage:[b.width|0, b.height|0], copy:[r.left-b.left|0, r.top-b.top|0, r.width|0, r.height|0],
                   litPct: +(100*lit/(im.length/4)).toFixed(3) };
        }""")
        fps = pg.evaluate("""() => new Promise(res => {
            let n = 0; const s = performance.now();
            const tick = () => { if (++n < 60) requestAnimationFrame(tick);
              else res(Math.round(60000 / (performance.now() - s))); };
            requestAnimationFrame(tick); })""")
        b.close()
        print("viewport %dx%d" % (W, H), probe, "fps:", fps)
        print("erros:", errs if errs else "nenhum")


main()
