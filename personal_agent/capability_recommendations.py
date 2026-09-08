"""Owner-local, reviewed capability recommendations; never an installer."""
import time

CATALOGUE = (
    {"id":"reviewed-drive-search","kind":"mcp","name":"Reviewed Drive search","outcomes":["private-document-research"],"publisher":"AgentOS reviewed catalogue","version":"1.0.0","digest":"sha256:drive-search-v1","license":"Apache-2.0","permissions":["read"],"data":["selected-document-excerpts"],"isolation":"owner-local adapter","cost":"none","health":"mock-contract","recovery":"Keep disabled; configure only in operating mode."},
    {"id":"reviewed-research-peer","kind":"a2a","name":"Reviewed research peer","outcomes":["specialist-research"],"publisher":"AgentOS compatibility fixtures","version":"1.0.0","digest":"sha256:research-peer-v1","license":"Apache-2.0","permissions":["delegate"],"data":["owner-approved-minimum-context"],"isolation":"bounded A2A contract","cost":"unknown","health":"mock-contract","recovery":"Keep disabled; inspect the future approval handoff."},
    {"id":"reviewed-local-runtime","kind":"runtime","name":"Reviewed local runtime","outcomes":["local-specialist-processing"],"publisher":"AgentOS reviewed catalogue","version":"1.0.0","digest":"sha256:local-runtime-v1","license":"Apache-2.0","permissions":[],"data":["declared-local-input"],"isolation":"isolated owner runtime","cost":"none","health":"mock-contract","recovery":"Keep disabled; inspect the future approval handoff."},
)

class RecommendationError(ValueError): pass

class CapabilityRecommendationOrchestrator:
    def __init__(self, store, now=time.time): self.store,self.now=store,now
    def recommend(self, owner, outcome):
        if not isinstance(owner,str) or not owner or not isinstance(outcome,str) or outcome not in {tag for item in CATALOGUE for tag in item['outcomes']}:
            raise RecommendationError('검토된 결과 유형을 선택하세요.')
        rows=[item for item in CATALOGUE if outcome in item['outcomes']]
        rows.sort(key=lambda item:(len(item['permissions'])+len(item['data']), 0 if item['cost']=='none' else 1, item['id']))
        result=[{key:item[key] for key in ('id','kind','name','version','license','permissions','data','isolation','cost','health','recovery')} | {"reason":f"declared outcome: {outcome}","approval_handoff":"future-explicit-install-approval"} for item in rows]
        audit=self.store.config('capability_recommendation_audit',[]);audit=audit if isinstance(audit,list) else []
        self.store.put('capability_recommendation_audit',[*audit,{"at":self.now(),"outcome":outcome,"count":len(result),"terminal":"recommended"}][-100:])
        return {"state":"recommended","outcome":outcome,"recommendations":result}
