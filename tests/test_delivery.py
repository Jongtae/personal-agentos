import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from personal_agent.delivery import CommandRunner, DeliveryController, DeliveryPlan, StateStore, classify_failure


class Runner:
    def __init__(self, results=None):self.calls=[];self.results=list(results or [])
    def run(self,args,cwd=None,timeout=900):
        self.calls.append((list(args),Path(cwd) if cwd else None))
        return self.results.pop(0) if self.results else SimpleNamespace(returncode=0,stdout='',stderr='')


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'repo';self.root.mkdir()
        plan=Path(__file__).parents[1]/'delivery-plan.yaml';(self.root/'delivery-plan.yaml').write_text(plan.read_text())
        self.state=self.root/'state.json';self.clock=[1_700_000_000]
    def tearDown(self):self.temp.cleanup()
    def controller(self, runner):return DeliveryController(self.root,self.state,runner,now=lambda:self.clock[0])

    def test_plan_starts_at_live_gate_and_uses_repair_when_blocked(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        self.assertEqual(plan.select({})['id'],'P1-01')
        self.assertEqual(plan.select({'blocked':'P1-01'})['id'],'P1-01a')
        self.assertEqual(plan.select({'completed':['P1-01','P1-01a']})['id'],'P1-01b')
        self.assertEqual(plan.select({'completed':['P1-01','P1-01a','P1-01b']})['id'],'P1-02')
        self.assertEqual(plan.select({'completed':['P1-01','P1-01a','P1-01b','P1-02'],'blocked':'P1-02'})['id'],'P1-03')

    def test_authenticated_git_push_uses_login_shell_credentials(self):
        completed=SimpleNamespace(returncode=0,stdout='',stderr='')
        with patch('personal_agent.delivery.subprocess.run',return_value=completed) as run:
            CommandRunner().run(['git','push','-u','origin','delivery/p6-01'])
        args=run.call_args.args[0]
        self.assertEqual(args[:4],['zsh','-ic','source "$HOME/.zshrc" >/dev/null 2>&1; command "$@"','agentos-auth'])
        self.assertEqual(args[4:],['git','push','-u','origin','delivery/p6-01'])

    def test_worker_startup_failures_are_not_misclassified_as_product_validation(self):
        self.assertEqual(classify_failure('spawn codex ENOENT'),'worker-unavailable')
        self.assertEqual(classify_failure('codex: unexpected argument --full-auto'),'worker-incompatible')

    def test_rate_limit_is_blocked_with_six_hour_retry_and_no_secret(self):
        runner=Runner([SimpleNamespace(returncode=1,stdout='',stderr='HTTP 429 rate limit')])
        result=self.controller(runner).run_once(dry_run=True)
        self.assertEqual(result['status'],'blocked-external-rate-limit')
        self.assertEqual(result['next_retry_at'],self.clock[0]+21600)
        self.assertNotIn('token',json.dumps(result).lower())
        self.assertEqual(StateStore(self.state).read()['attempts_today'],1)

    def test_retry_cap_waits_until_next_day_without_running_validation(self):
        day='2023-11-14';StateStore(self.state).write({'active':'P1-01','blocked':'P1-01','status':'blocked-external-rate-limit','attempt_day':day,'attempts_today':4,'next_retry_at':0})
        runner=Runner([SimpleNamespace(returncode=0,stdout='OPEN\n',stderr='')])
        result=self.controller(runner).run_once(dry_run=True)
        self.assertEqual(result['attempts_today'],4)
        self.assertEqual(len(runner.calls),0)

    def test_closed_repair_issue_is_recorded_without_touching_worktree(self):
        StateStore(self.state).write({'blocked':'P1-01'})
        runner=Runner([SimpleNamespace(returncode=0,stdout='CLOSED\n',stderr='')])
        result=self.controller(runner).run_once()
        self.assertIn('P1-01a',result['completed'])
        self.assertFalse((self.root/'worktrees').exists())

    def test_reconcile_adopts_a_closed_active_issue_then_selects_schedule_repair(self):
        StateStore(self.state).write({'active':'P1-01a','completed':['P1-01'],'issues':{'P1-01a':10}})
        runner=Runner([SimpleNamespace(returncode=0,stdout='CLOSED\n',stderr='')])
        result=self.controller(runner).reconcile()
        self.assertEqual(result['completed'],['P1-01','P1-01a'])
        self.assertEqual(self.controller(Runner()).status()['active'],'P1-01b')

    def test_timeout_is_recorded_and_never_leaves_running_state(self):
        class TimeoutRunner:
            def run(self, args, cwd=None, timeout=900):
                raise __import__('subprocess').TimeoutExpired(args,timeout)
        result=self.controller(TimeoutRunner()).run_once(dry_run=True)
        self.assertEqual(result['status'],'blocked-delivery-timeout')
        self.assertEqual(result['active'],'P1-01')
        self.assertIn('Timed out after 900 seconds.',result['last_error'])

    def test_github_auth_failure_blocks_before_worker_or_worktree(self):
        StateStore(self.state).write({'active':'P1-01b','completed':['P1-01','P1-01a']})
        runner=Runner([SimpleNamespace(returncode=1,stdout='',stderr='HTTP 401: Bad credentials')])
        result=self.controller(runner).run_once()
        self.assertEqual(result['status'],'blocked-blocked-approval')
        self.assertEqual(result['active'],'P1-01b')
        self.assertFalse((self.root/'worktrees').exists())

    def test_local_live_validation_does_not_require_github(self):
        plan=json.loads((self.root/'delivery-plan.yaml').read_text())
        plan['iterations']=[{'id':'LOCAL','milestone':'TEST','kind':'live_validation','validation':'python3 verify.py','summary':'local proof'}]
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        (self.root/'verify.py').write_text('print("ok")\n')
        runner=Runner([SimpleNamespace(returncode=0,stdout='ok\n',stderr='')])
        result=self.controller(runner).run_once()
        self.assertEqual(result['completed'],['LOCAL'])
        self.assertEqual(runner.calls[0][0],['python3','verify.py'])

    def test_state_persists_only_delivery_metadata(self):
        saved=StateStore(self.state).write({'active':'P1-01','completed':['P0-01'],'status':'blocked','api_key':'secret','model_response':'private'})
        self.assertEqual(saved,{'active':'P1-01','completed':['P0-01'],'status':'blocked'})

    def test_worker_uses_dedicated_worktree_then_controller_publishes(self):
        (self.root/'.git').mkdir();StateStore(self.state).write({'active':'P1-01a','blocked':'P1-01'})
        ok=lambda stdout='':SimpleNamespace(returncode=0,stdout=stdout,stderr='')
        runner=Runner([ok('OPEN\n'),ok(),ok(),ok(),ok(),ok('https://github.com/Jongtae/personal-agentos/pull/99\n'),ok()])
        result=self.controller(runner).run_once()
        self.assertIn('P1-01a',result['completed'])
        worktree=self.state.parent/'worktrees'/'p1-01a'
        self.assertEqual(runner.calls[2][1],worktree)  # Codex never receives the caller worktree.
        self.assertEqual(runner.calls[2][0][:3],['codex','exec','--approve-for-me'])
        self.assertIn(['gh','pr','merge','https://github.com/Jongtae/personal-agentos/pull/99','--repo','Jongtae/personal-agentos','--squash','--delete-branch'],[call[0] for call in runner.calls])

    def test_launchd_schedule_pins_the_repository_root(self):
        runner=Runner([SimpleNamespace(returncode=0,stdout='',stderr=''),SimpleNamespace(returncode=0,stdout='',stderr=''),SimpleNamespace(returncode=0,stdout='',stderr='')]);home=self.root/'home'
        controller=self.controller(runner)
        with patch.object(Path,'home',return_value=home):
            result=controller.install_schedule()
        content=Path(result['path']).read_text()
        self.assertIn(f'<string>{controller.root}</string>',content)
        self.assertIn('<string>--scheduled</string>',content)
        self.assertIn(f'<string>{controller.state_store.path}</string>',content)
        self.assertIn('<integer>21600</integer>',content)
        self.assertEqual(runner.calls[0][0][1],'bootout')
        self.assertEqual(runner.calls[-1][0][1],'print')

    def test_completed_v1_state_selects_stage_two_without_stale_issue(self):
        completed=[item['id'] for item in DeliveryPlan(self.root/'delivery-plan.yaml').data['iterations'] if item['id']!='P6-01']
        StateStore(self.state).write({'completed':completed,'status':'complete','milestone':'M1','issue':25})
        controller=self.controller(Runner())
        status=controller.status()
        self.assertEqual(status['active'],'P6-01')
        self.assertEqual(status['milestone'],'M6')
        self.assertEqual(status['issue'],55)
        result=controller.run_once(dry_run=True)
        self.assertEqual(result['active'],'P6-01')
        self.assertEqual(result['status'],'ready-for-codex')

    def test_fully_completed_plan_clears_stale_current_iteration_metadata(self):
        completed=[item['id'] for item in DeliveryPlan(self.root/'delivery-plan.yaml').data['iterations']]
        StateStore(self.state).write({'completed':completed,'active':'P5-02','milestone':'M5','issue':25,'status':'running'})
        result=self.controller(Runner()).run_once(dry_run=True)
        self.assertEqual(result['status'],'complete')
        self.assertNotIn('active',result)
        self.assertNotIn('milestone',result)
        self.assertNotIn('issue',result)
        self.assertEqual(self.controller(Runner()).status()['next_action'],'delivery plan complete')

    def test_created_stage_two_issue_uses_its_configured_milestone(self):
        plan=json.loads((self.root/'delivery-plan.yaml').read_text())
        plan['iterations']=[{'id':'P6-99','milestone':'M6','kind':'implementation','summary':'stage two task'}]
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        runner=Runner([SimpleNamespace(returncode=0,stdout='https://github.com/Jongtae/personal-agentos/issues/99\n',stderr='')])
        state={}
        issue=self.controller(runner)._ensure_issue(DeliveryPlan(self.root/'delivery-plan.yaml').items['P6-99'],state,False)
        self.assertEqual(issue,99)
        self.assertIn('Personal AgentOS Stage 2',runner.calls[0][0])

    def test_status_reports_current_iteration(self):
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'P1-01')
        self.assertEqual(result['milestone'],'M1')


if __name__=='__main__':unittest.main()
