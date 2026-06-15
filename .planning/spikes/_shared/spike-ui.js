/* Shared render helpers for spike mockups. Reads window.SPIKE_DATA. */
(function(){
  const SD = window.SPIKE_DATA;
  const fmt = n => n==null ? '—' : n.toLocaleString('es-CL');
  const ranked = SD.comunas.filter(c=>c.rate!=null && !c.lowPop).sort((a,b)=>a.rate-b.rate);
  const safest = n => ranked.slice(0,n);
  const highest = n => ranked.slice(-n).reverse();
  const byName = [...SD.comunas].sort((a,b)=>a.name.localeCompare(b.name,'es'));
  const regions = SD.regions.slice().sort((a,b)=>a.name.localeCompare(b.name,'es'));
  function search(q){
    q=(q||'').trim().toLowerCase();
    if(!q) return [];
    return byName.filter(c=>c.name.toLowerCase().includes(q)).slice(0,8);
  }
  function lvlDot(l){return `<span class="lvl lvl${l||1}" title="nivel ${l}"></span>`;}
  // demo link (no real page) — shows the IA intent
  function comunaHref(c){return `../003-comuna-page-spokes/comuna-page.html#${c.slug}`;}
  function rankRow(c,i){
    return `<tr><td class="num muted">${c.rank||i+1}</td><td><a href="${comunaHref(c)}">${c.name}</a> <span class="muted" style="font-size:12px">· ${c.region}</span></td><td class="num">${lvlDot(c.level)} ${fmt(c.rate)}</td></tr>`;
  }
  window.SPIKEUI = {SD,fmt,ranked,safest,highest,byName,regions,search,lvlDot,comunaHref,rankRow,
    rankTable(list,headRate){
      return `<table><thead><tr><th class="num">#</th><th>Comuna</th><th class="num">${headRate||'Tasa /100k'}</th></tr></thead><tbody>${list.map(rankRow).join('')}</tbody></table>`;
    },
    header(active, variantLabel){
      const items=[['Mapa','#'],['Comunas','../002-comuna-finder/finder.html'],['Rankings','#'],['Regiones','#'],['Noticias','#'],['Metodología','#']];
      return `<div class="spike-banner">SPIKE 001 · prototipo de arquitectura de información — <b>${variantLabel}</b> · datos CEAD ${SD.year} reales · enlaces ilustrativos</div>
      <header class="site"><div class="wrap"><div class="row">
        <span class="logo"><span class="dot"></span>Is Chile Safe</span>
        <nav class="main">${items.map(([t,h])=>`<a href="${h}" ${t===active?'style=\"color:var(--primary)\"':''}>${t}</a>`).join('')}</nav>
        <span class="lang">ES · <a href="#" style="color:var(--muted)">EN</a></span>
      </div></div></header>`;
    }
  };
})();
