# rafaguiar.dev

Site de portfólio de **Rafael Aguiar** — AI Automation Engineer.
Página única, HTML/CSS/JS puro, sem framework, sem build de node.

**No ar:** https://rafaguiar.dev

## Como funciona

| arquivo | papel |
|---|---|
| `template.html` | **o site.** É aqui que se edita. |
| `build.py` | comprime as imagens, embute em base64 e gera a página final |
| `docs/index.html` | **gerado.** É o que o GitHub Pages publica. Nunca editar à mão. |
| `verificar.py` | bateria de testes: sintaxe, layout, fps, acessibilidade |
| `assets/`, `hero*.png` | as imagens de origem que o `build.py` consome |

```bash
python build.py       # gera docs/index.html
python verificar.py   # tem que dizer TUDO PASSOU antes de publicar
```

Depois: `git add -A && git commit -m "..." && git push`. O Pages republica sozinho.

## Licença

**Todos os direitos reservados.** Veja [LICENSE](LICENSE).

O código está visível porque um site estático precisa estar — isso não é permissão
para copiar. Você pode ler, aprender e reaproveitar trechos técnicos genéricos.
Você não pode republicar o site, vender o design como template, nem usar o nome,
a foto ou os dados pessoais do autor.
