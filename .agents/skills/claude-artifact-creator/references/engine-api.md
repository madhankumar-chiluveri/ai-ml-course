# Engine API (`assets/engine.js`, global `AE`)

Start every spec script with:

```js
(function(){
'use strict';
var E=AE.E,T=AE.T,fn=AE.fn,plot=AE.plot,spark=AE.spark,dg=AE.dg,safe=AE.safe;
safe(function(){ /* one chart or diagram */ });
safe(function(){ /* the next one */ });
AE.spy();          // highlights the header nav link of the section in view (uses a[data-spy])
})();
```

Helpers:
- `fn(f, a, b, n=160)` samples `f` into `[[x,y],…]`.
- `E(tag, attrs, parent)` creates an SVG element.
- `T(parent, x, y, text, cls, anchor)` adds text.
- `safe(f)` runs `f` and logs errors instead of throwing.

Color keys (`k`): `k-stock k-flow k-bal k-rein k-delay k-risk k-note k-info k-ink k-mute`.

## AE.plot(id, options): to-scale charts

| Option | Meaning |
|---|---|
| `w`, `h` | viewBox size (default 640×260). Keep 400–700 wide. |
| `m` | margins, merged into `{l:52,r:18,t:22,b:34}`. Raise `r` to 30+ when the last x tick is long. |
| `x`, `y` | `[min, max]` data domains. One scale per chart. |
| `xt`, `yt` | tick values. `xf`, `yf` format ticks. `yt` also draws grid lines. |
| `xl`, `yl` | axis captions (bottom-right, top-left). |
| `frame:false` | no axes (sparks) |
| `bands` | `[{x0,x1,k,label}]` shaded vertical regions (phases, regimes) |
| `refs` | `[{y,k,label,at:'left',below:true}]` dashed horizontal reference lines (goal, target, capacity) |
| `vlines` | `[{x,k,label,dy,anchor}]` dashed vertical markers (threshold, peak) |
| `series` | see below |
| `notes` | `[{x,y,t,k,dot,dx,dy,a}]` point annotations. `t` may contain `\n`. |
| `legend:false` | suppress the legend built from series labels |
| `label` | aria-label |

Series:
- `{data:[[x,y],…], k, label, dash, thin, area, dots, values, vf, end}` draws a line.
- `{type:'bar', data, k, label, bw, n, i, values}` draws bars. Use `n` and `i` to group bars side by side.
- `{type:'dots', data, k, r}` draws points only.

```js
plot('ch-stock',{w:460,h:250,x:[-0.35,5.35],y:[300,620],yt:[300,400,500,600],xt:[0,1,2,3,4,5],
  xf:function(d){return ['Start','Mon','Tue','Wed','Thu','Fri'][d];},
  refs:[{y:500,k:'k-mute',label:'start 500',at:'left',below:true}],
  series:[{data:[[0,500],[1,560],[2,480],[3,360],[4,410],[5,440]],k:'k-stock',dots:true,values:true,label:'buffer stock'}]});
```

## AE.spark(id, series, options): behavior shapes

This is `plot` with small defaults (`300×118`, `x:[0,1]`, no legend). Pass `y`, `refs`, `bands` and `notes` as needed.

```js
spark('sp-damped',[{data:fn(function(t){return 1-0.85*Math.exp(-4*t)*Math.cos(16*t);},0,1,200),k:'k-bal'}],{y:[0,2],refs:[{y:1,k:'k-bal'}]});
```

## AE.dg(id, spec): schematics (stock-and-flow, architecture)

```js
dg('dg-loop',{w:760,h:250,label:'aria description',
  nodes:{                                    // x,y,w,h in viewBox units
    c1:{x:20,y:62,w:76,h:46,kind:'cloud'},
    st:{x:290,y:44,w:200,h:82,kind:'stock',k:'STOCK',t:['Population','what you can count']},
    c2:{x:664,y:62,w:76,h:46,kind:'cloud'}},
  edges:[
    {a:'c1.r',b:'st.l',kind:'pipe',label:'INFLOW',lp:[195,52],lk:'c-flow'},
    {a:'st.b@0.3',via:[[350,200],[195,200]],b:[195,96],kind:'rein'},     // loop back to the valve
    {a:'st.r',b:'c2.l',kind:'pipe'}],
  valves:[[195,85],[577,85]],                // bow-tie on a pipe; add 'v' for a vertical pipe
  badges:[{x:272,y:166,t:'R',kind:'rein'}],  // loop badges: kind rein | bal
  delays:[[857,248,'v']],                    // ‖ marks across an edge ('v' = vertical edge)
  regions:[{x:8,y:150,w:924,h:294,t:'INFORMATION LAYER'}],
  texts:[{x:272,y:224,t:'more stock → more inflow',c:'lab c-rein',a:'middle'}]});
```

Reference:
- **Anchors:** `'node.side'` or `'node.side@fraction'`. Side is `l r t b`; the fraction runs along the side (default 0.5). A raw `[x,y]` is also accepted, e.g. to end an arrow under a valve at `[valveX, valveY+10]`.
- **Node kinds:**
  - `stock` and `stockd` (delay-tinted) draw a double border.
  - `b r i d x f` are tinted boxes: balancing, reinforcing, info, delay, risk, flow.
  - `goal` is a dashed green box; `mute` is a grey box.
  - `cloud` draws a source or sink.
  - `text` has no box.
  - No kind draws an ink box.
- **Node text:** `k` is an uppercase key line, `t[0]` is the bold title, `t[1…]` are detail lines. Budget the width at about 8.1px per title character (see SKILL.md gotchas).
- **Edge kinds:**
  - `pipe` is a thick flow with a big arrow.
  - `info` is a dashed signal.
  - `bal`, `rein`, `delay` and `ink` are solid.
  - `risk` is a dashed red "missing or broken link".
  - `good` is solid green.
  - `empty` is a dashed grey "nothing flows".
- **Edge options:** `noarrow:true` drops the arrowhead. `label` may contain `\n`. `lp:[x,y]` places the label (default: midpoint of the longest segment). `lk` colors it (`c-bal c-rein c-flow c-delay c-risk c-stock`). `anchor` aligns it.

Layout habits that keep diagrams clean:
- Put pipes on a row (y ≈ node center) and information on the rows below.
- Keep loop returns at a fixed y under the stocks.
- Route edges orthogonally with `via`.
- Keep 12px or more between an edge label and any box.
- Wide diagrams (more than 700 units) go in `.scroll` with `--minw` about 80% of `w`.
