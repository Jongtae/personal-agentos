'use strict';
const $=id=>document.getElementById(id);
let claimed=false, authenticated=false, modelLoaded=false, stateFingerprint='', refreshing=false;
let bootstrap=new URLSearchParams(location.hash.slice(1)).get('setup')||'';
if(bootstrap)history.replaceState(null,'',location.pathname+location.search);
async function api(path,body){
 const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await response.json();
 if(!response.ok)throw new Error(data.error||'요청을 처리할 수 없습니다.');
 return data;
}
function error(id,e){$(id).textContent=e.message||String(e);}
async function busy(button,fn){const text=button.textContent;button.disabled=true;button.textContent='처리 중…';try{await fn();}finally{button.disabled=false;button.textContent=text;}}
async function status(){
 const s=await api('/api/status');claimed=s.claimed;authenticated=s.authenticated;
 $('welcome').hidden=authenticated;$('workspace').hidden=!authenticated;$('logout').hidden=!authenticated;
 $('auth-title').textContent=claimed?'다시 만나서 반갑습니다.':'나만의 에이전트를 시작하세요.';
 $('auth-step').textContent=claimed?'개인 환경 로그인':'01 / 관리자 설정';
 $('auth-help').textContent=claimed?'관리자 비밀번호로 로그인하세요.':'이 환경을 관리할 비밀번호를 정하세요. 기록과 연결 설정을 보호합니다.';
 $('auth-submit').textContent=claimed?'로그인':'개인 환경 만들기';
 $('password').minLength=claimed?1:12;$('password').autocomplete=claimed?'current-password':'new-password';
 $('code-label').hidden=claimed||!!bootstrap;
 if(authenticated)await refresh();
}
$('auth-form').addEventListener('submit',async e=>{e.preventDefault();$('auth-error').textContent='';await busy($('auth-submit'),async()=>{try{await api(claimed?'/api/login':'/api/claim',{password:$('password').value,code:bootstrap||$('setup-code').value});bootstrap='';$('password').value='';await status();}catch(e){error('auth-error',e);}});});
$('logout').onclick=async()=>{try{await api('/api/logout',{});modelLoaded=false;stateFingerprint='';await status();}catch(e){error('global-error',e);}};
const providers={ollama:{endpoint:'http://127.0.0.1:11434',help:'Ollama 서버의 주소입니다. 모델은 Ollama에 미리 설치되어 있어야 합니다.'},compatible:{endpoint:'https://api.openai.com/v1',help:'Chat Completions 호환 기본 URL입니다. 필요한 경우 /v1을 포함하세요.'},anthropic:{endpoint:'https://api.anthropic.com',help:'Anthropic에서 사용 가능한 모델 ID와 API 키를 입력하세요.'}};
$('provider').onchange=()=>{const p=providers[$('provider').value];$('endpoint').value=p.endpoint;$('endpoint-help').textContent=p.help;$('api-key').value='';$('model-feedback').textContent='연결 대상이 바뀌면 기존 키를 자동으로 전달하지 않습니다. 필요한 키를 다시 입력하세요.';};
$('model-form').onsubmit=async e=>{e.preventDefault();await busy(e.submitter,async()=>{try{await api('/api/model',{provider:$('provider').value,endpoint:$('endpoint').value,model:$('model-name').value,api_key:$('api-key').value});$('api-key').value='';$('model-feedback').textContent='저장했습니다. 연결 확인을 누르면 실제 응답을 확인합니다.';await refresh();}catch(e){error('model-feedback',e);}});};
$('test-model').onclick=async()=>busy($('test-model'),async()=>{try{const data=await api('/api/model/test',{});$('model-feedback').textContent='실제 모델 응답: '+data.response;await refresh();}catch(e){error('model-feedback',e);}});
function showPair(data){$('pair-link').href=data.url;$('telegram-pair').hidden=false;$('telegram-token').value='';}
$('telegram-form').onsubmit=async e=>{e.preventDefault();await busy(e.submitter,async()=>{try{showPair(await api('/api/telegram',{token:$('telegram-token').value}));await refresh();}catch(e){error('telegram-status',e);}});};
$('new-pair').onclick=async()=>{try{showPair(await api('/api/telegram/pair',{}));}catch(e){error('telegram-status',e);}};
$('disconnect').onclick=async()=>{try{await api('/api/telegram/disconnect',{});$('telegram-pair').hidden=true;await refresh();}catch(e){error('telegram-status',e);}};
$('toggle-settings').onclick=()=>{$('settings-panel').scrollIntoView({behavior:'smooth',block:'start'});$('provider').focus({preventScroll:true});};
$('chat-form').onsubmit=async e=>{e.preventDefault();const message=$('message').value.trim();if(!message)return;await busy(e.submitter,async()=>{try{await api('/api/chat',{message,request_key:crypto.randomUUID()});$('message').value='';$('global-error').textContent='';await refresh();}catch(e){error('global-error',e);}});};
document.querySelectorAll('[data-message]').forEach(button=>button.onclick=()=>{$('message').value=button.dataset.message;$('message').focus();});
function element(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
async function refresh(){
 if(!authenticated||refreshing)return;refreshing=true;
 try{
 const state=await api('/api/state');const settings=state.settings;const model=settings.model;const tg=settings.telegram;
 $('runtime-badge').textContent=state.healthy?'● 개인 환경 실행 중':'실행 상태 확인 필요';
 if(!modelLoaded){if(model.provider){$('provider').value=model.provider;$('endpoint').value=model.endpoint;$('model-name').value=model.model;}$('endpoint-help').textContent=providers[$('provider').value].help;modelLoaded=true;}
 $('model-label').textContent=model.model?model.model+' · '+(settings.model_test?.ok?'연결 확인됨':'저장됨 · 확인 전'):'메모 기능 준비됨';
 $('model-step').textContent=settings.model_test?.ok?'✓ 모델 연결 확인':'② 모델 연결';$('model-step').classList.toggle('done',!!settings.model_test?.ok);
 $('telegram-step').textContent=tg.paired?'✓ Telegram 계정 연결':'③ Telegram 연결 · 선택';$('telegram-step').classList.toggle('done',tg.paired);
 $('key-hint').textContent=settings.has_api_key?'키가 저장되어 있습니다. 빈칸으로 저장하면 같은 연결의 키를 유지합니다.':'키는 대화 기록과 분리된 개인 설정 파일에 저장합니다.';
 $('telegram-status').textContent=settings.telegram_status?.message||'아직 연결되지 않았습니다.';
 $('disconnect').hidden=!tg.enabled;$('new-pair').hidden=!tg.enabled;
 if(tg.paired)$('telegram-pair').hidden=true;
 const fingerprint=JSON.stringify([state.messages,state.jobs,state.notes]);
 if(fingerprint!==stateFingerprint){stateFingerprint=fingerprint;
 const container=$('messages');const nearBottom=container.scrollHeight-container.scrollTop-container.clientHeight<90;
 if(state.messages.length){container.replaceChildren();for(const m of state.messages){const item=element('article',undefined,'message '+m.role);item.append(element('div',(m.role==='user'?'나':'AgentOS')+' · '+(m.channel.startsWith('telegram:')?'Telegram':'웹'),'message-meta'));item.append(element('div',m.content,'bubble'));container.append(item);}if(nearBottom||container.scrollTop===0)container.scrollTop=container.scrollHeight;}
 const pending=state.jobs.filter(j=>j.status==='queued'||j.status==='running');const failed=state.jobs.find(j=>j.status==='failed'||j.status==='interrupted'||j.delivery==='unknown');
 $('job-status').textContent=pending.length?`${pending.length}개 작업 처리 중…`:failed?(failed.delivery==='unknown'?'Telegram 전송 결과가 불확실합니다. 자동 재전송하지 않으며 결과는 웹 기록에서 확인할 수 있습니다.':failed.error):'';
 $('note-count').textContent=String(state.notes.length);$('notes-list').replaceChildren();for(const n of state.notes)$('notes-list').append(element('article',n.content));if(!state.notes.length)$('notes-list').append(element('p','메모가 없습니다.'));
 }
 }catch(e){error('global-error',e);}finally{refreshing=false;}
}
status().catch(e=>error('global-error',e));setInterval(()=>{if(authenticated)refresh();},2000);
