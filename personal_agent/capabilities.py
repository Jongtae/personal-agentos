"""Reviewed capability lifecycle; never installs or executes arbitrary code."""
import time

CATALOGUE=(
 {'id':'builtin-mcp-read','kind':'mcp','version':'1','tools':['read_only'],'scopes':['read']},
 {'id':'compatibility-a2a-peer','kind':'a2a','version':'1','tools':['delegate'],'scopes':['delegate']},
 {'id':'isolated-runtime-placeholder','kind':'runtime','version':'1','tools':[],'scopes':[]},
)
STATES={'available','connected-disabled','enabled','paused','auth-required','error','disconnected'}

class CapabilityRegistry:
 def __init__(self,store): self.store=store
 def list(self):
  saved=self.store.config('capability_registry',{})
  return [{**item,'state':saved.get(item['id'],{}).get('state','available')} for item in CATALOGUE]
 def transition(self,capability_id,target,approved_scopes=()):
  item=next((x for x in CATALOGUE if x['id']==capability_id),None)
  if not item or target not in STATES: raise ValueError('검토된 capability와 상태를 확인하세요.')
  if target=='enabled' and set(item['scopes'])!=set(approved_scopes): raise ValueError('선언된 scope의 명시 승인이 필요합니다.')
  saved=self.store.config('capability_registry',{});saved[capability_id]={'state':target,'changed_at':time.time()};self.store.put('capability_registry',saved)
  return next(x for x in self.list() if x['id']==capability_id)
