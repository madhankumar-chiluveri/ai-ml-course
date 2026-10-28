# Component markup

All classes live in `assets/base.css`. Every color comes from a token, so dark mode works with no extra code.

## Contents
1. Page frame
2. Panels, labels, pills, marks
3. Lists
4. Callouts and editor notes
5. Quote and equation
6. Tables
7. Comparison split
8. Box-and-pipe rails and loops
9. Causal chains
10. Figures, charts and legends
11. Diagnostic card
12. Laws grid and leverage rows
13. Special layouts: iceberg, tiers, log bars, gauge, nesting, balance beam

---

## 1. Page frame

```html
<header class="top"><div class="wrap top-in">
  <a class="brand" href="#top">Book Title<span>Author · Ch 2</span></a>
  <nav class="tnav" aria-label="Chapters">
    <a href="chapter-01-x.html"><b>01</b><span>Basics</span></a>
    <a href="chapter-02-y.html#ch2" data-spy="ch2" aria-current="true"><b>02</b><span>Zoo</span></a>
  </nav></div></header>
<main id="top">
<section class="hero wrap">
  <p class="eyebrow">Author · Book · Chapter 2</p>
  <h1>Thesis sentence. <em>Accent clause.</em></h1>
  <p class="lede">One or two sentences.</p>
  <!-- optional .key notation grid; see the systems book pages for the full block -->
</section>
<section class="chapter wrap" id="ch2">
  <div class="ch-open"><div class="ch-num"><small>CHAPTER</small>02</div><div class="ch-body">
    <p class="eyebrow">Part One · …</p><h2>Chapter title</h2><p class="ch-sub">Subtitle</p>
    <p class="goal"><b class="l">Goal</b>What the reader will be able to do.</p>
    <nav class="cmap"><a href="#c2-x"><b>2.1</b>Section</a> …</nav></div></div>
  <section class="sec" id="c2-x">
    <header class="sh"><span class="sid">2.1 · Eyebrow</span><h3>Section title</h3><p>Lede.</p></header>
    <div class="sub"><h4>Sub-heading</h4> … </div>
  </section>
  <a class="next" href="chapter-03-z.html"><span>Next chapter</span><b>03 · Title →</b></a>
</section>
<footer class="foot wrap"><p>Source and editor-tag legend.</p></footer>
</main>
```
Grids: `.g2 .g3 .g4 .g5` collapse on their own at narrow widths. Children with long text need nothing extra, because `min-width:0` is already set.

## 2. Panels, labels, pills, marks

```html
<div class="panel">            <!-- neutral box; add .ink for a black border -->
<div class="panel tint t-bal">  <!-- tinted: t-stock t-flow t-bal t-rein t-delay t-risk t-note t-info -->
  <div class="ph"><span class="lab" style="--k:var(--bal)">Label</span><span class="pill" style="--k:var(--bal);--kb:var(--bal-bg)">tag</span></div>
  <h5>Title</h5><p>Text</p></div>
<span class="lb" style="--k:var(--rein)">R</span>   <!-- loop badge / numbered disc -->
<span class="m ok">✓</span> <span class="m no">✗</span>   <!-- table check marks -->
```

## 3. Lists

```html
<ul class="dl" style="--k:var(--risk)"><li>dash-marked item</li></ul>
<ol class="steps" style="--k:var(--delay)"><li><span><b>Step.</b> Text.</span></li></ol>  <!-- real sequences only -->
<dl class="kv"><dt>Goal</dt><dd>21 °C</dd><dt>Gap</dt><dd>+6 °C</dd></dl>
```

## 4. Callouts and editor notes

```html
<div class="call imp"><span class="tag">Important · title</span><p>…</p></div>   <!-- imp cau nte wrn tip -->
<aside class="ed"><span class="tag">Added</span><p>New material not in the source.</p></aside>
<aside class="ed fix"><span class="tag">Corrected</span><p>What the source said, and why it was wrong.</p></aside>
```

## 5. Quote and equation

```html
<blockquote class="quote">"Quote."<cite>AUTHOR</cite></blockquote>
<div class="eq"><span class="s">Δ Stock</span> = <span class="fi">Inflow</span> − <span class="fo">Outflow</span><small>units / note</small></div>
<!-- term colors: .s stock .fi inflow .fo outflow .b balancing .r reinforcing .d delay -->
```

## 6. Tables

```html
<div class="tbl"><table class="wide">  <!-- .wide = min 720px; the box scrolls, not the page -->
  <thead><tr><th>Name</th><th class="n">Value</th></tr></thead>
  <tbody><tr class="hl" style="--kb:var(--risk-bg)"><td>…</td><td class="n neg">−120</td></tr></tbody>
</table></div>
<!-- td.n right-aligned mono · td.pos green · td.neg red · td.c centered -->
```

## 7. Comparison split

```html
<div class="split">
  <div class="side bad"><span class="lab">Old way</span><h4>…</h4><p>…</p></div>   <!-- bad good r s, or no class = ink -->
  <div class="vs"><span>vs</span></div>
  <div class="side good"><span class="lab">Better way</span><h4>…</h4><p>…</p></div>
</div>
```

## 8. Box-and-pipe rails and loops

```html
<div class="loop">                                    <!-- omit .loop/.ret for an open rail -->
  <div class="rail">
    <div class="node cloud"><small>source</small></div>
    <div class="pipe flow"><span>INFLOW</span></div>     <!-- pipe kinds: flow info bal rein risk delay (adds ‖) -->
    <div class="node stock"><span class="nk">Stock</span><b>Title</b><small>detail</small></div>
    <div class="pipe info"><span>reading</span></div>
    <div class="node ctrl"><span class="nk">Decide</span><b>…</b></div>
  </div>
  <div class="ret b"><span>what feeds back</span></div>   <!-- ret kinds: b r d -->
</div>
```
Node kinds: `stock stockd flow goal ctrl bal rein delay risk cloud`, or no kind for ink. Below 760px the rail turns vertical and `.ret` becomes a labeled bar.

## 9. Causal chains

```html
<div class="chain x"><span>Rumor</span><i>→</i><span>Withdrawals</span><i>→</i><span>Reserves plunge</span><i>↺</i></div>
<!-- kinds: r (reinforcing) b (balancing) x (risk) s (stock); no kind = ink -->
```

## 10. Figures, charts and legends

```html
<figure class="fig ink">
  <p class="ft">Chart title · units</p>
  <div class="scroll" id="ch-name" style="--minw:420px"></div>   <!-- AE.plot / AE.dg target -->
  <figcaption>What to notice.</figcaption>
</figure>
<div class="scroll" id="sp-name"></div>   <!-- AE.spark inside a panel -->
```
Host id prefixes: `ch-` charts, `sp-` sparks, `dg-` schematics. `check.py` relies on these prefixes. Legends are generated from series `label`s.

## 11. Diagnostic card

```html
<div class="diag">
  <div class="diag-h"><span>Tool name</span><span>run in order</span></div>
  <ol><li><div><b><span class="chk"></span>Question?</b><p>What to look for.</p></div></li></ol>
</div>
```

## 12. Laws grid and leverage rows

```html
<div class="laws">
  <div><span class="ln-n">1</span><div><b>Law title</b><p>One sentence.</p></div></div>
  <div class="span"><span class="ln-n">7</span><div>…</div></div>   <!-- .span = full width for an odd last item -->
</div>
<div class="lev"><h5>1 · Problem</h5>
  <div class="lo"><span class="lab">✗ Low leverage</span><p>…</p></div>
  <div class="hi"><span class="lab">✓ High leverage</span><ul class="dl" style="--k:var(--bal)"><li>…</li></ul></div></div>
```

## 13. Special layouts

```html
<!-- iceberg: 4 events above, 4 hidden causes below -->
<div class="berg"><div class="above"><div><span class="ev">"Event"</span></div>…</div>
  <div class="wl">▼ Waterline · …</div>
  <div class="below"><div><span class="st">Hidden stock</span><br>…</div>…</div></div>

<!-- tiers -->
<div class="tiers"><div class="tier" style="--k:var(--bal);--kb:var(--bal-bg)">
  <div class="th"><span class="lab">Tier 1</span><b>Name</b><span class="small">fast · cheap</span></div>
  <div class="tb"><!-- rail + dl.kv --></div></div></div>

<!-- log-scale bars: width = (log10(v) − log10(min)) / (log10(max) − log10(min)) -->
<div class="hbars"><div class="hbar"><span class="nm">A</span><div class="tr"><div class="fl" style="--k:var(--risk);width:12.7%"></div><span class="vl">0.000043</span></div></div></div>
<div class="scale"><span>10⁻⁵</span>…<span>1</span></div>

<!-- gauge: operating zone → stretched → broken -->
<div class="gauge"><div style="--k:var(--bal);--kb:var(--bal-bg)"><b>Zone</b><span>…</span></div>…</div>

<!-- nesting (hierarchy as containment) -->
<div class="nest"><span class="lab">Total</span><div class="row"><div class="sub2"><span class="lab">A</span><div class="mods"><span>A1</span><span>A2</span></div></div>…</div></div>

<!-- balance beam -->
<div class="beam"><div class="bar"><span>Left<small>…</small></span><i>◄ ⚖ ►</i><span>Right<small>…</small></span></div><div class="fulcrum"></div></div>
```
