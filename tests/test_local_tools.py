import unittest
from unittest.mock import patch
from personal_agent.local_tools import LocalTools,needs_lookup
from personal_agent.providers import ModelResult,ProviderError
class LocalToolTests(unittest.TestCase):
    def test_intents(self):
        self.assertTrue(needs_lookup('서울 오늘 날씨 알려줘'))
        self.assertTrue(needs_lookup('최신 뉴스 검색해줘'))
        self.assertFalse(needs_lookup('안녕'))
    def test_search_result_is_passed_to_model(self):
        class Adapter:
            def invoke(self,c,k,m):
                self.messages=m
                return ModelResult('근거 기반 답변','compatible','test-model')
        a=Adapter();events=[]
        with patch.object(LocalTools,'search',return_value={'tool':'web_search','results':[{'snippet':'untrusted'}],'sources':['https://example.com']}):
            r=LocalTools().answer(a,{},'',[],'system','/search public query',lambda *e:events.append(e))
        self.assertIn('https://example.com',r.content)
        self.assertIn('untrusted',a.messages[-1]['content'])
        self.assertEqual([e[1] for e in events],['running','succeeded'])
    def test_missing_weather_location_clarifies_without_network(self):
        class Adapter:
            def invoke(self,*args):return ModelResult('{"tool":"clarify","question":"어느 도시의 날씨를 확인할까요?"}','test','test')
        with patch.object(LocalTools,'execute') as execute:
            r=LocalTools().answer(Adapter(),{},'',[],'','오늘 날씨',lambda *e:None)
            execute.assert_not_called();self.assertIn('도시',r.content)
    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):LocalTools().execute({'tool':'shell','command':'bad'})
    def test_failure_does_not_claim_success(self):
        with patch.object(LocalTools,'search',side_effect=ProviderError('검색 실패')):
            events=[]
            with self.assertRaises(ProviderError):LocalTools().answer(None,{},'',[],'','/search hello',lambda *e:events.append(e))
            self.assertEqual(events[-1][1],'failed')
if __name__=='__main__':unittest.main()
