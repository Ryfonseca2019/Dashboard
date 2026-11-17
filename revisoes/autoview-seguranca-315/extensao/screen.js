const profileId=Number(new URL(location.href).searchParams.get('profile'))||1;
async function render(){const s=(await chrome.storage.local.get('autoview')).autoview;const p=s?.profiles?.find(x=>x.id===profileId);const image=document.getElementById('art');if(p?.image&&p.image.startsWith('data:image/')){image.src=p.image;image.hidden=false;document.getElementById('title').hidden=true;document.getElementById('subtitle').hidden=true}else{image.hidden=true;document.getElementById('title').hidden=false;document.getElementById('subtitle').hidden=false;document.getElementById('title').textContent=p?.name||'Dashboard AutoView'}}
chrome.storage.onChanged.addListener(c=>{if(c.autoview)render()});render();

const control=document.getElementById('institutionalControl');
const panel=document.getElementById('institutionalPanel');
async function refreshControl(){const s=(await chrome.storage.local.get('autoview')).autoview;control.hidden=!(profileId===1&&s?.institutional&&s?.enabled);if(control.hidden)panel.hidden=true}
document.getElementById('openInstitutional').onclick=()=>panel.hidden=!panel.hidden;
document.getElementById('closeInstitutional').onclick=()=>panel.hidden=true;
document.getElementById('restoreInstitutional').onclick=async()=>{if(!confirm('Retomar os dashboards nos quatro monitores? Informações corporativas voltarão a ficar visíveis.'))return;const r=await chrome.runtime.sendMessage({type:'RESUME'});if(!r?.ok)document.getElementById('institutionalMessage').textContent=r?.error||'Não foi possível restaurar';};
chrome.storage.onChanged.addListener(c=>{if(c.autoview)refreshControl()});refreshControl();
