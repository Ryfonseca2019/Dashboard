'use strict';
// Central de seleção exibida somente na aba ativa da janela vinculada ao Monitor 1.
(() => {
  const ID='autoview31-selector-root';
  let root=null, shadow=null, lastSig='', lastHost=false, open=false, busy=false, notice='', introDone=false, requestSeq=0, loading=false, commandStarted=0;
  // Logs bounded to the console: no URLs, images or persistent configuration writes.
  const trace=(stage,start,detail={})=>console.debug('[AutoView perf]',stage,{ms:+(performance.now()-start).toFixed(2),...detail});
  const send=async payload=>{const start=performance.now();try{const response=await chrome.runtime.sendMessage(payload);if(!response?.ok)throw Error(response?.error||'Comando não concluído');return response}finally{trace('runtime:'+payload.type,start)}};
  const elt=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
  const css=`
:host{all:initial;color-scheme:light}*{box-sizing:border-box}
.av-fab-shell{position:fixed;right:18px;bottom:18px;z-index:2147483647;pointer-events:auto}
.av-fab{position:relative;display:grid;place-items:center;width:54px;height:54px;border:1px solid rgba(219,236,255,.57);border-radius:19px;background:linear-gradient(140deg,rgba(19,94,163,.88),rgba(13,45,91,.87));backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);color:#fff;box-shadow:0 8px 30px rgba(0,20,51,.38),inset 0 1px rgba(255,255,255,.24);cursor:pointer;opacity:.76;transition:opacity .22s,transform .22s,box-shadow .22s}
.av-fab svg{width:25px;height:25px;stroke:currentColor;stroke-width:1.85;fill:none;stroke-linecap:round;stroke-linejoin:round}
.av-fab:hover,.av-fab:focus-visible{opacity:1;transform:translateY(-2px) scale(1.05);box-shadow:0 12px 36px rgba(0,20,51,.52),0 0 0 3px rgba(113,205,255,.17)}
.av-fab:focus-visible{outline:3px solid #a5d9ff;outline-offset:3px}
.av-fab-shell.av-intro::before,.av-fab-shell.av-intro::after{content:'';position:absolute;inset:-6px;border:2px solid rgba(69,193,255,.8);border-radius:24px;pointer-events:none;animation:av-ripple 1.9s ease-out 3}
.av-fab-shell.av-intro::after{animation-delay:.65s}
@keyframes av-ripple{0%{transform:scale(.9);opacity:.9}100%{transform:scale(1.75);opacity:0}}
.av-hint{position:absolute;right:66px;top:50%;transform:translateY(-50%);white-space:nowrap;pointer-events:none;background:rgba(9,30,55,.91);border:1px solid rgba(166,219,255,.28);color:#f8fcff;padding:10px 13px;border-radius:12px;font:600 12px system-ui,Arial;box-shadow:0 8px 25px #071c3666;opacity:0;animation:av-hint 5s ease-in-out forwards}
@keyframes av-hint{0%,8%{opacity:0;transform:translate(8px,-50%)}18%,72%{opacity:1;transform:translate(0,-50%)}88%,100%{opacity:0;transform:translate(0,-50%)}}
.av-panel{position:fixed;z-index:2147483647;right:12px;top:12px;bottom:12px;width:min(384px,calc(100vw - 24px));background:rgba(245,249,255,.91);-webkit-backdrop-filter:blur(24px) saturate(145%);backdrop-filter:blur(24px) saturate(145%);border:1px solid rgba(255,255,255,.85);border-radius:23px;color:#14263f;box-shadow:0 18px 60px rgba(3,20,47,.4);display:flex;flex-direction:column;font:14px system-ui,Arial;line-height:1.4;overflow:hidden;pointer-events:auto;animation:av-slide .25s ease-out}
@keyframes av-slide{from{opacity:0;transform:translateX(18px)}to{opacity:1;transform:translateX(0)}}
.av-head{padding:20px 18px 15px;border-bottom:1px solid rgba(100,137,180,.16);display:flex;align-items:center;justify-content:space-between;background:linear-gradient(125deg,rgba(230,242,255,.75),rgba(255,255,255,.35))}
.av-title{font-weight:750;font-size:16px;letter-spacing:-.25px}.av-sub{font-size:12px;color:#59728c;margin-top:3px}.av-body{overflow:auto;flex:1;padding:16px}
.av-input{display:block;width:100%;background:rgba(255,255,255,.88);border:1px solid #c5d5e5;border-radius:13px;padding:12px;color:#10243c;font:inherit;margin-bottom:14px;outline:none;transition:box-shadow .15s,border-color .15s}.av-input:focus{border-color:#377ecd;box-shadow:0 0 0 3px rgba(60,138,216,.15)}
.av-card{width:100%;display:flex;gap:11px;align-items:center;text-align:left;padding:10px;margin-bottom:9px;border-radius:15px;border:1px solid rgba(153,180,209,.44);background:rgba(255,255,255,.71);color:#152842;cursor:pointer;font:inherit;transition:background .16s,transform .16s,box-shadow .16s}.av-card:hover,.av-card:focus-visible{border-color:#4288ce;background:#fff;transform:translateX(-2px);box-shadow:0 5px 15px #1e4b7820;outline:none}
.av-thumb{width:90px;height:53px;flex-shrink:0;border-radius:10px;object-fit:cover;background:linear-gradient(135deg,#173253,#286da4);color:#bad9ff;display:flex;align-items:center;justify-content:center;font-size:23px}.av-name{font-weight:650;font-size:12px}.av-meta{font-size:11px;color:#627c98;margin-top:4px}
.av-foot{padding:14px 16px;border-top:1px solid #dce5f1;background:rgba(255,255,255,.5);max-height:41vh;overflow:auto}.av-status{display:flex;align-items:center;gap:8px;font-size:12px;margin:7px 0}.av-status span{flex:1;min-width:0}.av-action{border:1px solid #cad9e8;border-radius:10px;background:rgba(227,240,253,.89);color:#173b62;padding:8px 10px;cursor:pointer;font:12px system-ui}.av-action:disabled{opacity:.5}.av-protect{width:100%;margin-top:12px;background:linear-gradient(120deg,#14345a,#235c93);color:#fff;border:0;border-radius:12px;padding:12px;cursor:pointer;font-weight:650}.av-notice{padding:10px;background:rgba(219,239,255,.85);color:#123f6d;border-radius:11px;font-size:12px;margin-bottom:10px}.av-close{display:grid;place-items:center;width:35px;height:35px;background:rgba(210,227,246,.55);border:1px solid rgba(140,172,203,.2);border-radius:11px;font-size:24px;color:#385875;cursor:pointer;line-height:1}.av-close:hover{background:#dcecff;color:#123e68}.av-loading{display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;min-height:200px;color:#536d89;text-align:center}.av-spinner{width:28px;height:28px;border:3px solid #c6dff3;border-top-color:#307fc6;border-radius:50%;animation:av-spin .8s linear infinite}@keyframes av-spin{to{transform:rotate(360deg)}}
@media(prefers-reduced-motion:reduce){.av-fab-shell.av-intro::before,.av-fab-shell.av-intro::after,.av-hint,.av-panel,.av-spinner{animation:none!important}.av-fab,.av-card{transition:none!important}}
`;
  function ensureRoot(){if(root)return;root=document.createElement('div');root.id=ID;root.style.cssText='position:fixed!important;top:0!important;left:0!important;width:100vw!important;height:100vh!important;z-index:2147483647!important;pointer-events:none!important;';shadow=root.attachShadow({mode:'closed'});const style=document.createElement('style');style.textContent=css;shadow.append(style);document.documentElement.append(root)}
  function remove(){if(root){root.remove();root=null;shadow=null;lastSig=''}}
  function makeButton(text,klass,click){const b=elt('button',klass,text);b.type='button';b.style.pointerEvents='auto';b.addEventListener('click',click);return b}
  // O fechamento é exclusivamente local; respostas antigas não podem reabrir o painel.
  function closeLocally(){
    const start=performance.now();
    ++requestSeq;
    open=false; loading=false;
    render();
    trace('close:dom',start);
    requestAnimationFrame(()=>trace('close:frame',start));
    void send({type:'SELECTOR_OPEN',open:false}).catch(e=>console.warn('AutoView: estado do seletor',e));
  }
  function setSelectorOpen(value){
    if(!value){ closeLocally(); return; }
    const start=performance.now();
    ++requestSeq;
    open=true;loading=true;
    render();trace('open:dom',start); // exibir o painel e o estado de carregamento imediatamente
    void send({type:'SELECTOR_OPEN',open:true}).catch(e=>console.warn('AutoView: falha ao sincronizar abertura',e));
    void refresh(true); // consultar apenas uma vez ao abrir, sem atualizar DOM a cada tick
  }
  async function action(payload,message){
    if(busy)return;
    busy=true;notice='Executando comando…';render();
    try{
      const r=await send(payload);
      notice=r.message||message||'Comando realizado';
    }catch(e){notice='Erro: '+e.message}
    finally{busy=false;}
    // Atualizar dados, sem substituir a decisão local de abrir/fechar.
    void refresh(true);
  }
  function chooseDashboard(profileId,itemId){
    if(busy||loading)return;
    const clicked=performance.now();trace('select:click',clicked);
    commandStarted=performance.now();
    closeLocally(); // sem await, antes de qualquer chamada ao navegador
    busy=true;
    void send({type:'SELECT_DASHBOARD',profileId,itemId}).then(r=>{
      notice=r.message||'Dashboard selecionado';
      console.info('AutoView: seleção concluída em',Math.round(performance.now()-commandStarted),'ms');
    }).catch(e=>{
      notice='Erro ao selecionar dashboard: '+e.message;
      console.warn('AutoView: falha na seleção',e);
      // Não reabrir automaticamente: devolver o controle ao operador.
    }).finally(()=>{busy=false;if(open)void refresh(true)});
  }
  let current=null;
  function render(){const start=performance.now();if(!current?.host||current.institutional){remove();return}ensureRoot();// ShadowRoot has no element :scope. Iterate direct children instead.
    for(const child of [...shadow.children])if(child.tagName!=='STYLE')child.remove();
    const shell=elt('div','av-fab-shell'+(!introDone?' av-intro':''));
    const fab=makeButton('','av-fab',()=>setSelectorOpen(!open));
    fab.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>';
    fab.title='Abrir Central de Seleção';fab.setAttribute('aria-label','Abrir Central de Seleção');
    shell.append(fab);
    if(!introDone){shell.append(elt('span','av-hint','Clique aqui para escolher um painel'));introDone=true}
    shadow.append(shell);
    if(!open)return;
    const panel=elt('aside','av-panel');panel.style.pointerEvents='auto';panel.setAttribute('aria-label','Central de Seleção');const header=elt('div','av-head');const title=elt('div');title.append(elt('div','av-title','Central de Seleção'),elt('div','av-sub','Monitor 1 • Quatro apresentações'));header.append(title,makeButton('×','av-close',()=>setSelectorOpen(false)));panel.append(header);
    const body=elt('div','av-body');if(loading){const loader=elt('div','av-loading');loader.append(elt('div','av-spinner'),elt('div','', 'Preparando central...'),elt('div','av-sub','Aguarde a lista de dashboards ficar disponível.'));body.append(loader);panel.append(body);shadow.append(panel);trace('render:loading',start);return;}const search=elt('input','av-input');search.type='search';search.placeholder='Pesquisar em todos os monitores';search.setAttribute('aria-label','Pesquisar dashboards');search.value=render.query||'';body.append(search);
    const results=elt('div');body.append(results);panel.append(body);
    const profiles=current.profiles||[];
    function showResults(){render.query=search.value;results.replaceChildren();const query=search.value.trim().toLocaleLowerCase('pt-BR');let count=0;for(const p of profiles){for(const item of p.items||[]){if(!(item.name+' '+p.name).toLocaleLowerCase('pt-BR').includes(query))continue;count++;const button=makeButton('','av-card',()=>chooseDashboard(p.id,item.id));const thumb=item.thumbnail?.startsWith('data:image/')?elt('img','av-thumb'):elt('div','av-thumb','▥');if(thumb.tagName==='IMG'){thumb.src=item.thumbnail;thumb.alt='Miniatura de '+item.name}const info=elt('div');info.append(elt('div','av-name',item.name),elt('div','av-meta',`${p.name} · Monitor ${p.id}`));button.append(thumb,info);results.append(button)}}if(!count)results.append(elt('div','av-sub','Nenhum dashboard encontrado.'))}
    search.addEventListener('input',showResults);showResults();
    const footer=elt('div','av-foot');if(notice)footer.append(elt('div','av-notice',notice));footer.append(elt('div','av-title','Controle das apresentações'));
    for(const p of profiles){const row=elt('div','av-status');row.append(elt('span','',`Tela ${p.id}: ${p.maintenance?'Manutenção':p.paused?'Pausada':'Rotação automática'}`));if(p.paused&&!p.maintenance){row.append(makeButton('Retomar','av-action',()=>action({type:'RESUME_PROFILE',profileId:p.id},`Monitor ${p.id} retomado`)))}footer.append(row)}
    footer.append(makeButton('Retomar todas as rotações','av-action',()=>action({type:'RESUME_ALL_PROFILES'},'Rotações retomadas')));
    footer.append(makeButton('Ativar Modo Institucional','av-protect',()=>action({type:'INSTITUTIONAL'},'Modo Institucional ativado')));
    panel.append(footer);shadow.append(panel);
    if(busy)panel.querySelectorAll('.av-action,.av-protect,.av-card').forEach(b=>b.disabled=true);
    trace('render:ready',start);
  }
  async function refresh(force=false){
    if(!document.documentElement)return;
    // Nunca reconstruir um painel já pronto por causa do polling ou de eventos de storage.
    if(open&&!loading&&!force)return;
    const seq=++requestSeq;
    try{
      const r=await send({type:'HOST_STATUS',includeThumbnails:open});
      if(seq!==requestSeq)return;
      lastHost=r.host;
      if(!r.host||r.institutional){current=r;open=false;loading=false;remove();return;}
      current=r;
      if(open){loading=false;render();return;}
      if(!root)render();
    }catch(e){
      if(seq!==requestSeq)return;
      if(open){loading=false;notice='Falha ao carregar: '+e.message;render();}
      else console.warn('AutoView: falha ao consultar estado',e);
    }
  }
  chrome.storage.onChanged.addListener(changes=>{
    if(!changes.autoview)return;
    // A privacidade deve derrubar o seletor imediatamente; demais mudanças não mexem no menu aberto.
    if(changes.autoview.newValue?.institutional){++requestSeq;open=false;loading=false;current={host:false,institutional:true};remove();return;}
    if(!open&&!busy)void refresh(false);
  });
  // O painel aberto é estável. Atualizações automáticas não substituem botões durante um clique.
  setInterval(()=>{if(!open&&!busy&&document.visibilityState==='visible')void refresh(false)},30000);
  refresh(false);
})();
