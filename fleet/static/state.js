'use strict';
function expireSnapshot(data, now=Date.now()/1000) {
 if(!data)return null;
 const transportExpired=!Number.isFinite(data.observed_at)||now>=data.observed_at+90||now<data.observed_at-30;
 return {...data,devices:(data.devices||[]).map(d=>{
  const expired=transportExpired||(d.telemetry==='fresh'&&(!Number.isFinite(d.expires_at)||now>=d.expires_at));
  if(!expired)return {...d};
  return {...d,transport:transportExpired?'unknown':d.transport,desktop:'unknown',app:'unknown',worker:'unknown',telemetry:'stale',desktop_url:null,resources:null,updates:'unknown',detail:'Status expired. Refresh is required before opening this desktop.'};
 })};
}
function expiryKey(data, now=Date.now()/1000){return JSON.stringify(expireSnapshot(data,now)?.devices.map(d=>[d.transport,d.telemetry,!!d.desktop_url]));}
if(typeof module!=='undefined')module.exports={expireSnapshot,expiryKey};
