'use strict';
const BASE={version:3,institutional:false,selectorOpen:false,enabled:false,maintenanceAll:false,profiles:Array.from({length:4},(_,i)=>({id:i+1,name:`Monitor ${i+1}`,displayIndex:i,showSeconds:30,refreshSeconds:3600,maintenance:false,paused:false,items:[],image:'',windowId:null,screenTabId:null,activeIndex:0,lastSwitch:0,issue:'',activeSince:0})),refreshJob:null,events:[]};
const safeUrl=u=>{try{const x=new URL(u);return ['http:','https:'].includes(x.protocol)?x.href:null;}catch{return null}};
let busy=false;
// A single writer for each read/modify/write transaction, including browser events.
// Rejections do not poison subsequent commands. Read-only status bypasses the queue.
let transaction=Promise.resolve();
function serialize(label,task){
  const queued=performance.now();
  const result=transaction.then(async()=>{
    const start=performance.now();
    console.debug('[AutoView perf]',label,{queueMs:+(start-queued).toFixed(2)});
    try{return await task()}finally{console.debug('[AutoView perf]',label,{executionMs:+(performance.now()-start).toFixed(2)})}
  });
  transaction=result.catch(()=>{});
  return result;
}
async function measured(stage,task){const start=performance.now();try{return await task()}finally{console.debug('[AutoView perf]',stage,{ms:+(performance.now()-start).toFixed(2)})}}
async function read(){return (await measured('storage:read',()=>chrome.storage.local.get('autoview'))).autoview||structuredClone(BASE)}
async function write(s){const start=performance.now();await chrome.storage.local.set({autoview:s});console.debug('[AutoView perf] storage:write',{ms:+(performance.now()-start).toFixed(2)})}
const log=(s,msg)=>{s.events=[{at:Date.now(),message:msg},...(s.events||[])].slice(0,120)};
async function displays(){const ds=await chrome.system.display.getInfo();return ds.filter(d=>d.isEnabled!==false&&d.bounds).sort((a,b)=>a.bounds.left-b.bounds.left||a.bounds.top-b.bounds.top)}
async function validWindow(id){if(!Number.isInteger(id))return false;try{await chrome.windows.get(id);return true}catch{return false}}
const recoveringProfiles=new Set();
function screenProfile(tab){
  const base=chrome.runtime.getURL('screen.html');
  for(const value of [tab.url,tab.pendingUrl]){try{const u=new URL(value);if(u.protocol+'//'+u.host+u.pathname===base)return Number(u.searchParams.get('profile'))}catch{}}
  return null;
}
async function ensureWindow(s,p){
  // Browser IDs may change after session restore. The institutional tab is the profile marker.
  const all=await chrome.windows.getAll({populate:true,windowTypes:['normal']});
  const claimed=new Set(s.profiles.filter(x=>x.id!==p.id).map(x=>x.windowId).filter(Number.isInteger));
  const hasOtherMarker=w=>(w.tabs||[]).some(t=>screenProfile(t)!==null&&screenProfile(t)!==p.id);
  const marked=all.filter(w=>!hasOtherMarker(w)&&(w.tabs||[]).some(t=>screenProfile(t)===p.id));
  if(all.some(w=>hasOtherMarker(w)&&(w.tabs||[]).some(t=>screenProfile(t)===p.id))){p.issue='Marcadores de perfis diferentes na mesma janela; criação suspensa para evitar duplicação';return null}
  const stored=all.find(w=>w.id===p.windowId&&!hasOtherMarker(w));
  const storedOwned=stored&&((stored.tabs||[]).some(t=>screenProfile(t)===p.id)||
    (!claimed.has(stored.id)&&(stored.tabs||[]).some(t=>p.items.some(item=>item.tabId===t.id&&[t.url,t.pendingUrl].some(u=>safeUrl(u)===safeUrl(item.url))))));
  const found=(storedOwned?stored:null)||marked[0];
  if(found){
    if(found.id!==p.windowId){recoveringProfiles.add(p.id);p.recoveringTabs=true;log(s,`Janela existente recuperada para o Monitor ${p.id}`)}
    p.windowId=found.id;p.screenTabId=(found.tabs||[]).find(t=>screenProfile(t)===p.id)?.id||null;
    if(marked.length>1)p.issue='Há outras janelas deste perfil; nenhuma janela adicional foi criada';
    return found.id;
  }
  if(stored){p.issue='Janela cadastrada existente sem identificação segura; criação suspensa para evitar duplicação';return null}
  if(Date.now()<(s.startupRecoveryUntil||0)){p.issue='Aguardando restauração das janelas do Edge';return null}
  const ds=await displays(),d=ds[p.displayIndex];if(!d){p.issue='Monitor de destino não encontrado';return null}
  const b=d.workArea||d.bounds;
  const w=await chrome.windows.create({url:chrome.runtime.getURL('screen.html?profile='+p.id),type:'normal',focused:false,left:b.left,top:b.top,width:Math.max(450,b.width),height:Math.max(350,b.height),state:'normal'});
  p.windowId=w.id;p.screenTabId=w.tabs?.[0]?.id||null;p.lastSwitch=Date.now();p.activeSince=p.lastSwitch;p.issue='';recoveringProfiles.delete(p.id);p.recoveringTabs=false;
  // Commit the window binding before opening any dashboards.
  await write(s);
  try{await chrome.windows.update(w.id,{state:'fullscreen'})}catch(e){p.issue='Tela cheia não aplicada: '+e.message}
  log(s,`Janela do perfil ${p.id} aberta`);return w.id;
}
async function getTabs(p){if(!await validWindow(p.windowId))return [];return chrome.tabs.query({windowId:p.windowId})}
async function ensureScreen(p){let ts=await getTabs(p);const u=chrome.runtime.getURL('screen.html');let screen=ts.find(t=>screenProfile(t)===p.id);if(!screen){screen=await chrome.tabs.create({windowId:p.windowId,url:u+'?profile='+p.id,active:false})}p.screenTabId=screen.id;return screen.id}
async function showScreen(p){if(!await validWindow(p.windowId))return;try{const id=await ensureScreen(p);await chrome.tabs.update(id,{active:true})}catch{}}
async function ensureDashboardTabs(p,onlyItemId=null){
  let tabs=await getTabs(p);
  const configured=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));
  if(p.recoveringTabs)recoveringProfiles.add(p.id);
  const claimed=new Set();
  const matches=(tab,item)=>[tab.url,tab.pendingUrl].some(u=>safeUrl(u)===safeUrl(item.url));
  // Two passes preserve valid bindings first; no tab is claimed by two items.
  for(const item of configured){
    const tab=tabs.find(t=>t.id===item.tabId&&!claimed.has(t.id)&&screenProfile(t)===null&&!configured.some(other=>other!==item&&matches(t,other)&&!matches(t,item)));
    if(tab)claimed.add(tab.id);else delete item.tabId;
  }
  for(const item of configured){
    if(Number.isInteger(item.tabId))continue;
    const tab=tabs.find(t=>!claimed.has(t.id)&&matches(t,item));
    if(tab){item.tabId=tab.id;claimed.add(tab.id)}
  }
  const unresolvedExisting=()=>tabs.some(t=>!claimed.has(t.id)&&screenProfile(t)===null&&
    ([t.url,t.pendingUrl].some(u=>!!safeUrl(u))||!t.url||t.url==='about:blank'));
  for(const item of configured){
    if(Number.isInteger(item.tabId)||(onlyItemId!==null&&item.id!==onlyItemId))continue;
    // Recheck the live browser immediately before creating: pending/restored tabs may just have appeared.
    tabs=await getTabs(p);
    const existing=tabs.find(t=>!claimed.has(t.id)&&matches(t,item));
    if(existing){item.tabId=existing.id;claimed.add(existing.id);continue}
    const loginPending=tabs.some(t=>[t.url,t.pendingUrl].some(value=>{try{const u=new URL(value);return ['login.microsoftonline.com','login.windows.net','login.live.com'].includes(u.hostname)||u.hostname==='app.powerbi.com'&&/\/(signin|login)(\/|$)/i.test(u.pathname)}catch{return false}}));
    if((recoveringProfiles.has(p.id)&&unresolvedExisting())||loginPending){
      p.issue='Abas restauradas ainda sem vínculo. Conclua o login e use Verificar abas e janelas; novas abas foram suspensas';
      continue;
    }
    const tab=await measured('tabs:create',()=>chrome.tabs.create({windowId:p.windowId,url:item.url,active:false}));
    item.tabId=tab.id;claimed.add(tab.id);tabs.push(tab);
  }
  if(configured.every(item=>Number.isInteger(item.tabId))){recoveringProfiles.delete(p.id);p.recoveringTabs=false}
  return configured;
}
async function showDashboard(s,p,idx){const list=await ensureDashboardTabs(p);if(!list.length){await showScreen(p);return}const i=((idx%list.length)+list.length)%list.length;if(!Number.isInteger(list[i].tabId))return;p.activeIndex=i;try{await chrome.tabs.update(list[i].tabId,{active:true});p.lastSwitch=Date.now();p.activeSince=Date.now()}catch(e){p.issue=e.message}}
// Seleção prioritária: ativar a aba cadastrada sem percorrer/criar todos os dashboards.
async function showDashboardFast(p,idx){
  const list=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));
  if(!list.length)throw Error('O perfil não possui dashboards ativos');
  const i=((idx%list.length)+list.length)%list.length,item=list[i];let tab=null;
  if(Number.isInteger(item.tabId)){
    try{const candidate=await measured('tabs:get',()=>chrome.tabs.get(item.tabId));if(candidate.windowId===p.windowId&&screenProfile(candidate)===null)tab=candidate}catch{}
  }
  if(!tab){await ensureDashboardTabs(p,item.id);if(!Number.isInteger(item.tabId))throw Error(p.issue||'Dashboard ainda sem vínculo');tab={id:item.tabId}}
  await measured('tabs:activate',()=>chrome.tabs.update(tab.id,{active:true}));
  item.tabId=tab.id;p.activeIndex=i;p.lastSwitch=Date.now();p.activeSince=p.lastSwitch;
}
async function launch(){if(busy)return;busy=true;try{const s=await read();if(!s.enabled)return;const ds=await displays();if(ds.length<4){log(s,`Detectados somente ${ds.length} monitores; confira o Windows`)}for(const p of s.profiles){if(p.maintenance||s.maintenanceAll)continue;if(!await ensureWindow(s,p))continue;if(s.institutional){await showScreen(p)}else if(!p.paused){await showScreen(p);await showDashboard(s,p,p.activeIndex||0)} }await write(s)}finally{busy=false}}
async function reconcile(){if(busy)return;busy=true;try{const s=await read();if(!s.enabled)return;for(const p of s.profiles){if(s.maintenanceAll||p.maintenance)continue;if(!await validWindow(p.windowId)){if(!await ensureWindow(s,p))continue;if(s.institutional){await showScreen(p)}else{await showScreen(p);await showDashboard(s,p,p.activeIndex||0)}continue}if(s.institutional){await showScreen(p);continue}if(p.paused||(p.id===1&&s.selectorOpen))continue;const list=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));if(!list.length)continue;const interval=Math.max(30,(list[p.activeIndex]?.showSeconds||p.showSeconds||30))*1000;if(Date.now()-(p.lastSwitch||0)>=interval){await showDashboard(s,p,(p.activeIndex+1)%list.length)}}await scheduleRefresh(s);await write(s)}finally{busy=false}}
async function scheduleRefresh(s){if(s.institutional||s.maintenanceAll||s.refreshJob)return;const now=Date.now();for(const p of s.profiles){if(p.maintenance||p.paused||!await validWindow(p.windowId))continue;const list=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));for(const item of list){if(!Number.isInteger(item.tabId))continue;const ms=Math.max(30,(item.refreshSeconds||p.refreshSeconds||3600))*1000;if(now-(item.lastRefresh||now)>=ms){const tabs=await getTabs(p);const active=tabs.find(t=>t.active)?.id;if(active===item.tabId&&(list.length>1||(p.id===1&&s.selectorOpen)))continue;try{if(active===item.tabId)await showScreen(p);s.refreshJob={profileId:p.id,itemId:item.id,tabId:item.tabId,started:now,returnToDashboard:active===item.tabId};await chrome.tabs.reload(item.tabId);log(s,`Atualização iniciada: ${item.name}`);return}catch(e){item.issue=e.message;s.refreshJob=null}}}}}
async function checkRefresh(){const s=await read();const j=s.refreshJob;if(!j)return;if(Date.now()-j.started>110000){const p=s.profiles.find(p=>p.id===j.profileId),item=p?.items.find(x=>x.id===j.itemId);if(item){item.issue='Tempo limite de carregamento';item.lastRefresh=Date.now()}s.refreshJob=null;log(s,'Timeout de atualização');await write(s)}}
chrome.tabs.onUpdated.addListener((tabId,change)=>serialize('tabs:updated',async()=>{if(change.status!=='complete')return;const s=await read(),j=s.refreshJob;if(!j||j.tabId!==tabId)return;const p=s.profiles.find(x=>x.id===j.profileId),item=p?.items.find(x=>x.id===j.itemId);if(!p||!item)return;item.lastRefresh=Date.now();item.issue='';s.refreshJob=null;await write(s);if(j.returnToDashboard){await chrome.alarms.create('return:'+p.id+':'+item.id,{when:Date.now()+10000})}}).catch(console.error));
chrome.alarms.onAlarm.addListener(a=>serialize('alarm:'+a.name,async()=>{try{if(a.name==='restore-windows'){await launch()}else if(a.name==='tick'){await reconcile();await checkRefresh()}else if(a.name.startsWith('return:')){const [,pid,iid]=a.name.split(':');const s=await read(),p=s.profiles.find(x=>x.id===Number(pid));if(!p||!s.enabled||s.institutional||p.maintenance||p.paused||(p.id===1&&s.selectorOpen))return;const item=p.items.find(x=>x.id===iid);if(!item)return;const list=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));const ix=list.findIndex(x=>x.id===iid);if(ix>=0&&await validWindow(p.windowId)){await showDashboard(s,p,ix);await write(s)}}}catch(e){console.error(e)}}).catch(console.error));
chrome.windows.onRemoved.addListener(id=>serialize('window:removed',async()=>{const s=await read(),p=s.profiles.find(x=>x.windowId===id);if(!p)return;p.windowId=null;p.screenTabId=null;log(s,`Janela do monitor ${p.id} fechada`);await write(s);if(s.enabled&&!s.maintenanceAll&&!p.maintenance)await chrome.alarms.create('tick',{periodInMinutes:.5,delayInMinutes:.5})}).catch(console.error));

const MESSAGE_PAGES={
  'options.html':new Set(['GET','TAB_DIAGNOSTICS','SAVE','START','STOP','PAUSE','MAINTENANCE','REFRESH','OPEN_OPTIONS','INSTITUTIONAL','RESUME','RESUME_PROFILE','RESUME_ALL_PROFILES']),
  'popup.html':new Set(['GET','OPEN_OPTIONS','INSTITUTIONAL','RESUME']),
  'screen.html':new Set(['RESUME'])
};
const SELECTOR_MESSAGES=new Set(['HOST_STATUS','SELECTOR_OPEN','SELECT_DASHBOARD','RESUME_PROFILE','RESUME_ALL_PROFILES','INSTITUTIONAL']);
function assertMessageSource(req,sender,s){
  if(!req||typeof req!=='object'||typeof req.type!=='string'||sender?.id!==chrome.runtime.id)throw Error('Origem da mensagem não autorizada');
  const source=typeof sender.url==='string'?sender.url.split(/[?#]/,1)[0]:'';
  for(const [page,types] of Object.entries(MESSAGE_PAGES)){
    if(source===chrome.runtime.getURL(page)){
      if(!types.has(req.type))throw Error('Operação não permitida nesta página');
      return;
    }
  }
  if(sender.frameId!==0||!sender.tab||!/^https?:\/\//i.test(source)||!SELECTOR_MESSAGES.has(req.type))throw Error('Comando permitido apenas no controle da extensão');
  if(req.type!=='HOST_STATUS'&&(!s.enabled||sender.tab.windowId!==s.profiles[0]?.windowId))throw Error('Comando permitido apenas na janela vinculada ao Monitor 1');
}
function validStoredImage(value){
  return value===undefined||value===null||value===''||
    typeof value==='string'&&value.length<=10485760&&/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$/i.test(value)&&value.slice(value.indexOf(',')+1).length%4===0;
}
function assertConfigurationInput(value){
  if(!value||typeof value!=='object'||!Array.isArray(value.profiles)||value.profiles.length!==4)throw Error('Configuração inválida');
  const profiles=new Set();
  for(const p of value.profiles){
    if(!p||!Number.isInteger(p.id)||p.id<1||p.id>4||profiles.has(p.id)||typeof p.name!=='string'||!Number.isInteger(p.displayIndex)||p.displayIndex<0||!Array.isArray(p.items))throw Error('Perfis inválidos ou repetidos');
    profiles.add(p.id);
    if(!validStoredImage(p.image))throw Error('Imagem institucional inválida: use PNG, JPEG ou WebP local');
    for(const k of ['showSeconds','refreshSeconds'])if(typeof p[k]!=='number'||!Number.isFinite(p[k])||p[k]<30)throw Error('Intervalo inválido no perfil');
    const ids=new Set();
    for(const item of p.items){
      const validId=typeof item?.id==='string'&&item.id.length>0||Number.isInteger(item?.id);
      if(!validId||ids.has(item.id)||typeof item.name!=='string'||typeof item.url!=='string'||!safeUrl(item.url)||/^https?:\/\/[^/?#]*@/i.test(safeUrl(item.url)||''))throw Error('Dashboard inválido, repetido ou URL não permitida');
      ids.add(item.id);
      if(!validStoredImage(item.thumbnail))throw Error('Miniatura inválida: use PNG, JPEG ou WebP local');
      for(const k of ['showSeconds','refreshSeconds'])if(item[k]!==null&&item[k]!==undefined&&item[k]!==0&&(typeof item[k]!=='number'||!Number.isFinite(item[k])||item[k]<30))throw Error('Intervalo inválido no dashboard');
    }
  }
}

chrome.runtime.onMessage.addListener((req,sender,respond)=>{const handle=async()=>{let s=await read();assertMessageSource(req,sender,s);switch(req.type){case 'GET':respond({ok:true,state:s,displays:await displays()});return;
case 'TAB_DIAGNOSTICS':respond({ok:true,diagnostic:await tabDiagnostics(s)});return;
case 'HOST_STATUS':{const t=sender.tab;const host=!!(t&&s.enabled&&s.profiles[0]?.windowId===t.windowId);respond({ok:true,host,institutional:!!s.institutional,open:!!s.selectorOpen,profiles:host&&!s.institutional?s.profiles.map(p=>({id:p.id,name:p.name,paused:!!p.paused,maintenance:!!p.maintenance,available:!!p.windowId,items:p.items.filter(x=>x.enabled!==false&&safeUrl(x.url)).map(x=>({id:x.id,name:x.name,thumbnail:req.includeThumbnails?(x.thumbnail||null):null}))})):[]});return}
case 'SELECT_DASHBOARD':{if(s.institutional)throw Error('Modo Institucional ativo');if(!sender.tab||sender.tab.windowId!==s.profiles[0].windowId)throw Error('Comando permitido apenas no Monitor 1');const p=s.profiles.find(x=>x.id===Number(req.profileId));if(!s.enabled||!p||p.maintenance||s.maintenanceAll)throw Error('Monitor indisponível ou em manutenção');if(!await validWindow(p.windowId))throw Error('Janela do monitor indisponível');const list=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));const idx=list.findIndex(x=>x.id===req.itemId);if(idx<0)throw Error('Dashboard não encontrado');p.paused=true;s.selectorOpen=false;
// Persistir a pausa antes de ativar a aba: o ciclo de rotação não deve competir com o clique.
await write(s);
try{await showDashboardFast(p,idx)}catch(e){p.issue='Falha na seleção: '+e.message;await write(s);throw e}
log(s,`Seleção manual no Monitor ${p.id}: ${list[idx].name}`);
await write(s);respond({ok:true,message:`${list[idx].name} exibido no Monitor ${p.id}; rotação pausada`});return}
case 'SELECTOR_OPEN':{if(!sender.tab||sender.tab.windowId!==s.profiles[0].windowId)throw Error('Central disponível apenas no Monitor 1');if(s.institutional)throw Error('Controle institucional disponível na tela protegida');s.selectorOpen=!!req.open;await write(s);respond({ok:true});return}
case 'RESUME_PROFILE':{if(s.institutional)throw Error('Modo Institucional ativo');const p=s.profiles.find(x=>x.id===Number(req.profileId));if(!p)throw Error('Monitor inválido');p.paused=false;p.lastSwitch=Date.now();log(s,`Rotação retomada no Monitor ${p.id}`);await write(s);respond({ok:true});return}
case 'RESUME_ALL_PROFILES':{if(s.institutional)throw Error('Modo Institucional ativo');for(const p of s.profiles){p.paused=false;p.lastSwitch=Date.now()}log(s,'Rotações retomadas pelo operador');await write(s);respond({ok:true});return}

case 'SAVE':{
  assertConfigurationInput(req.state);
  const proposed=structuredClone(req.state);
  if(!proposed||!Array.isArray(proposed.profiles)||proposed.profiles.length!==4)throw Error('Configuração inválida');
  const importing=req.importing===true;
  for(const p of proposed.profiles){
    const live=s.profiles.find(x=>x.id===p.id);
    p.items=(p.items||[]).filter(x=>safeUrl(x.url)).map(x=>{
      const item={...x,url:safeUrl(x.url)},old=live?.items.find(y=>y.id===x.id&&safeUrl(y.url)===item.url);
      if(!importing&&old){for(const k of ['tabId','lastRefresh','issue']){if(old[k]===undefined)delete item[k];else item[k]=old[k]}}
      else{delete item.tabId;item.lastRefresh=item.lastRefresh||Date.now()}
      return item;
    });
    p.showSeconds=Math.max(30,Number(p.showSeconds)||30);p.refreshSeconds=Math.max(30,Number(p.refreshSeconds)||3600);
    if(!importing&&live)for(const k of ['windowId','screenTabId','activeIndex','lastSwitch','activeSince','paused','maintenance','issue','recoveringTabs'])p[k]=live[k];
    if(importing){p.windowId=null;p.screenTabId=null;p.recoveringTabs=false}
  }
  if(!importing)for(const k of ['enabled','institutional','selectorOpen','maintenanceAll','refreshJob','startupRecoveryUntil'])proposed[k]=s[k];
  else{proposed.enabled=false;proposed.institutional=true;proposed.selectorOpen=false;proposed.refreshJob=null;proposed.startupRecoveryUntil=0}
  proposed.events=s.events;await write(proposed);respond({ok:true});return;
}
case 'START':s.startupRecoveryUntil=0;s.enabled=true;await write(s);await launch();respond({ok:true});return;
case 'STOP':s.enabled=false;await write(s);respond({ok:true});return;
case 'INSTITUTIONAL':if(sender.tab&&sender.tab.windowId!==s.profiles[0].windowId)throw Error('Controle disponível apenas no Monitor 1');s.institutional=true;s.selectorOpen=false;log(s,'Modo institucional ativado');await write(s);for(const p of s.profiles)await showScreen(p);respond({ok:true});return;
case 'RESUME':if(sender.tab&&sender.tab.windowId!==s.profiles[0].windowId)throw Error('Controle disponível apenas no Monitor 1');s.institutional=false;s.selectorOpen=false;for(const p of s.profiles){p.paused=false;p.lastSwitch=Date.now()};log(s,'Modo institucional desativado');await write(s);for(const p of s.profiles){if(!p.maintenance&&!p.paused&&await validWindow(p.windowId)){await showDashboard(s,p,p.activeIndex||0)}}await write(s);respond({ok:true});return;
case 'PAUSE':{const p=s.profiles.find(x=>x.id===req.id);if(!p)throw Error('Perfil inválido');p.paused=!!req.paused;if(req.itemId){const idx=p.items.filter(x=>x.enabled!==false).findIndex(x=>x.id===req.itemId);if(idx>=0&&!s.institutional)await showDashboard(s,p,idx)}log(s,`Monitor ${p.id}: ${p.paused?'apresentador':'automático'}`);await write(s);respond({ok:true});return}
case 'MAINTENANCE':{const p=s.profiles.find(x=>x.id===req.id);if(!p)throw Error('Perfil inválido');p.maintenance=!!req.enabled;log(s,`Manutenção monitor ${p.id}: ${p.maintenance?'iniciada':'encerrada'}`);await write(s);if(!p.maintenance)await launch();respond({ok:true});return}
case 'REFRESH':{const p=s.profiles.find(x=>x.id===req.id),item=p?.items.find(x=>x.id===req.itemId);if(!item||!Number.isInteger(item.tabId)||s.institutional||p.paused||p.maintenance)throw Error('Atualização não autorizada neste estado');const t=(await getTabs(p)).find(x=>x.active);const hidden=t?.id===item.tabId;if(hidden)await showScreen(p);s.refreshJob={profileId:p.id,itemId:item.id,tabId:item.tabId,started:Date.now(),returnToDashboard:hidden};await write(s);await chrome.tabs.reload(item.tabId);respond({ok:true});return}
case 'OPEN_OPTIONS':await chrome.runtime.openOptionsPage();respond({ok:true});return;
default:throw Error('Comando desconhecido')}};
const job=['GET','HOST_STATUS','TAB_DIAGNOSTICS'].includes(req.type)?handle():serialize('message:'+req.type,handle);
job.catch(e=>respond({ok:false,error:e.message}));return true});
chrome.commands.onCommand.addListener(command=>serialize('command:'+command,async()=>{if(command==='open_control'){await chrome.runtime.openOptionsPage()}if(command==='institutional'){const s=await read();s.institutional=true;await write(s);for(const p of s.profiles)await showScreen(p)}}).catch(console.error));
// Read-only snapshot; intentionally excludes URLs, titles and images from the response.
async function tabDiagnostics(s){
  const windows=await chrome.windows.getAll({populate:true,windowTypes:['normal']});
  const screenURL=chrome.runtime.getURL('screen.html');
  function marker(tab){
    for(const value of [tab.url,tab.pendingUrl]){try{const u=new URL(value);if(u.protocol+'//'+u.host+u.pathname===screenURL)return Number(u.searchParams.get('profile'))}catch{}}
    return null;
  }
  const profiles=s.profiles.map(p=>{
    const items=p.items.filter(x=>x.enabled!==false&&safeUrl(x.url));
    const marked=windows.filter(w=>(w.tabs||[]).some(t=>marker(t)===p.id));
    const tracked=windows.find(w=>w.id===p.windowId);
    const candidates=[...marked];
    if(tracked&&!candidates.some(w=>w.id===tracked.id))candidates.push(tracked);
    const rows=candidates.map(w=>{
      const tabs=w.tabs||[],ids=new Set(items.map(x=>x.tabId).filter(Number.isInteger));
      const linked=tabs.filter(t=>ids.has(t.id));
      const screens=tabs.filter(t=>marker(t)===p.id);
      const exactMatches=new Map();
      for(const item of items){const key=safeUrl(item.url);if(!exactMatches.has(key))exactMatches.set(key,items.filter(x=>safeUrl(x.url)===key).length)}
      let exactExtra=0;
      for(const [url,expected] of exactMatches){const count=tabs.filter(t=>safeUrl(t.url)===url||safeUrl(t.pendingUrl)===url).length;exactExtra+=Math.max(0,count-expected)}
      return {tracked:w.id===p.windowId,marked:screens.length>0,totalTabs:tabs.length,institutionalTabs:screens.length,linkedDashboards:linked.length,
        unlinkedTabs:tabs.filter(t=>!ids.has(t.id)&&marker(t)!==p.id).length,
        excessComparedToConfiguration:Math.max(0,tabs.length-(items.length+1)),exactUrlExtraCandidates:exactExtra};
    });
    const trackedTabs=tracked?.tabs||[];
    return {profileId:p.id,configuredDashboards:items.length,referenceTabsPerWindow:items.length+1,markedWindows:marked.length,trackedWindowFound:!!tracked,
      missingDashboardLinks:items.filter(item=>!trackedTabs.some(t=>t.id===item.tabId)).length,recoveryPending:!!p.recoveringTabs,paused:!!p.paused,maintenance:!!p.maintenance,windows:rows};
  });
  return {generatedAt:new Date().toISOString(),automationEnabled:!!s.enabled,institutional:!!s.institutional,profiles};
}
async function initialize(restoring=false){
  const s=await read();
  for(const p of s.profiles){if(restoring){recoveringProfiles.add(p.id);p.recoveringTabs=true}p.items.forEach(x=>x.lastRefresh=x.lastRefresh||Date.now())}
  s.refreshJob=null;s.selectorOpen=false;
  // Keep operational bindings and pauses. Give browser session restore a grace period before creating windows.
  s.startupRecoveryUntil=restoring&&s.enabled?Date.now()+15000:0;
  await write(s);await chrome.alarms.create('tick',{periodInMinutes:.5});
  if(s.enabled){if(restoring)await chrome.alarms.create('restore-windows',{when:s.startupRecoveryUntil});await launch()}
}
chrome.runtime.onInstalled.addListener(details=>{serialize('installed',async()=>{const s=await read();if(details.reason==='install'){await initialize()}else{if(s.selectorOpen===undefined)s.selectorOpen=false;await write(s);await chrome.alarms.create('tick',{periodInMinutes:.5});if(s.enabled)await reconcile()}}).catch(console.error)});
chrome.runtime.onStartup.addListener(()=>{serialize('startup',()=>initialize(true)).catch(console.error)});
chrome.alarms.get('tick').then(a=>{if(!a)chrome.alarms.create('tick',{periodInMinutes:.5})});
