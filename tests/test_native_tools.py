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
    self.plan=plan;return {'temperature':25,'sources':['https://open-meteo.com/']}
  executor=Executor();events=[]
  cfg={'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'}
  result=run_native_tools(ModelAdapter(transport),cfg,'test',[{'role':'user','content':'성남은?'}],'',executor,lambda *e:events.append(e))
  self.assertEqual(executor.plan['city'],'Seongnam')
  self.assertEqual(requests[1]['messages'][-1]['role'],'tool')
  self.assertEqual(requests[1]['messages'][-1]['tool_call_id'],'call_1')
  self.assertEqual(requests[0]['tools'],requests[1]['tools'])
  self.assertTrue(requests[0]['provider']['require_parameters'])
  self.assertIn('https://open-meteo.com/',result.content)
  self.assertEqual(events[-1][1],'succeeded')
if __name__=='__main__':unittest.main()
