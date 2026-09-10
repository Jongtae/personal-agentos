"""Scoped local file workspace: references stay read-only; results are new files."""
from pathlib import Path
import hashlib, json, os, time, uuid

class FileWorkspace:
    def __init__(self, store): self.store=store
    def configure(self, references, workspace):
        refs=[]
        for value in references:
            path=Path(value).resolve()
            if not path.is_dir(): raise ValueError('참고 폴더를 찾을 수 없습니다.')
            refs.append({'id':str(uuid.uuid4()),'path':str(path)})
        target=Path(workspace).resolve()
        if not target.is_dir(): raise ValueError('관리 작업공간을 찾을 수 없습니다.')
        self.store.put('file_workspace',{'references':refs,'workspace':str(target)})
        return self.status()
    def status(self): return self.store.config('file_workspace',{'references':[],'workspace':None})
    def _reference(self, ref_id, relative):
        root=next((x for x in self.status()['references'] if x['id']==ref_id),None)
        if not root: raise ValueError('허용된 참고 폴더가 아닙니다.')
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts: raise ValueError('허용하지 않은 파일 경로입니다.')
        resolved=(Path(root['path'])/path).resolve()
        if not resolved.is_relative_to(Path(root['path'])) or resolved.is_symlink() or resolved.suffix.lower() not in ('.txt','.md') or not resolved.is_file(): raise ValueError('참고 폴더 밖 또는 지원하지 않는 파일입니다.')
        return resolved
    def read(self, ref_id, relative):
        path=self._reference(ref_id,relative); content=path.read_text(encoding='utf-8')
        return {'reference_id':ref_id,'path':relative,'version':hashlib.sha256(content.encode()).hexdigest(),'content':content}
    def save(self, request_id, title, content, sources):
        state=self.status(); root=Path(state.get('workspace') or '')
        if not root.is_dir(): raise ValueError('관리 작업공간을 먼저 연결하세요.')
        if not request_id or not content.strip(): raise ValueError('저장 요청과 내용이 필요합니다.')
        with self.store.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS file_workspace_results(id TEXT PRIMARY KEY, request_id TEXT UNIQUE, path TEXT UNIQUE, content_hash TEXT, sources TEXT, created REAL)')
            old=db.execute('SELECT * FROM file_workspace_results WHERE request_id=?',(request_id,)).fetchone()
            if old:return dict(old)
            safe=''.join(c if c.isalnum() or c in ' -_' else '-' for c in title).strip()[:80] or 'result'
            target=root/(safe+'.md'); suffix=1
            while target.exists(): suffix+=1;target=root/(safe+f'-{suffix}.md')
            body=content.rstrip()+'\n\n---\nSources:\n'+''.join(f'- {s["path"]} @ {s["version"]}\n' for s in sources)
            temp=target.with_name(target.name+'.tmp-'+uuid.uuid4().hex); temp.write_text(body,encoding='utf-8'); os.replace(temp,target)
            record={'id':str(uuid.uuid4()),'request_id':request_id,'path':target.name,'content_hash':hashlib.sha256(body.encode()).hexdigest(),'sources':json.dumps(sources),'created':time.time()}
            db.execute('INSERT INTO file_workspace_results VALUES (:id,:request_id,:path,:content_hash,:sources,:created)',record)
            return record
