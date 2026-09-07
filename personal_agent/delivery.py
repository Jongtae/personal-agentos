"""Evidence-driven local delivery controller for the Personal AgentOS repository."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from xml.sax.saxutils import escape as xml_escape
from types import SimpleNamespace

RETRY_SECONDS = 6 * 60 * 60
DAILY_LIMIT = 4


class DeliveryError(RuntimeError):
    pass


def default_state_path():
    override=os.environ.get('AGENTOS_DELIVERY_STATE')
    if override:return Path(override).expanduser()
    return Path.home()/'Library'/'Application Support'/'personal-agentos-delivery'/'state.json'


class StateStore:
    def __init__(self, path=None):
        self.path=Path(path or default_state_path())
        self.lock_path=self.path.with_suffix('.lock')

    def read(self):
        try:
            value=json.loads(self.path.read_text())
            return value if isinstance(value,dict) else {}
        except FileNotFoundError:return {}
        except (ValueError,OSError):return {'status':'invalid-state','last_error':'Delivery state could not be read.'}

    def write(self, value):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        safe={key:value[key] for key in ('active','completed','blocked','status','milestone','issue','issues','last_validation','last_error','next_retry_at','attempt_day','attempts_today','pr','release','updated_at') if key in value}
        with tempfile.NamedTemporaryFile('w',dir=self.path.parent,delete=False) as handle:
            json.dump(safe,handle,ensure_ascii=False,sort_keys=True)
            handle.write('\n');name=handle.name
        os.chmod(name,0o600);os.replace(name,self.path)
        return safe

    def locked(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        handle=self.lock_path.open('a')
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close();raise DeliveryError('A delivery loop is already running.')
        return handle


class DeliveryPlan:
    def __init__(self, path):
        try:data=json.loads(Path(path).read_text())
        except (OSError,ValueError) as exc:raise DeliveryError('delivery-plan.yaml must contain valid JSON-compatible YAML.') from exc
        if not isinstance(data,dict) or not isinstance(data.get('iterations'),list):raise DeliveryError('delivery plan has no iterations.')
        self.data=data
        self.items={item['id']:item for item in data['iterations'] if isinstance(item,dict) and isinstance(item.get('id'),str)}
        if len(self.items)!=len(data['iterations']):raise DeliveryError('Each delivery iteration needs a unique id.')
        self.milestones=data.get('milestones',{}) if isinstance(data.get('milestones',{}),dict) else {}

    def milestone_title(self, item):
        configured=self.milestones.get(item.get('milestone'),{})
        if isinstance(configured,dict) and isinstance(configured.get('title'),str):return configured['title']
        title=item.get('milestone_title')
        return title if isinstance(title,str) else None

    def select(self, state):
        completed=set(state.get('completed',[])) if isinstance(state.get('completed'),list) else set()
        active=state.get('active')
        if active in self.items and active not in completed:return self.items[active]
        blocked=state.get('blocked')
        if blocked in self.items and blocked not in completed:
            repair=next((item for item in self.items.values() if item.get('repair_of')==blocked and item['id'] not in completed),None)
            if repair:return repair
            return self.items[blocked]
        for item in self.data['iterations']:
            if item['id'] in completed:continue
            deps=item.get('depends_on',[])
            if all(dep in completed for dep in deps):return item
        return None


class CommandRunner:
    def run(self, args, cwd=None, timeout=900):
        try:
            # launchd and GUI-launched Python do not inherit the interactive
            # shell credentials.  Let gh load the user's normal shell setup
            # while every other delivery command stays non-interactive.
            if args and (args[0]=='gh' or args[:2]==['git','push']):
                args=['zsh','-ic','source "$HOME/.zshrc" >/dev/null 2>&1; command "$@"','agentos-auth',*args]
            return subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout=exc.stdout.decode() if isinstance(exc.stdout,bytes) else (exc.stdout or '')
            stderr=exc.stderr.decode() if isinstance(exc.stderr,bytes) else (exc.stderr or '')
            return SimpleNamespace(returncode=124,stdout=stdout,stderr=f'{stderr}\nTimed out after {timeout} seconds.')
        except OSError as exc:
            return SimpleNamespace(returncode=127,stdout='',stderr=f'Could not start {args[0]}: {exc}')


def classify_failure(text):
    lowered=(text or '').lower()
    if 'timed out' in lowered or 'timeout' in lowered:return 'delivery-timeout'
    if any(term in lowered for term in ('429','rate limit','quota','free model')):return 'external-rate-limit'
    if any(term in lowered for term in ('oauth','authorization','permission','forbidden','401','403')):return 'blocked-approval'
    if 'enoent' in lowered and 'codex' in lowered:return 'worker-unavailable'
    if 'unexpected argument' in lowered and 'codex' in lowered:return 'worker-incompatible'
    return 'validation-failed'


class DeliveryController:
    def __init__(self, root=None, state_path=None, runner=None, now=None):
        self.root=Path(root or Path.cwd()).resolve()
        configured_plan=self.root/'delivery-plan.yaml'
        packaged_plan=Path(__file__).with_name('delivery-plan.yaml')
        self.plan=DeliveryPlan(configured_plan if configured_plan.exists() else packaged_plan)
        self.state_store=StateStore(state_path)
        self.runner=runner or CommandRunner()
        self.now=now or time.time

    def status(self):
        state=self.state_store.read();item=self.plan.select(state)
        return {**state,'active':item and item['id'],'milestone':item and item['milestone'],
                'issue':item and self._issue_number(item,state),'summary':item and item['summary'],
                'next_action':'wait for retry' if state.get('status','').startswith('blocked') else ('run current iteration' if item else 'delivery plan complete')}

    def due(self, state):
        return not state.get('next_retry_at') or self.now()>=state['next_retry_at']

    def _attempt_allowed(self, state):
        day=dt.datetime.fromtimestamp(self.now(),dt.timezone.utc).date().isoformat()
        attempts=state.get('attempts_today',0) if state.get('attempt_day')==day else 0
        return attempts<DAILY_LIMIT,day,attempts

    def _gh(self, *args):
        return self._command(['gh',*args],cwd=self.root,timeout=60)

    def _command(self, args, cwd=None, timeout=900):
        """Run every child process through one bounded, non-throwing boundary."""
        try:
            return self.runner.run(args,cwd=cwd,timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout=exc.stdout.decode() if isinstance(exc.stdout,bytes) else (exc.stdout or '')
            stderr=exc.stderr.decode() if isinstance(exc.stderr,bytes) else (exc.stderr or '')
            return SimpleNamespace(returncode=124,stdout=stdout,stderr=f'{stderr}\nTimed out after {timeout} seconds.')
        except OSError as exc:
            return SimpleNamespace(returncode=127,stdout='',stderr=f'Could not start {args[0]}: {exc}')

    @staticmethod
    def _issue_number(item, state):
        return item.get('issue') or state.get('issues',{}).get(item['id'])

    def _ensure_issue(self, item, state, dry_run):
        issue=self._issue_number(item,state)
        if issue or dry_run:return issue
        title=f'[{item["id"]}] {item["summary"]}'
        args=['issue','create','--repo',self.plan.data['repository'],'--title',title,
              '--body',f'Automated delivery iteration `{item["id"]}` for {item["milestone"]}.\n\n{item["summary"]}',
              '--label','iteration','--label','needs-validation']
        milestone=self.plan.milestone_title(item)
        if milestone:args.extend(['--milestone',milestone])
        result=self._gh(*args)
        found=re.search(r'/issues/(\d+)',result.stdout or '')
        if result.returncode or not found:raise DeliveryError(result.stderr or 'Could not create delivery issue.')
        state.setdefault('issues',{})[item['id']]=int(found.group(1))
        return state['issues'][item['id']]

    def _record_block(self, item, state, classification, detail, dry_run):
        allowed,day,attempts=self._attempt_allowed(state)
        retry_at=self.now()+RETRY_SECONDS if allowed else (dt.datetime.fromtimestamp(self.now(),dt.timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)+dt.timedelta(days=1)).timestamp()
        issue=self._issue_number(item,state)
        state.update(active=item['id'],blocked=item.get('repair_of') or item['id'],milestone=item['milestone'],issue=issue,status='blocked-'+classification,
                     last_validation='failed',last_error=detail[:500],next_retry_at=retry_at,attempt_day=day,attempts_today=attempts+1,updated_at=self.now())
        if issue and not dry_run:
            self._gh('issue','edit',str(issue),'--repo',self.plan.data['repository'],'--add-label','blocked')
            self._gh('issue','comment',str(issue),'--repo',self.plan.data['repository'],'--body',f'Delivery loop blocked: `{classification}`. Retry is scheduled after {dt.datetime.fromtimestamp(retry_at,dt.timezone.utc).isoformat()}. Validation detail: {detail[:300]}')
        return self.state_store.write(state)

    def _complete(self, item, state, dry_run=False):
        completed=set(state.get('completed',[]));completed.add(item['id'])
        state.update(completed=sorted(completed),active=None,status='completed',last_validation='passed',last_error='',next_retry_at=None,updated_at=self.now())
        if state.get('blocked')==item['id']:state.pop('blocked',None)
        issue=self._issue_number(item,state)
        if issue and not dry_run:
            self._gh('issue','close',str(issue),'--repo',self.plan.data['repository'],'--comment',f'Delivery loop completed `{item["id"]}` with recorded validation evidence.')
        return self.state_store.write(state)

    def _issue_is_closed(self, item, state):
        issue=self._issue_number(item,state)
        if not issue:return False
        result=self._gh('issue','view',str(issue),'--repo',self.plan.data['repository'],'--json','state','--jq','.state')
        if result.returncode:
            raise DeliveryError(result.stderr or 'Could not read delivery issue status.')
        return result.returncode==0 and result.stdout.strip()=='CLOSED'

    @staticmethod
    def _complete_plan(state, now):
        state={**state}
        for key in ('active','milestone','issue','pr','release','blocked','next_retry_at'):
            state.pop(key,None)
        state.update(status='complete',last_validation=state.get('last_validation','passed'),updated_at=now)
        return state

    def reconcile(self, dry_run=False):
        """Adopt a GitHub-closed active iteration without starting new work."""
        lock=self.state_store.locked()
        try:
            state=self.state_store.read();item=self.plan.select(state)
            if not item:return self.state_store.write(self._complete_plan(state,self.now()))
            issue=self._issue_number(item,state)
            if not issue:
                return self.state_store.write({**state,'status':'ready-to-run','updated_at':self.now()})
            try:
                if self._issue_is_closed(item,state):
                    return self._complete(item,state,dry_run=True)
            except DeliveryError as exc:
                return self._record_block(item,state,classify_failure(str(exc)),str(exc),dry_run)
            return self.state_store.write({**state,'active':item['id'],'milestone':item['milestone'],'issue':issue,'status':'ready-to-run','updated_at':self.now()})
        finally:
            lock.close()

    def run_once(self, dry_run=False, scheduled=False):
        lock=self.state_store.locked()
        try:
            state=self.state_store.read();item=self.plan.select(state)
            if not item:return self.state_store.write(self._complete_plan(state,self.now()))
            # A local validation can establish its evidence without GitHub.
            # This is essential for launchd's intentionally minimal runtime
            # environment and makes local acceptance usable offline.
            issue=self._issue_number(item,state)
            if issue or item['kind']!='live_validation':
                try:
                    issue=self._ensure_issue(item,state,dry_run)
                except DeliveryError as exc:
                    return self._record_block(item,state,classify_failure(str(exc)),str(exc),dry_run)
            if issue:state['issues']=dict(state.get('issues',{}),**{item['id']:issue})
            # Launchd has no interactive GitHub credential context. A live
            # validation must record its local evidence before any optional
            # GitHub status lookup; only repair implementation work needs the
            # closed-issue shortcut.
            if not dry_run and item['kind']!='live_validation':
                try:
                    if self._issue_is_closed(item,state):return self._complete(item,state,dry_run=True)
                except DeliveryError as exc:
                    return self._record_block(item,state,classify_failure(str(exc)),str(exc),dry_run)
            if state.get('status','').startswith('blocked') and not self.due(state):return self.status()
            allowed,_,_=self._attempt_allowed(state)
            if state.get('status','').startswith('blocked') and not allowed:
                state['next_retry_at']=(dt.datetime.fromtimestamp(self.now(),dt.timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)+dt.timedelta(days=1)).timestamp()
                return self.state_store.write(state)
            state.update(active=item['id'],milestone=item['milestone'],issue=issue,status='running',updated_at=self.now())
            if item['kind']=='live_validation':
                result=self._command(item['validation'].split(),cwd=self.root,timeout=900)
                output=(result.stdout or '')+'\n'+(result.stderr or '')
                if result.returncode:
                    return self._record_block(item,state,classify_failure(output),output,dry_run)
                return self._complete(item,state,dry_run)
            if dry_run:
                state.update(status='ready-for-codex',updated_at=self.now())
                return self.state_store.write(state)
            return self._run_worker(item,state)
        finally:
            lock.close()

    def _run_worker(self, item, state):
        if not (self.root/'.git').exists():return self._record_block(item,state,'delivery-failed','Codex delivery requires a git checkout.',False)
        worktrees=self.state_store.path.parent/'worktrees';worktree=worktrees/item['id'].lower()
        branch='delivery/'+item['id'].lower()
        if not worktree.exists():
            created=self._command(['git','worktree','add','-b',branch,str(worktree),'origin/main'],cwd=self.root,timeout=120)
            if created.returncode:return self._record_block(item,state,classify_failure((created.stdout or '')+'\n'+(created.stderr or '')),created.stderr or 'Could not create delivery worktree.',False)
        definition=json.dumps(item,ensure_ascii=False,sort_keys=True)
        prompt=(f'Implement this delivery iteration definition: {definition}\n'
                'Work only in this worktree. Preserve product safety boundaries. Run listed tests and commit the finished change. Do not push, create a PR, merge, tag, or release; the delivery controller owns those actions.')
        result=self._command(['codex','exec','--approve-for-me',prompt],cwd=worktree,timeout=3600)
        output=(result.stdout or '')+'\n'+(result.stderr or '')
        if result.returncode:return self._record_block(item,state,classify_failure(output),output,False)
        for command in item.get('tests',[]):
            checked=self._command(command.split(),cwd=worktree,timeout=900)
            if checked.returncode:return self._record_block(item,state,'validation-failed',(checked.stdout or '')+'\n'+(checked.stderr or ''),False)
        pushed=self._command(['git','push','-u','origin',branch],cwd=worktree,timeout=180)
        if pushed.returncode:return self._record_block(item,state,'delivery-failed',(pushed.stdout or '')+'\n'+(pushed.stderr or ''),False)
        issue=self._issue_number(item,state)
        body=f'Automated delivery implementation for `{item["id"]}`.\n\nCloses #{issue}.' if issue else f'Automated delivery implementation for `{item["id"]}`.'
        opened=self._gh('pr','create','--repo',self.plan.data['repository'],'--base','main','--head',branch,'--title',f'[{item["id"]}] {item["summary"]}','--body',body)
        match=re.search(r'https://github\.com/[^\s]+/pull/\d+',opened.stdout or '')
        if opened.returncode or not match:return self._record_block(item,state,'delivery-failed',(opened.stdout or '')+'\n'+(opened.stderr or ''),False)
        state['pr']=match.group(0)
        merged=self._gh('pr','merge',state['pr'],'--repo',self.plan.data['repository'],'--squash','--delete-branch')
        if merged.returncode:return self._record_block(item,state,'delivery-failed',(merged.stdout or '')+'\n'+(merged.stderr or ''),False)
        return self._complete(item,state,dry_run=True)

    def _schedule_program(self):
        """Select the same runtime as the selected delivery-plan checkout."""
        if (self.root/'personal_agent'/'quickstart.py').is_file():
            # pyenv interpreters can hang before importing codecs under launchd.
            # The delivery controller path is standard-library-only, so the
            # macOS runtime is a safe source-schedule fallback.
            system_python=Path('/usr/bin/python3')
            return [str(system_python if system_python.is_file() else Path(sys.executable)),'-m','personal_agent.quickstart']
        command=shutil.which('agentos')
        return [command] if command else [sys.executable,'-m','personal_agent.quickstart']

    def install_schedule(self):
        label='com.jongtae.personal-agentos.delivery';folder=Path.home()/'Library'/'LaunchAgents';path=folder/(label+'.plist')
        folder.mkdir(parents=True,exist_ok=True)
        source_mode=(self.root/'personal_agent'/'quickstart.py').is_file()
        args=[*self._schedule_program(),'delivery','run','--once','--scheduled','--root',str(self.root),'--state',str(self.state_store.path)]
        rendered=''.join(f'<string>{xml_escape(str(arg))}</string>' for arg in args)
        # launchd can stall Python while resolving a cloud-synchronised project
        # directory. Source mode imports through PYTHONPATH from a stable cwd.
        working_directory='/' if source_mode else str(self.root)
        environment=(f'<key>EnvironmentVariables</key><dict><key>PYTHONPATH</key><string>{xml_escape(str(self.root))}</string></dict>' if source_mode else '')
        payload=(f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict>'
                 f'<key>Label</key><string>{label}</string><key>ProgramArguments</key><array>{rendered}</array>{environment}'
                 f'<key>WorkingDirectory</key><string>{xml_escape(working_directory)}</string>'
                 f'<key>StartInterval</key><integer>{RETRY_SECONDS}</integer><key>RunAtLoad</key><true/>'
                 f'<key>StandardOutPath</key><string>{xml_escape(str(Path.home()/"Library/Logs/personal-agentos-delivery.log"))}</string>'
                 f'<key>StandardErrorPath</key><string>{xml_escape(str(Path.home()/"Library/Logs/personal-agentos-delivery.error.log"))}</string></dict></plist>')
        path.write_text(payload);os.chmod(path,0o600)
        self._command(['launchctl','bootout',f'gui/{os.getuid()}',str(path)],timeout=30)
        result=self._command(['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],timeout=30)
        if result.returncode:raise DeliveryError(result.stderr or 'Could not install launchd schedule.')
        health=self._command(['launchctl','print',f'gui/{os.getuid()}/{label}'],timeout=30)
        if health.returncode:raise DeliveryError(health.stderr or 'launchd did not register the delivery schedule.')
        return {'scheduled':True,'path':str(path)}

    def uninstall_schedule(self):
        path=Path.home()/'Library'/'LaunchAgents'/'com.jongtae.personal-agentos.delivery.plist'
        self._command(['launchctl','bootout',f'gui/{os.getuid()}',str(path)],timeout=30)
        path.unlink(missing_ok=True);return {'scheduled':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('status','run','reconcile','install-schedule','uninstall-schedule'))
    parser.add_argument('--once',action='store_true');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--scheduled',action='store_true')
    parser.add_argument('--root',default=str(Path.cwd()));parser.add_argument('--state')
    args=parser.parse_args(argv);controller=DeliveryController(args.root,args.state)
    if args.command=='status':result=controller.status()
    elif args.command=='run':result=controller.run_once(args.dry_run,args.scheduled)
    elif args.command=='reconcile':result=controller.reconcile(args.dry_run)
    elif args.command=='install-schedule':result=controller.install_schedule()
    else:result=controller.uninstall_schedule()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
