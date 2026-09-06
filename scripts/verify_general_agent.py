"""Live multi-topic acceptance, isolated from personal conversation and files."""
import json,tempfile,time,sys
from pathlib import Path
sys.path.insert(0,'/opt/homebrew/opt/agentos/libexec' if '--installed' in sys.argv else str(Path(__file__).resolve().parents[1]))
from personal_agent.quickstart_store import QuickStore
from personal_agent.quickstart_service import AgentService
source=QuickStore(Path.home()/'.local/share/agentos')
results=[]
with tempfile.TemporaryDirectory() as root:
 docs=Path(root)/'documents';docs.mkdir();(docs/'aurora-launch.txt').write_text('Project Aurora launch date: 2031-10-12. Owner: Mina. Budget: 4200 USD.')
 store=QuickStore(Path(root)/'data');svc=AgentService(store)
 svc.save_roots({'paths':[str(docs)]})
 config=dict(source.config('model'))
 if '--model' in sys.argv:config['model']=sys.argv[sys.argv.index('--model')+1]
 svc.save_model({**config,'api_key':source.secret('model_key')})
 cases=[('search','Kubernetes 공식 문서를 웹에서 검색해서 링크를 알려줘',['web_search'],None),('files','이번에는 내 파일에서 Aurora 출시 날짜를 찾아줘. 파일 내용으로 확인해줘.',['find_files','read_file'],'2031'),('delegate','방금 읽은 Aurora 출시 내용을 검토 에이전트에게 전달해서 검토를 받아줘.',['delegate_agent'],None),('general','이제 다른 주제야. 도구를 쓰지 말고 안녕이라고만 답해줘.',[], '안녕'),('memory','Aurora 출시 검토가 필요하다는 내용을 내 메모에 저장해줘.',['save_note'],None)]
 for label,prompt,expected,substring in cases:
  job=store.enqueue(prompt,'acceptance-'+label);svc.run_one()
  row=store.jobs()[0]
  with store.db() as db:events=[dict(r) for r in db.execute('SELECT * FROM tool_events WHERE job_id=? ORDER BY id',(job,))]
  actual={e['tool'] for e in events if e['status']=='succeeded'}
  passed=row['status']=='succeeded' and all(x in actual for x in expected) and (bool(substring in (row.get('response') or '')) if substring else True)
  if label=='general':passed=passed and not any(e['status']=='running' for e in events)
  results.append({'case':label,'passed':passed,'status':row['status'],'response':row.get('response'),'error':row.get('error'),'model':row['model'],'events':events})
  print(label,'PASS' if passed else 'FAIL',sorted(actual),row['model'],flush=True)
Path('GENERAL_AGENT_ACCEPTANCE.json').write_text(json.dumps({'installed':'--installed' in sys.argv,'tested_at':time.time(),'configured_model':config['model'],'results':results},ensure_ascii=False,indent=2))
if not all(r['passed'] for r in results):raise SystemExit(1)
