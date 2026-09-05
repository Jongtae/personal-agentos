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
 let s=await api('/api/status');
 if(!s.claimed){await api('/api/claim',{code:bootstrap});s=await api('/api/status');}
 claimed=s.claimed;authenticated=s.authenticated;
 if(!authenticated&&s.local_access){await api('/api/local-login',{});authenticated=true;}
 $('welcome').hidden=authenticated;$('workspace').hidden=!authenticated;$('logout').hidden=!authenticated||s.local_access;
 $('auth-title').textContent=claimed?'다시 만나서 반갑습니다.':'나만의 에이전트를 시작하세요.';
 $('auth-step').textContent=claimed?'개인 환경 로그인':'처음 시작하기';
 $('auth-help').textContent=claimed?'설정한 비밀번호로 로그인하세요.':'설정 없이 바로 시작할 수 있습니다. 이 PC를 함께 쓰는 사람이 있다면 비밀번호를 설정하세요.';
 $('auth-submit').textContent=claimed?'로그인':'바로 시작하기';
 $('password').required=claimed;$('password-option').open=claimed;$('password').minLength=claimed?1:12;$('password').autocomplete=claimed?'current-password':'new-password';
 $('password-label').textContent=claimed?'비밀번호':'사용할 비밀번호';
 if(authenticated){await refresh();await finishOpenRouter();}
}
$('auth-form').addEventListener('submit',async e=>{e.preventDefault();$('auth-error').textContent='';await busy($('auth-submit'),async()=>{try{await api(claimed?'/api/login':'/api/claim',{password:$('password').value,code:bootstrap});bootstrap='';$('password').value='';await status();}catch(e){error('auth-error',e);}});});
$('logout').onclick=async()=>{try{await api('/api/logout',{});modelLoaded=false;stateFingerprint='';await status();}catch(e){error('global-error',e);}};
const providers={ollama:{endpoint:'http://127.0.0.1:11434',help:'Ollama 서버의 주소입니다. 모델은 Ollama에 미리 설치되어 있어야 합니다.'},compatible:{endpoint:'https://openrouter.ai/api/v1',help:'Chat Completions 호환 기본 URL입니다. 필요한 경우 /v1을 포함하세요.'},anthropic:{endpoint:'https://api.anthropic.com',help:'Anthropic에서 사용 가능한 모델 ID와 API 키를 입력하세요.'}};
$('provider').onchange=()=>{const p=providers[$('provider').value];$('endpoint').value=p.endpoint;$('endpoint-help').textContent=p.help;$('api-key').value='';$('model-feedback').textContent='연결 대상이 바뀌면 기존 키를 자동으로 전달하지 않습니다. 필요한 키를 다시 입력하세요.';};
$('model-form').onsubmit=async e=>{e.preventDefault();await busy(e.submitter,async()=>{try{await api('/api/model',{provider:$('provider').value,endpoint:$('endpoint').value,model:$('model-name').value,api_key:$('api-key').value});$('api-key').value='';$('model-feedback').textContent='저장했습니다. 연결 확인을 누르면 실제 응답을 확인합니다.';await refresh();}catch(e){error('model-feedback',e);}});};
$('test-model').onclick=async()=>busy($('test-model'),async()=>{try{const data=await api('/api/model/test',{});$('model-feedback').textContent='실제 모델 응답: '+data.response;await refresh();}catch(e){error('model-feedback',e);}});
function showPair(data){$('pair-link').href=data.url;$('telegram-pair').hidden=false;$('telegram-token').value='';}
$('telegram-form').onsubmit=async e=>{e.preventDefault();await busy(e.submitter,async()=>{try{showPair(await api('/api/telegram',{token:$('telegram-token').value}));await refresh();}catch(e){error('telegram-status',e);}});};
$('new-pair').onclick=async()=>{try{showPair(await api('/api/telegram/pair',{}));}catch(e){error('telegram-status',e);}};
$('disconnect').onclick=async()=>{try{await api('/api/telegram/disconnect',{});$('telegram-pair').hidden=true;await refresh();}catch(e){error('telegram-status',e);}};
function openConnections(){ $('connections').hidden=false;$('settings-panel').scrollIntoView({behavior:'smooth',block:'start'});}
$('toggle-settings').onclick=openConnections;
$('try-ai').onclick=openConnections;
$('try-note').onclick=()=>{$('message').value='메모: ';$('message').focus();};
$('chat-form').onsubmit=async e=>{e.preventDefault();const message=$('message').value.trim();if(!message)return;if(!hasModel&&!/^(메모:|기록:|\/note(?:s)?(?:\s|$)|\/help$)/.test(message)){openConnections();$('easy-feedback').textContent='AI를 연결하면 작성한 메시지를 보낼 수 있어요. 입력한 내용은 그대로 남겨 두었습니다.';return;}await busy(e.submitter,async()=>{try{await api('/api/chat',{message,request_key:crypto.randomUUID()});$('message').value='';$('global-error').textContent='';await refresh();}catch(e){error('global-error',e);}});};
document.querySelectorAll('[data-message]').forEach(button=>button.onclick=()=>{$('message').value=button.dataset.message;$('message').focus();});
function element(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
async function refresh(){
 if(!authenticated||refreshing)return;refreshing=true;
 try{
 const state=await api('/api/state');const settings=state.settings;const model=settings.model;const tg=settings.telegram;hasModel=!!model.model;
 const latest=state.jobs.find(j=>j.status==='succeeded'&&j.model)||state.jobs.find(j=>j.model);
 $('actual-model').textContent=latest?'최근 응답 모델: '+latest.model:(model.model==='openrouter/free'?'무료 모델 자동 선택 · 첫 응답 후 실제 모델이 표시됩니다.':'');
 $('tool-status').textContent=settings.tool_run?({running:'조회 중',succeeded:'조회 완료',failed:'조회 실패'}[settings.tool_run.status]+' · '+settings.tool_run.tool+' · 내 AgentOS에서 실행'):'';
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
 if(state.messages.length){container.replaceChildren();for(const m of state.messages){const item=element('article',undefined,'message '+m.role);item.append(element('div',(m.role==='user'?'나':'AgentOS')+' · '+(m.channel.startsWith('telegram:')?'Telegram':'웹'),'message-meta'));const bubble=element('div',undefined,'bubble');for(const part of m.content.split(/(https?:\/\/[^\s<>]+)/g)){if(/^https?:\/\//.test(part)){const a=element('a',part);a.href=part;a.target='_blank';a.rel='noreferrer noopener';bubble.append(a);}else bubble.append(document.createTextNode(part));}item.append(bubble);container.append(item);}if(nearBottom||container.scrollTop===0)container.scrollTop=container.scrollHeight;}
 const pending=state.jobs.filter(j=>j.status==='queued'||j.status==='running');const failed=state.jobs.slice(0,1).find(j=>j.status==='failed'||j.status==='interrupted'||j.delivery==='unknown');
 $('job-status').textContent=pending.length?`${pending.length}개 작업 처리 중…`:failed?(failed.delivery==='unknown'?'Telegram 전송 결과가 불확실합니다. 자동 재전송하지 않으며 결과는 웹 기록에서 확인할 수 있습니다.':failed.error):'';
 $('note-count').textContent=String(state.notes.length);$('notes-list').replaceChildren();for(const n of state.notes)$('notes-list').append(element('article',n.content));if(!state.notes.length)$('notes-list').append(element('p','메모가 없습니다.'));
 }
 }catch(e){error('global-error',e);}finally{refreshing=false;}
}
status().catch(e=>error('global-error',e));setInterval(()=>{if(authenticated)refresh();},2000);

let hasModel=false;
$('connect-openrouter').onclick=async()=>{
 const popup=window.open('about:blank','agentos-openrouter');
 try {
 const bytes=crypto.getRandomValues(new Uint8Array(48));
 const verifier=btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier));
 const challenge=btoa(String.fromCharCode(...new Uint8Array(digest))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 sessionStorage.setItem('agentos-draft',$('message').value);
 const state=crypto.randomUUID();localStorage.setItem('openrouter-flow',JSON.stringify({verifier,state,expires:Date.now()+600000}));
 const callback=location.origin+'/?state='+encodeURIComponent(state);
 const url='https://openrouter.ai/auth?'+new URLSearchParams({callback_url:callback,code_challenge:challenge,code_challenge_method:'S256'});
 const flow=JSON.parse(localStorage.getItem('openrouter-flow'));flow.url=url;localStorage.setItem('openrouter-flow',JSON.stringify(flow));
 $('resume-openrouter').hidden=false;$('easy-feedback').textContent='새 창에서 가입 또는 로그인하고 연결을 승인해 주세요. 이 대화는 그대로 유지됩니다. 가입 후 승인 화면이 나오지 않으면 연결 이어가기를 눌러 주세요.';
 if(popup)popup.location.href=url;else $('easy-feedback').textContent='새 창이 차단됐습니다. 연결 이어가기를 눌러 새 창을 열어 주세요.';
 }catch(e){error('easy-feedback',e);}
};
async function finishOpenRouter(){
 const params=new URLSearchParams(location.search);if(!params.has('code'))return;
 const code=params.get('code'),returnedState=params.get('state');history.replaceState(null,'',location.pathname);
 openConnections();$('message').value=sessionStorage.getItem('agentos-draft')||'';sessionStorage.removeItem('agentos-draft');
 try{
 const flow=JSON.parse(localStorage.getItem('openrouter-flow')||'null');
 if(!flow||flow.state!==returnedState||Date.now()>flow.expires)throw new Error('연결 시간이 지났습니다. 계정 연결을 다시 눌러 주세요.');
 await api('/api/openrouter/connect',{code,verifier:flow.verifier});localStorage.removeItem('openrouter-flow');localStorage.setItem('openrouter-connected',String(Date.now()));modelLoaded=false;await refresh();
 $('easy-feedback').textContent='무료 AI가 연결됐습니다. 대화창에서 메시지를 보내 보세요.';$('message').focus();if(window.opener)window.close();
 }catch(e){error('easy-feedback',e);$('resume-openrouter').hidden=false;}
}
$('find-local').onclick=()=>busy($('find-local'),async()=>{
 $('local-models').replaceChildren();
 try{
 const data=await api('/api/ollama/models',{});
 $('local-help').textContent=data.models.length?'사용할 모델을 선택하세요.':'Ollama는 실행 중이지만 모델이 없습니다. Ollama에서 모델을 먼저 다운로드해 주세요.';
 for(const m of data.models){const button=element('button',m.name);button.type='button';button.onclick=()=>busy(button,async()=>{try{await api('/api/model',{provider:'ollama',endpoint:'http://127.0.0.1:11434',model:m.name});modelLoaded=false;await refresh();$('local-help').textContent='연결했습니다. 대화창에서 메시지를 보내세요.';}catch(e){error('local-help',e);}});$('local-models').append(button);}
 }catch(e){$('local-help').textContent='실행 중인 Ollama를 찾지 못했습니다. 아래 설치 안내에서 설치하고 실행한 뒤 다시 찾아 주세요.';}
});

$('resume-openrouter').onclick=()=>{
 const flow=JSON.parse(localStorage.getItem('openrouter-flow')||'null');
 if(flow&&flow.expires>Date.now()&&flow.url){window.open(flow.url,'agentos-openrouter');}
 else $('connect-openrouter').click();
};
if(localStorage.getItem('openrouter-flow')){$('resume-openrouter').hidden=false;}
window.addEventListener('storage',async e=>{if(e.key==='openrouter-connected'){modelLoaded=false;await refresh();$('resume-openrouter').hidden=true;$('easy-feedback').textContent='무료 AI 연결이 완료됐습니다. 작성하던 대화를 이어가세요.';$('message').focus();}});
$('load-free-models').onclick=()=>busy($('load-free-models'),async()=>{
 try{const data=await api('/api/openrouter/models',{});$('free-model-list').replaceChildren();
 for(const m of data.models){const row=element('p',m.name+' · '+m.id);$('free-model-list').append(row);}
 if(!data.models.length)$('free-model-list').append(element('p','현재 확인된 무료 모델이 없습니다. 잠시 후 다시 확인하세요.'));
 }catch(e){$('free-model-list').replaceChildren(element('p','목록을 가져오지 못했습니다. 잠시 후 다시 시도하세요.'));}
});
