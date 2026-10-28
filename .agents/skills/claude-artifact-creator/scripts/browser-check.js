/* Paste as the `function` argument of a browser evaluate call (e.g. chrome-devtools evaluate_script)
   on the opened page. Measures, it does not screenshot. Expect every array empty and docOverflow false.
   - emptyHosts:     chart/diagram hosts that rendered no <svg>
   - nodeOverflow:   schematic node text wider than its box (mono glyph budget exceeded)
   - outsideViewBox: any SVG text drawn past its viewBox (clipped labels, last x-tick)
   - labelOnBox:     schematic edge label sitting on top of a node box
   - docOverflow:    page scrolls sideways */
async () => {
  await document.fonts.ready;
  const id = el => (el.closest('[id]') || {}).id;
  const emptyHosts = [...document.querySelectorAll('[id^="sp-"],[id^="ch-"],[id^="dg-"]')].filter(h => !h.querySelector('svg')).map(h => h.id);
  const nodeOverflow = [];
  document.querySelectorAll('svg.dg g.n').forEach(g => {
    const r = g.querySelector('rect.nb'); if (!r) return; const rb = r.getBBox();
    g.querySelectorAll('text').forEach(t => { const b = t.getBBox(); if (b.x < rb.x + 2 || b.x + b.width > rb.x + rb.width - 2) nodeOverflow.push(id(g) + ': ' + t.textContent + ' (' + Math.round(b.width) + '/' + Math.round(rb.width) + ')'); });
  });
  const outsideViewBox = [];
  document.querySelectorAll('svg[viewBox]').forEach(s => {
    const vb = s.viewBox.baseVal; if (!vb || !vb.width) return;
    s.querySelectorAll('text').forEach(t => { try { const b = t.getBBox(); if (b.x < vb.x - 2 || b.y < vb.y - 2 || b.x + b.width > vb.x + vb.width + 2 || b.y + b.height > vb.y + vb.height + 2) outsideViewBox.push(id(s) + ': ' + t.textContent); } catch (e) {} });
  });
  const labelOnBox = [];
  document.querySelectorAll('svg.dg').forEach(s => {
    const boxes = [...s.querySelectorAll('g.n rect.nb')].map(r => r.getBBox());
    s.querySelectorAll(':scope > text.lab').forEach(t => { const b = t.getBBox(); boxes.forEach(r => { if (b.x < r.x + r.width && b.x + b.width > r.x && b.y < r.y + r.height && b.y + b.height > r.y) labelOnBox.push(id(s) + ': ' + t.textContent); }); });
  });
  return { emptyHosts, nodeOverflow, outsideViewBox, labelOnBox, docOverflow: document.documentElement.scrollWidth > window.innerWidth };
}
