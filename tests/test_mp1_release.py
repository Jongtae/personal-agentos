"""Automated MP1 Core release acceptance: no external provider is contacted."""
import tempfile
from personal_agent.a2a import A2ADelegation
from personal_agent.calendar import CalendarCreate
from personal_agent.capabilities import CapabilityRegistry
from personal_agent.google_drive import GoogleDrive
from personal_agent.quickstart_store import QuickStore

class Peer:
 def card(self):return {'protocol':'a2a/1','skill':'bounded-research','artifact_schema':'text'}
 def create(self,p):return {'correlation_id':p['correlation_id']}
 def status(self,i,c):return {'correlation_id':c,'state':'completed','artifact':{'id':'a','text':'delegated evidence'}}
 def cancel(self,i,c):pass

def test_mp1_owner_flow_uses_evidence_explicit_delegation_approval_and_disconnect():
 with tempfile.TemporaryDirectory() as root:
  store=QuickStore(root)
  def drive_transport(url,body,headers):return {'files':[{'id':'f','name':'source'}]}
  source=GoogleDrive(drive_transport,'mock-token').search('source')[0]
  delegation=A2ADelegation(store,Peer()).delegate({'explicit':True,'owner':'owner','prompt':'summarize '+source['name']})
  assert A2ADelegation(store,Peer()).status(delegation['id'],'owner')['state']=='completed'
  calls=[];calendar=CalendarCreate(store,lambda url,body,headers:calls.append((url,body,headers)) or {'id':'event-1'})
  draft=calendar.draft({'summary':'review','start':'2026-01-01T10:00','end':'2026-01-01T11:00','timezone':'Asia/Seoul'})
  approval=calendar.approve(draft['id'],'owner');assert not calls
  assert calendar.create(draft['id'],approval['approval_id'],'owner')['id']=='event-1';assert len(calls)==1
  registry=CapabilityRegistry(store);registry.transition('compatibility-a2a-peer','enabled',('delegate',));assert registry.transition('compatibility-a2a-peer','disconnected')['state']=='disconnected'
  assert store.config('a2a_delegations') and store.config('calendar_create')
