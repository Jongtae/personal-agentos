import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from personal_agent.delivery import DeliveryController, DeliveryPlan, StateStore


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
        self.assertEqual(plan.select({'completed':['P1-01','P1-01a']})['id'],'P1-02')

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
        self.assertIn(['gh','pr','merge','https://github.com/Jongtae/personal-agentos/pull/99','--squash','--delete-branch'],[call[0] for call in runner.calls])

    def test_launchd_schedule_pins_the_repository_root(self):
        runner=Runner([SimpleNamespace(returncode=0,stdout='',stderr='')]);home=self.root/'home'
        controller=self.controller(runner)
        with patch.object(Path,'home',return_value=home):
            result=controller.install_schedule()
        content=Path(result['path']).read_text()
        self.assertIn(f'<string>{controller.root}</string>',content)
        self.assertIn('<integer>21600</integer>',content)

    def test_status_reports_current_iteration(self):
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'P1-01')
        self.assertEqual(result['milestone'],'M1')


if __name__=='__main__':unittest.main()
