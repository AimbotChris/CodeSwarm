'use strict';
const $ = id => document.getElementById(id);
let data = null;
let renderedExpiryKey=null;
let requestGeneration=0,requestController=null;
function element(tag, text, cls) { const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e; }
function numeric(v, suffix) {return typeof v==='number'&&Number.isFinite(v)?Math.round(v)+suffix:'unknown';}
function render(){
  const current=expireSnapshot(data);renderedExpiryKey=expiryKey(data);
  const rows=(current?.devices||[]).filter(d=>(d.name+' '+d.hostname+' '+d.os).toLowerCase().includes($('filter').value.toLowerCase()));
  $('workers').replaceChildren(); $('empty').hidden=rows.length>0;
  $('empty-detail').textContent=$('filter').value?'No devices match this search.':!data||data.error?data?.setup_instructions||'Check that the local management service is running, then refresh.':'No peers were returned. Connect this computer to your tailnet, then refresh.';
  for(const d of rows){
    const card=element('article','','card');card.append(element('h2',d.name),element('p',d.hostname+' · '+d.os,'host'));
    const states=element('div','','states');
    for(const [label,value] of [['Transport',d.transport],['Desktop',d.desktop],['App',d.app],['Work / sign-in',d.worker]]){const e=element('div',value,'state');e.prepend(element('span',label));states.append(e);}
    card.append(states);
    if(d.resources){const r=d.resources;const p=element('p','RAM available: '+numeric(r.memory_available_mib,' MiB')+' / '+numeric(r.memory_total_mib,' MiB')+'\nDisk free: '+numeric(r.disk_free_gib,' GiB')+' / '+numeric(r.disk_total_gib,' GiB'),'resource');if(typeof r.disk_free_gib==='number'&&r.disk_free_gib<5)p.classList.add('warning');card.append(p);}
    card.append(element('p','Telemetry: '+d.telemetry+' · Updates: '+(d.updates||'unknown'),'resource'),element('p',d.detail,'detail'));
    if(d.desktop_url){const a=element('a','Open desktop ↗','connect');a.href=d.desktop_url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('data-expires',String(Math.min(d.expires_at,data.observed_at+90)));a.setAttribute('aria-label','Open desktop for '+d.name);card.append(a);}else{card.append(element('p','Desktop link unavailable','warning'));}
    $('workers').append(card);
  }
  $('total').textContent=current?.devices?.length??'—';$('online').textContent=current?.devices?.filter(d=>d.transport==='online').length??'—';$('ready').textContent=current?.devices?.filter(d=>d.desktop_url).length??'—';
}
async function refresh(force=false){
  force=force===true;
  if($('refresh').disabled&&!force)return;
  if(force&&requestController)requestController.abort();
  const generation=++requestGeneration;requestController=new AbortController();
  $('refresh').disabled=true;$('workers').setAttribute('aria-busy','true');$('status').textContent='Checking transport and configured workers…';
  try{const r=await fetch('/api/workers',{signal:AbortSignal.any([requestController.signal,AbortSignal.timeout(20000)])});if(!r.ok)throw Error('Management service returned HTTP '+r.status);const next=await r.json();if(generation!==requestGeneration)return;data=next;$('error').hidden=!data.error;$('error').textContent=data.error||'';$('troubleshooting').hidden=!data.technical_detail;$('technical-detail').textContent=data.technical_detail||'';render();$('status').textContent='Checked '+new Date(data.observed_at*1000).toLocaleTimeString()+' · refreshes every 60 seconds';}
  catch(e){if(generation!==requestGeneration)return;data=null;render();$('error').hidden=false;$('error').textContent='The local management service is unavailable. Open Workers management again, then refresh.';$('troubleshooting').hidden=false;$('technical-detail').textContent=e.message;$('status').textContent='Status unavailable; previous states have been cleared.';}
  finally{if(generation===requestGeneration){$('refresh').disabled=false;$('workers').setAttribute('aria-busy','false');}}
}
$('refresh').onclick=refresh;$('filter').oninput=render;refresh();setInterval(()=>{if(!document.hidden&&!$('refresh').disabled)refresh();},60000);
function expireVisible(){if(expiryKey(data)!==renderedExpiryKey)render();}
setInterval(expireVisible,1000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden){expireVisible();refresh(true);}});
document.addEventListener('click',e=>{const a=e.target.closest('a[data-expires]');if(a&&Date.now()/1000>=Number(a.getAttribute('data-expires'))){e.preventDefault();expireVisible();refresh();}},true);
