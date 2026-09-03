# Sonda de medição

Injetar com `mcp__Claude_Browser__javascript_tool` depois de a rota carregar,
com o viewport já redimensionado e o tema já aplicado. A sonda mede; ela não
julga. O julgamento e a decisão de abrir PRD são do agente.

A sonda não substitui a interação: ela roda **depois** de o agente ter clicado
em cada elemento interativo e observado o resultado. `interactive_exercised`
precisa refletir cliques reais, não a contagem que a sonda enxerga.

## Script

```javascript
(() => {
  const doc = document.documentElement;
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const luminance = (rgb) => {
    const [r, g, b] = rgb.map((v) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const parse = (value) => {
    const m = value.match(/\d+(\.\d+)?/g);
    return m ? m.slice(0, 3).map(Number) : null;
  };
  const backdrop = (el) => {
    let node = el;
    while (node && node !== doc.parentNode) {
      const c = parse(getComputedStyle(node).backgroundColor || '');
      const a = getComputedStyle(node).backgroundColor.includes('rgba')
        ? Number(getComputedStyle(node).backgroundColor.split(',')[3])
        : 1;
      if (c && a > 0) return c;
      node = node.parentElement;
    }
    return [255, 255, 255];
  };
  const ratio = (fg, bg) => {
    const a = luminance(fg) + 0.05;
    const b = luminance(bg) + 0.05;
    return Number((Math.max(a, b) / Math.min(a, b)).toFixed(2));
  };

  const interactive = [...document.querySelectorAll(
    'a[href], button, input, select, textarea, [role="button"], [tabindex]:not([tabindex="-1"])'
  )].filter(visible);

  const smallTapTargets = interactive
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter(({ r }) => r.width < 44 || r.height < 44)
    .map(({ el, r }) => ({
      selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
        (el.className && typeof el.className === 'string'
          ? '.' + el.className.trim().split(/\s+/).join('.') : ''),
      width: Math.round(r.width),
      height: Math.round(r.height),
      text: (el.textContent || el.value || '').trim().slice(0, 40),
    }));

  const contrastFailures = [...document.querySelectorAll(
    'p, span, a, button, label, li, td, th, h1, h2, h3, h4, h5, h6'
  )].filter((el) => visible(el) && (el.textContent || '').trim())
    .map((el) => {
      const s = getComputedStyle(el);
      const fg = parse(s.color);
      if (!fg) return null;
      const size = parseFloat(s.fontSize);
      const bold = Number(s.fontWeight) >= 700;
      const large = size >= 24 || (size >= 18.66 && bold);
      const value = ratio(fg, backdrop(el));
      const minimum = large ? 3 : 4.5;
      return value < minimum
        ? { selector: el.tagName.toLowerCase(), ratio: value, minimum,
            text: el.textContent.trim().slice(0, 40) }
        : null;
    }).filter(Boolean).slice(0, 25);

  const boxes = interactive.map((el) => ({ el, r: el.getBoundingClientRect() }));
  const overlaps = [];
  for (let i = 0; i < boxes.length && overlaps.length < 25; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i].r;
      const b = boxes[j].r;
      if (boxes[i].el.contains(boxes[j].el) || boxes[j].el.contains(boxes[i].el)) continue;
      if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) {
        overlaps.push({
          a: boxes[i].el.tagName.toLowerCase(),
          b: boxes[j].el.tagName.toLowerCase(),
          text: (boxes[i].el.textContent || '').trim().slice(0, 30),
        });
        break;
      }
    }
  }

  const scrollers = [...document.querySelectorAll('*')].filter((el) => {
    const s = getComputedStyle(el);
    return /(auto|scroll)/.test(s.overflowX + s.overflowY) && el.scrollHeight > el.clientHeight + 1;
  }).length;

  return {
    url: location.href,
    theme: doc.dataset.theme || doc.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    document_scroll_width: doc.scrollWidth,
    document_client_width: doc.clientWidth,
    document_scroll_height: doc.scrollHeight,
    scroll_containers: scrollers,
    interactive_total: interactive.length,
    small_tap_targets: smallTapTargets,
    contrast_failures: contrastFailures,
    overlaps,
  };
})()
```

## Campos que o agente completa

A sonda não sabe o que o agente fez. Antes de gravar o relatório em
`visual_state.py probe`, acrescentar ao JSON:

- `console_errors`: contagem real vinda de `read_console_messages` com
  `onlyErrors`, depois de exercitar a página;
- `interactive_exercised`: quantos elementos interativos foram de fato
  acionados. O script recusa a sondagem quando este número difere de
  `interactive_total`;
- `theme`: o tema que o agente aplicou, que precisa coincidir com o medido;
- `findings`: lista dos defeitos que o agente decidiu registrar, cada um com
  `selector`, `problema` e `esperado`. Medição problemática sem achado é
  recusada pelo script.

## Limites da sonda

O contraste é calculado sobre o primeiro ancestral com fundo opaco; imagem de
fundo, gradiente e sobreposição translúcida não são resolvidos e pedem
verificação manual quando o valor ficar perto do limite. Sobreposição só
considera elementos interativos entre si. Nenhum desses limites autoriza
declarar a rota auditada sem os demais itens do checklist.
