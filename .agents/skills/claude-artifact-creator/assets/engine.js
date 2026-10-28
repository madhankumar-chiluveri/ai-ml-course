/* claude-artifact-creator engine: chart (plot/spark) + stock-and-flow schematic (dg) + nav scroll-spy.
   Exposes window.AE. Every mark is placed through one scale per chart; all colors come from CSS tokens. */
var AE=(function(){
'use strict';
var NS='http://www.w3.org/2000/svg', XL='http://www.w3.org/1999/xlink';
function E(tag,attrs,parent){var e=document.createElementNS(NS,tag);if(attrs){for(var k in attrs){if(attrs[k]!==null&&attrs[k]!==undefined)e.setAttribute(k,attrs[k]);}}if(parent)parent.appendChild(e);return e;}
function T(p,x,y,s,cls,anchor){var t=E('text',{x:x,y:y,'class':cls||'','text-anchor':anchor||'start'},p);t.textContent=s;return t;}
function lines(p,x,y,s,cls,anchor,lh){String(s).split('\n').forEach(function(l,i){T(p,x,y+i*(lh||14),l,cls,anchor);});}
function fn(f,a,b,n){n=n||160;var r=[];for(var i=0;i<=n;i++){var x=a+(b-a)*i/n;r.push([x,f(x)]);}return r;}
function pth(pts,sx,sy){return 'M'+pts.map(function(p){return sx(p[0]).toFixed(1)+','+sy(p[1]).toFixed(1);}).join(' L');}
function safe(f){try{f();}catch(err){if(window.console)console.error(err);}}

/* ───────── chart engine: one scale per chart, every mark placed through it ───────── */
function plot(id,o){
  var host=document.getElementById(id); if(!host) return;
  var W=o.w||640,H=o.h||260,m=Object.assign({l:52,r:18,t:22,b:34},o.m||{});
  var x0=o.x[0],x1=o.x[1],y0=o.y[0],y1=o.y[1];
  var sx=function(v){return m.l+(v-x0)/(x1-x0)*(W-m.l-m.r);};
  var sy=function(v){return H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);};
  var svg=E('svg',{viewBox:'0 0 '+W+' '+H,role:'img','aria-label':o.label||''});
  (o.bands||[]).forEach(function(b){E('rect',{x:sx(b.x0),y:m.t,width:sx(b.x1)-sx(b.x0),height:H-m.t-m.b,'class':'band '+(b.k||'k-mute')},svg);if(b.label)T(svg,(sx(b.x0)+sx(b.x1))/2,m.t+13,b.label,'sm t2','middle');});
  (o.yt||[]).forEach(function(v){E('line',{x1:m.l,x2:W-m.r,y1:sy(v),y2:sy(v),'class':'grid'},svg);T(svg,m.l-7,sy(v)+4,(o.yf||String)(v),'t2 sm','end');});
  if(o.frame!==false){E('line',{x1:m.l,x2:W-m.r,y1:H-m.b,y2:H-m.b,'class':'axis'},svg);E('line',{x1:m.l,x2:m.l,y1:m.t,y2:H-m.b,'class':'axis'},svg);}
  (o.xt||[]).forEach(function(v){T(svg,sx(v),H-m.b+16,(o.xf||String)(v),'t2 sm','middle');});
  if(o.xl)T(svg,W-m.r,H-3,o.xl,'t2 sm','end');
  if(o.yl)T(svg,m.l+4,m.t-8,o.yl,'t2 sm','start');
  (o.vlines||[]).forEach(function(v){var g=E('g',{'class':v.k||'k-ink'},svg);E('line',{x1:sx(v.x),x2:sx(v.x),y1:m.t,y2:H-m.b,'class':'ref'},g);if(v.label){var px=sx(v.x),a=v.anchor||(px>W-m.r-50?'end':(px<m.l+50?'start':'middle'));T(g,px+(a==='end'?-5:a==='start'?5:0),m.t+(v.dy||28),v.label,'sm kt tb halo',a);}});
  (o.refs||[]).forEach(function(r){var g=E('g',{'class':r.k||'k-ink'},svg);E('line',{x1:m.l,x2:W-m.r,y1:sy(r.y),y2:sy(r.y),'class':'ref'},g);if(r.label){var left=r.at==='left';T(g,left?m.l+6:W-m.r-6,sy(r.y)+(r.below?15:-6),r.label,'sm kt tb halo',left?'start':'end');}});
  var leg=[];
  (o.series||[]).forEach(function(s){
    var g=E('g',{'class':s.k||'k-ink'},svg);
    if(s.label)leg.push(s);
    if(s.type==='bar'){
      var unit=(W-m.l-m.r)/(x1-x0),bw=s.bw||unit*0.7,n=s.n||1,i=s.i||0,w=bw/n,base=s.base!==undefined?s.base:Math.max(0,y0);
      s.data.forEach(function(d){var cx=sx(d[0])-bw/2+i*w,ya=sy(d[1]),yb=sy(base);E('rect',{x:cx+0.5,y:Math.min(ya,yb),width:Math.max(1,w-1),height:Math.max(0.5,Math.abs(yb-ya)),'class':'bar'},g);if(s.values)T(g,cx+w/2,ya-5,(s.vf||String)(d[1]),'sm kt tb','middle');});
      return;
    }
    if(s.type!=='dots'){
      if(s.area){var b0=sy(Math.max(y0,0)),F=s.data[0],L=s.data[s.data.length-1];E('path',{d:pth(s.data,sx,sy)+' L'+sx(L[0]).toFixed(1)+','+b0.toFixed(1)+' L'+sx(F[0]).toFixed(1)+','+b0.toFixed(1)+' Z','class':'area'},g);}
      E('path',{d:pth(s.data,sx,sy),'class':'ln'+(s.dash?' dash':'')+(s.thin?' thin':'')},g);
    }
    if(s.dots||s.type==='dots'){(s.pts||s.data).forEach(function(d){E('circle',{cx:sx(d[0]),cy:sy(d[1]),r:s.r||4,'class':'dot'},g);if(s.values)T(g,sx(d[0]),sy(d[1])+(s.vdy||-9),(s.vf||String)(d[1]),'sm kt tb halo','middle');});}
    if(s.end){var Z=s.data[s.data.length-1];T(g,sx(Z[0])+(s.endx||6),sy(Z[1])+(s.endy||4),s.end,'sm kt tb halo',s.enda||'start');}
  });
  (o.notes||[]).forEach(function(n){var g=E('g',{'class':n.k||'k-ink'},svg);if(n.dot)E('circle',{cx:sx(n.x),cy:sy(n.y),r:4.5,'class':'dot'},g);lines(g,sx(n.x)+(n.dx||0),sy(n.y)+(n.dy===undefined?-10:n.dy),n.t,'sm kt halo'+(n.b===false?'':' tb'),n.a||'middle',13);});
  host.appendChild(svg);
  if(leg.length&&o.legend!==false){var lg=document.createElement('div');lg.className='legend';leg.forEach(function(s){var sp=document.createElement('span');sp.className=s.k||'k-ink';var i=document.createElement('i');if(s.type==='bar')i.className='bar';else if(s.dash)i.className='dash';sp.appendChild(i);sp.appendChild(document.createTextNode(s.label));lg.appendChild(sp);});host.parentNode.insertBefore(lg,host.nextSibling);}
}
function spark(id,series,o){o=o||{};plot(id,Object.assign({w:300,h:118,m:{l:12,r:12,t:12,b:14},x:[0,1],y:[0,1.05],series:series,legend:false},o));}

/* ───────── schematic engine: stocks, pipes, valves, clouds, links ───────── */
function midpt(pts){var best=-1,bi=0;for(var i=0;i<pts.length-1;i++){var d=Math.abs(pts[i+1][0]-pts[i][0])+Math.abs(pts[i+1][1]-pts[i][1]);if(d>best){best=d;bi=i;}}return [(pts[bi][0]+pts[bi+1][0])/2,(pts[bi][1]+pts[bi+1][1])/2-7];}
function dg(id,o){
  var host=document.getElementById(id); if(!host) return;
  var svg=E('svg',{viewBox:'0 0 '+o.w+' '+o.h,role:'img','aria-label':o.label||'','class':'dg'});
  var N=o.nodes||{};
  (o.regions||[]).forEach(function(r){E('rect',{x:r.x,y:r.y,width:r.w,height:r.h,'class':'region'},svg);if(r.t)T(svg,r.x+10,r.y+18,r.t,'rlab');});
  function anc(s){if(Array.isArray(s))return s;var mm=/^(\w+)\.([lrtb])(?:@([\d.]+))?$/.exec(s),n=N[mm[1]],f=mm[3]!==undefined?+mm[3]:0.5;
    if(mm[2]==='l')return [n.x,n.y+n.h*f];if(mm[2]==='r')return [n.x+n.w,n.y+n.h*f];if(mm[2]==='t')return [n.x+n.w*f,n.y];return [n.x+n.w*f,n.y+n.h];}
  var CLS={pipe:'e-pipe',info:'e-info',bal:'e-bal',rein:'e-rein',delay:'e-delay',ink:'e-ink',risk:'e-risk',empty:'e-empty',good:'e-good'};
  var MK={pipe:'ah-flow',info:'ah-info',bal:'ah-bal',rein:'ah-rein',delay:'ah-delay',ink:'ah-ink',risk:'ah-risk',empty:'ah-info',good:'ah-bal'};
  var eg=E('g',{},svg),labs=[];
  (o.edges||[]).forEach(function(e){var k=e.kind||'ink',pts=[anc(e.a)].concat(e.via||[],[anc(e.b)]);
    E('path',{d:'M'+pts.map(function(p){return p[0]+','+p[1];}).join(' L'),'class':CLS[k],'marker-end':e.noarrow?null:'url(#'+MK[k]+')'},eg);
    if(e.label)labs.push([e.lp||midpt(pts),e.label,e.lk,e.anchor]);});
  (o.valves||[]).forEach(function(v){var x=v[0],y=v[1],d=v[2]==='v'?'M'+(x-8)+','+(y-8)+' L'+(x+8)+','+(y-8)+' L'+(x-8)+','+(y+8)+' L'+(x+8)+','+(y+8)+' Z':'M'+(x-8)+','+(y-8)+' L'+(x+8)+','+(y+8)+' L'+(x+8)+','+(y-8)+' L'+(x-8)+','+(y+8)+' Z';E('path',{d:d,'class':'valve'},svg);});
  Object.keys(N).forEach(function(key){var n=N[key],g=E('g',{'class':'n n-'+(n.kind||'box')},svg);
    if(n.kind==='cloud'){var u=E('use',{href:'#cloud',x:n.x,y:n.y,width:n.w,height:n.h},g);u.setAttributeNS(XL,'xlink:href','#cloud');}
    else if(n.kind!=='text'){E('rect',{x:n.x,y:n.y,width:n.w,height:n.h,'class':'nb'},g);if(n.kind==='stock'||n.kind==='stockd')E('rect',{x:n.x+4,y:n.y+4,width:n.w-8,height:n.h-8,'class':'nb2'},g);}
    var L=[];if(n.k)L.push([n.k,'nk']);(n.t||[]).forEach(function(s,i){L.push([s,i===0?'nt':'ns']);});
    var lh=16,yy=n.y+n.h/2-(L.length-1)*lh/2+4;
    L.forEach(function(r,i){T(g,n.x+n.w/2,yy+i*lh,r[0],r[1],'middle');});});
  (o.delays||[]).forEach(function(d){var x=d[0],y=d[1];E('path',{d:d[2]==='v'?'M'+(x-8)+','+(y-3)+' H'+(x+8)+' M'+(x-8)+','+(y+3)+' H'+(x+8):'M'+(x-3)+','+(y-8)+' V'+(y+8)+' M'+(x+3)+','+(y-8)+' V'+(y+8),'class':'dmark'},svg);});
  (o.badges||[]).forEach(function(b){var g=E('g',{'class':'badge b-'+b.kind},svg);E('circle',{cx:b.x,cy:b.y,r:15},g);T(g,b.x,b.y+5,b.t,'bt','middle');});
  labs.forEach(function(l){lines(svg,l[0][0],l[0][1],l[1],'lab halo '+(l[2]||''),l[3]||'middle',13);});
  (o.texts||[]).forEach(function(t){lines(svg,t.x,t.y,t.t,t.c||'lab',t.a||'start',13);});
  host.appendChild(svg);
}

/* ───────── nav scroll-spy: marks the header link of the section in view ───────── */
function spy(){
  if(!('IntersectionObserver' in window))return;
  var links=[].slice.call(document.querySelectorAll('.tnav a[data-spy]'));
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(a){a.setAttribute('aria-current',a.getAttribute('data-spy')===e.target.id?'true':'false');});}});},{rootMargin:'-35% 0px -60% 0px'});
  links.forEach(function(a){var s=document.getElementById(a.getAttribute('data-spy'));if(s)io.observe(s);});
}

return {E:E,T:T,lines:lines,fn:fn,pth:pth,safe:safe,plot:plot,spark:spark,dg:dg,spy:spy};
})();
