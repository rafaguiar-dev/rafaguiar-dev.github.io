from playwright.sync_api import sync_playwright
U="http://localhost:8765/mockup.html"; T="tmp/v27/"
with sync_playwright() as p:
    b=p.chromium.launch()
    for (W,H,nomes) in [(1440,900,["all","avatar","produto","broll"]),(390,844,["all","produto"])]:
        pg=b.new_page(viewport={"width":W,"height":H})
        pg.goto(U); pg.wait_for_timeout(2500)
        pg.evaluate("document.getElementById('section-lock') && document.getElementById('section-lock').getAttribute('aria-pressed')==='true' && document.getElementById('section-lock').click()")
        for f in nomes:
            pg.evaluate("f=>document.querySelector('.chip[data-f='+f+']').click()",f)
            pg.wait_for_timeout(1500)
            # rola a seção inteira para disparar os revelados
            h=pg.evaluate("document.querySelector('#reel').getBoundingClientRect().height")
            top=pg.evaluate("scrollY+document.querySelector('#reel').getBoundingClientRect().top")
            for y in range(0,int(h),400):
                pg.evaluate("y=>scrollTo({top:y,behavior:'instant'})",top+y); pg.wait_for_timeout(250)
            pg.evaluate("y=>scrollTo({top:y,behavior:'instant'})",top); pg.wait_for_timeout(1500)
            pg.locator("#reel").screenshot(path=f"{T}reel-{W}-{f}.png")
        pg.close()
    b.close()
