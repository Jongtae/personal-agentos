"""Read-only Google Drive adapter with a narrow, injectable transport."""
from urllib.parse import urlencode

DRIVE_READONLY='https://www.googleapis.com/auth/drive.readonly'

class GoogleDrive:
 def __init__(self,transport,token): self.transport,self.token=transport,token
 def search(self,query):
  data=self.transport('https://www.googleapis.com/drive/v3/files?'+urlencode({'q':"name contains '"+query.replace("'","\\'")+"'",'fields':'files(id,name,mimeType,modifiedTime)','pageSize':20}),None,{'Authorization':'Bearer '+self.token})
  return [{'id':x['id'],'name':x.get('name',''),'mime_type':x.get('mimeType',''),'modified_time':x.get('modifiedTime','')} for x in data.get('files',[])]
 def read(self,file_id):
  if not isinstance(file_id,str) or not file_id: raise ValueError('파일을 확인하세요.')
  return self.transport('https://www.googleapis.com/drive/v3/files/'+file_id+'?alt=media',None,{'Authorization':'Bearer '+self.token})
