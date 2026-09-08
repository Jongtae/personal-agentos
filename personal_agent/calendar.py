"""Mock-first Calendar create-only approval boundary."""
import hashlib,json,secrets,time,uuid
class CalendarError(ValueError):pass
class CalendarCreate:
 def __init__(self,store,transport,now=time.time,scope_granted=lambda:True):self.store,self.transport,self.now,self.scope_granted=store,transport,now,scope_granted
 def _rows(self):return self.store.config('calendar_create',{})
 def _put(self,x):self.store.put('calendar_create',x)
 def draft(self,value,owner=None):
  required=('summary','start','end','timezone')
  if not isinstance(value,dict) or any(not isinstance(value.get(k),str) or not value[k] for k in required) or value['start']>=value['end']:raise CalendarError('Invalid event draft.')
  if owner is not None and (not isinstance(owner,str) or not owner):raise CalendarError('Draft owner is invalid.')
  payload={k:value.get(k,'') for k in ('summary','start','end','timezone','location','description')};ident=str(uuid.uuid4());digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();rows=self._rows();rows[ident]={'id':ident,'payload':payload,'hash':digest,'owner':owner,'state':'awaiting-approval'};self._put(rows);return self.preview(ident,owner)
 def preview(self,ident,owner=None):
  row=self._rows().get(ident)
  if not row or (owner is not None and row.get('owner') not in (None,owner)):raise CalendarError('Draft not found.')
  return {'id':ident,'payload':dict(row['payload']),'state':row['state']}
 def status(self,ident,owner=None):
  row=self._rows().get(ident)
  if not row or (owner is not None and row.get('owner') not in (None,owner)):raise CalendarError('Draft not found.')
  if row.get('state')=='approved' and self.now()>row.get('expires',0):
   rows=self._rows();row['state']='expired';rows[ident]=row;self._put(rows)
  return {'id':ident,'state':row['state'],'payload_hash':row['hash'],'result':dict(row.get('result',{})),'error_class':row.get('error_class','')}
 def approve(self,ident,owner):
  rows=self._rows();row=rows.get(ident)
  if not row or not isinstance(owner,str) or not owner or row.get('owner') not in (None,owner):raise CalendarError('Approval is invalid.')
  if row['state']!='awaiting-approval':raise CalendarError('Draft cannot be approved.')
  row.update(state='approved',owner=owner,approval=secrets.token_urlsafe(16),approval_hash=row['hash'],expires=self.now()+900);rows[ident]=row;self._put(rows);return {'approval_id':row['approval'],'payload_hash':row['hash']}
 def create(self,ident,approval,owner):
  rows=self._rows();row=rows.get(ident)
  if not row or row.get('owner')!=owner or row.get('approval')!=approval or row.get('state') not in ('approved','created') or self.now()>row.get('expires',0):
   if row and row.get('state')=='approved':row['state']='expired';rows[ident]=row;self._put(rows)
   raise CalendarError('Exact approval is required.')
  if row['state']=='created':return dict(row['result'])
  digest=hashlib.sha256(json.dumps(row['payload'],sort_keys=True).encode()).hexdigest()
  if digest!=row.get('hash') or digest!=row.get('approval_hash'):
   row['state']='failed';row['error_class']='payload-changed';rows[ident]=row;self._put(rows);raise CalendarError('Calendar draft changed after approval.')
  if not self.scope_granted():
   row['state']='failed';row['error_class']='scope-denied';rows[ident]=row;self._put(rows);raise CalendarError('Calendar scope is not granted.')
  try:result=self.transport('/calendars/primary/events',row['payload'],{'Idempotency-Key':hashlib.sha256((approval+row['hash']).encode()).hexdigest()})
  except Exception:
   row['state']='failed';row['error_class']='transport-error';rows[ident]=row;self._put(rows);raise CalendarError('Calendar create failed.')
  if not isinstance(result,dict) or not isinstance(result.get('id'),str) or not result['id']:
   row['state']='failed';row['error_class']='malformed-response';rows[ident]=row;self._put(rows);raise CalendarError('Calendar create failed.')
  row.update(state='created',result={'id':result['id'],'summary':row['payload']['summary']});rows[ident]=row;self._put(rows);return dict(row['result'])
