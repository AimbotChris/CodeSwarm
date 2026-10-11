// Execute the actual shipped state.js/app.js with a small DOM and controlled clock/network.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
let now=1000,mode='ok',calls=0;
class Element{constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.value='';this.disabled=false;this.classList={add(){}};}append(...x){this.children.push(...x);}prepend(...x){this.children.unshift(...x);}replaceChildren(...x){this.children=x;}setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}}
const ids={};for(const id of ['filter','workers','empty','empty-detail','total','online','ready','refresh','status','error','troubleshooting','technical-detail'])ids[id]=new Element(id);
const events={},timers={};const document={hidden:false,getElementById:id=>ids[id],createElement:t=>new Element(t),addEventListener:(n,f)=>events[n]=f};
let emptyFixture=null;
const snapshot=()=>emptyFixture||({observed_at:now,devices:[{id:'qa',name:'QA worker',hostname:'qa.example.ts.net',os:'linux',transport:'online',desktop:'active',app:'running',worker:'unknown',telemetry:'fresh',expires_at:now+60,desktop_url:'https://qa.example.ts.net/vnc.html',detail:'QA fixture'}],error:null});
class Clock extends Date{static now(){return now*1000;}}
const context=vm.createContext({document,Date:Clock,console,Number,JSON,AbortController,AbortSignal,setInterval:(f,n)=>timers[n]=f,fetch:async()=>{calls++;if(mode==='hang')return new Promise(()=>{});if(mode==='error')throw Error('offline');return{ok:true,json:async()=>snapshot()};}});
vm.runInContext(fs.readFileSync('fleet/static/state.js','utf8'),context);vm.runInContext(fs.readFileSync('fleet/static/app.js','utf8'),context);
const links=()=>{const found=[];function walk(e){if(e.tag==='a')found.push(e);e.children.forEach(walk);}walk(ids.workers);return found;};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();assert.equal(links().length,1);assert.equal(ids.ready.textContent,1);
 mode='hang';context.refresh();await tick();now=1061;timers[1000]();assert.equal(links().length,0);assert.equal(ids.ready.textContent,0);assert.equal(ids.refresh.disabled,true);
 document.hidden=true;now=1199;const before=calls;document.hidden=false;events.visibilitychange();await tick();assert.equal(calls,before+1);assert.equal(links().length,0);assert.equal(ids.online.textContent,0);
 mode='ok';await context.refresh(true);assert.equal(links().length,1);
 const staleLink=links()[0];now+=61;let prevented=false;events.click({target:{closest:()=>staleLink},preventDefault:()=>prevented=true});assert.equal(prevented,true);assert.equal(links().length,0);await tick();
 mode='error';await context.refresh(true);assert.equal(links().length,0);assert.equal(ids.error.hidden,false);assert.match(ids.status.textContent,/cleared/);
 for(const [state,message,instructions] of [
 ['not-installed','Install Tailscale on this computer to see your workers.','Ask the owner to install Tailscale.'],
 ['not-running','Start Tailscale on this computer to see your workers.','Open Tailscale and start its connection.'],
 ['not-logged-in','Connect this computer to Tailscale to see your workers.','Open Tailscale and sign in.'],
 ['permission-denied','This account cannot read Tailscale status.','Ask the administrator to review access.'],
 ['unavailable','Tailscale status is unavailable right now.','Check the connection.']]){
  emptyFixture={observed_at:now,devices:[],error:message,connection_state:state,setup_instructions:instructions,technical_detail:"Command ['tailscale'] returned exit status 1"};mode='ok';await context.refresh(true);
  assert.equal(ids.error.textContent,message);assert.equal(ids['empty-detail'].textContent,instructions);assert.equal(ids.empty.hidden,false);assert.equal(ids.troubleshooting.hidden,false);assert.match(ids['technical-detail'].textContent,/Command/);assert.equal(links().length,0);
 }
 emptyFixture=null;await context.refresh(true);assert.equal(ids.troubleshooting.hidden,true);assert.equal(ids['technical-detail'].textContent,'');
 console.log('PASS actual fleet UI: initial link, hung-refresh expiry, hidden/reopen expiry + immediate refresh, stale click blocked, fresh recovery, network error clears states.');
})().catch(e=>{console.error(e);process.exitCode=1;});
