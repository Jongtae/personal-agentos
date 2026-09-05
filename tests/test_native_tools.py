import unittest,json
from personal_agent.providers import ModelAdapter
from personal_agent.local_tools import run_native_tools
class NativeTests(unittest.TestCase):
 def test_real_wire_contract_and_tool_id(self):
  requests=[]
  def transport(url,body,headers):
   requests.append(json.loads(json.dumps(body)))
   if len(requests)==1:return {'model':'test:free','choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'call_1','type':'function','function':{'name':'weather','arguments':'{"city":"Seongnam","country":"KR"}'}}]}}]}
   return {'model':'test:free','choices':[{'message':{'role':'assistant','content':'날씨 확인 완료'}}]}
  class Executor:
   def execute(self,plan):
    self.plan=plan;return {'location':{'name':'Seongnam'},'forecast':{'current':{'time':'2026-09-05T12:00','temperature_2m':25,'apparent_temperature':26,'precipitation':0,'wind_speed_10m':5},'current_units':{'temperature_2m':'°C','apparent_temperature':'°C','precipitation':'mm','wind_speed_10m':'km/h'}},'sources':['https://open-meteo.com/']}
  executor=Executor();events=[]
  cfg={'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'}
  result=run_native_tools(ModelAdapter(transport),cfg,'test',[{'role':'user','content':'성남은?'}],'',executor,lambda *e:events.append(e))
  self.assertEqual(executor.plan['city'],'Seongnam')
  self.assertEqual(requests[1]['messages'][-1]['role'],'tool')
  self.assertEqual(requests[1]['messages'][-1]['tool_call_id'],'call_1')
  self.assertEqual(requests[0]['tools'],requests[1]['tools'])
  self.assertTrue(requests[0]['provider']['require_parameters'])
  self.assertIn('https://open-meteo.com/',result.content)
  self.assertIn('25 °C',result.content)
  self.assertEqual(events[-1][1],'succeeded')
if __name__=='__main__':unittest.main()

class AcceptanceTests(unittest.TestCase):
 def test_followup_policy(self):
  from personal_agent.local_tools import weather_context
  self.assertTrue(weather_context([{'role':'user','content':'날씨 알려줘'},{'role':'assistant','content':'어디인가요?'},{'role':'user','content':'성남시'}]))
  self.assertFalse(weather_context([{'role':'user','content':'날씨 알려줘'},{'role':'user','content':'최신 뉴스 검색'}]))
  for prompt in ['다른 것도 할 수 있어?','파이썬 설명해줘','안녕','농담해줘','날씨 조회 기능은 어떻게 작동해?']:
   self.assertFalse(weather_context([{'role':'user','content':'현재 성남시 날씨'},{'role':'user','content':prompt}]),prompt)
 def test_no_call_cannot_pass_weather(self):
  from personal_agent.providers import ProviderError
  def transport(u,b,h):
   self.assertEqual(b['tool_choice'],'required')
   self.assertEqual({x['function']['name'] for x in b['tools']},{'weather','ask_location'})
   return {'choices':[{'message':{'content':'조회할 수 없습니다'}}]}
  with self.assertRaises(ProviderError):run_native_tools(ModelAdapter(transport),{'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'},'', [{'role':'user','content':'성남 날씨'}],'',None,lambda *a:None)
 def test_missing_location_asks_without_lookup(self):
  def transport(u,b,h):return {'choices':[{'message':{'tool_calls':[{'id':'ask1','function':{'name':'ask_location','arguments':'{"question":"어느 도시인가요?"}'}}]}}]}
  r=run_native_tools(ModelAdapter(transport),{'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'},'',[{'role':'user','content':'날씨'}],'',None,lambda *a:None)
  self.assertIn('도시',r.content)
 def test_failed_tool_is_failed_job_with_history(self):
  import tempfile
  from personal_agent.quickstart_store import QuickStore
  from personal_agent.quickstart_service import AgentService
  from personal_agent.providers import ProviderError
  with tempfile.TemporaryDirectory() as root:
   store=QuickStore(root);calls=[]
   def transport(u,b,h):
    calls.append(b)
    if len(calls)==1:return {'choices':[{'message':{'tool_calls':[{'id':'fail1','function':{'name':'weather','arguments':'{"city":"Seongnam"}'}}]}}]}
    return {'choices':[{'message':{'content':'조회 완료'}}]}
   svc=AgentService(store,ModelAdapter(transport));svc.save_model({'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'})
   class Broken:
    def execute(self,p):raise ProviderError('test offline')
   svc.local_tools=Broken();job=store.enqueue('성남 날씨','failure-test');svc.run_one()
   self.assertEqual(store.jobs()[0]['status'],'failed')
   reopened=QuickStore(root)
   with reopened.db() as db:
    rows=db.execute('SELECT * FROM tool_events WHERE job_id=?',(job,)).fetchall()
    self.assertEqual([r['status'] for r in rows],['running','failed'])
    self.assertIn('fail1',rows[0]['detail'])
