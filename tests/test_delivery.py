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

    def test_packaged_plan_is_used_when_no_source_checkout_is_present(self):
        installed_root=Path(self.temp.name)/'installed-cli-context';installed_root.mkdir()
        controller=DeliveryController(installed_root,self.state,Runner(),now=lambda:self.clock[0])
        self.assertEqual(controller.status()['active'],'UX-01')
        self.assertEqual(controller.plan.data['repository'],'Jongtae/personal-agentos')

    def test_packaged_delivery_plan_matches_the_repository_plan(self):
        root = Path(__file__).parents[1]
        self.assertEqual(json.loads((root/'personal_agent'/'delivery-plan.yaml').read_text()), json.loads((root/'delivery-plan.yaml').read_text()))

    def test_ux_plan_is_ordered_and_ignores_frozen_legacy_state(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        self.assertEqual(plan.select({})['id'],'UX-01')
        self.assertEqual(plan.select({'completed':['UX-01']})['id'],'UX-02')
        self.assertEqual(plan.select({'completed':['UX-01','UX-02']})['id'],'UX-03')
        self.assertEqual(plan.select({'completed':['UX-01','UX-02','UX-03']})['id'],'UX-04')
        self.assertEqual(plan.select({'active':'P7-03a','blocked':'P7-03a'})['id'],'UX-01')

    def test_stale_frozen_delivery_state_is_migrated_without_waiting_for_retry(self):
        StateStore(self.state).write({'active':'P7-03a','blocked':'P7-03a','milestone':'M7','issue':94,'pr':'https://example.test/pr','release':'v1.0.4','next_retry_at':self.clock[0]+21600,'last_error':'old model content','status':'blocked-validation-failed'})
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'UX-01')
        self.assertEqual(result['status'],'ready-to-run')
        self.assertNotIn('next_retry_at',result)
        self.assertNotIn('last_error',result)
        self.assertEqual(result['last_validation'],'migrated-plan')
        persisted=StateStore(self.state).read()
        self.assertEqual(persisted['status'],'ready-to-run')
        self.assertNotIn('next_retry_at',persisted)

    def test_closed_ux05_state_reconciles_to_next_mp2_selection(self):
        StateStore(self.state).write({'active':'UX-05','blocked':'UX-05','completed':['UX-01','UX-02','UX-03','UX-03a','UX-04'],'status':'blocked-validation-failed','next_retry_at':self.clock[0]+21600,'last_error':'historical failure'})
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'OP-01')
        self.assertEqual(result['status'],'reconciled-documentation')
        self.assertIsNone(result['next_goal'])
        self.assertEqual(result['next_action'],'run current iteration')
        self.assertIn('D-MP2-01',result['completed'])
        persisted=StateStore(self.state).read()
        self.assertNotIn('active',persisted);self.assertNotIn('blocked',persisted);self.assertNotIn('next_retry_at',persisted)

    def test_merged_documented_iteration_clears_active_state_and_exposes_review_gate(self):
        StateStore(self.state).write({'active':'I-MP2-01','milestone':'AgentOS Conversation-First Settings','issue':234,'status':'complete'})
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'OP-01')
        self.assertEqual(result['status'],'reconciled-documentation')
        self.assertIn('I-MP2-01',result['completed'])
        self.assertIsNone(result['next_goal'])

    def test_reconciled_documentation_state_adopts_later_documented_closeout(self):
        StateStore(self.state).write({'completed':['D-MP2-01'],'status':'complete','last_validation':'migrated-documentation'})
        result=self.controller(Runner()).status()
        self.assertIn('I-MP2-01',result['completed'])
        self.assertEqual(result['active'],'OP-01')

    def test_valid_ux_block_is_not_migrated(self):
        StateStore(self.state).write({'active':'UX-02','blocked':'UX-02','status':'blocked-validation-failed','next_retry_at':self.clock[0]+21600})
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'UX-02')
        self.assertEqual(result['next_action'],'wait for retry')

    def test_authenticated_git_push_uses_login_shell_credentials(self):
        completed=SimpleNamespace(returncode=0,stdout='',stderr='')
        with patch('personal_agent.delivery.subprocess.run',return_value=completed) as run:
            CommandRunner().run(['git','push','-u','origin','delivery/p6-01'])
        args=run.call_args.args[0]
        self.assertEqual(args[:4],['zsh','-ic','source "$HOME/.zshrc" >/dev/null 2>&1; unset GITHUB_TOKEN GH_TOKEN; command "$@"','agentos-auth'])
        self.assertEqual(args[4:],['git','push','-u','origin','delivery/p6-01'])

    def test_github_api_uses_keyring_without_loading_shell_tokens(self):
        completed=SimpleNamespace(returncode=0,stdout='',stderr='')
        with patch('personal_agent.delivery.subprocess.run',return_value=completed) as run:
            CommandRunner().run(['gh','issue','view','111'])
        self.assertEqual(run.call_args.args[0],['gh','issue','view','111'])
        self.assertNotIn('GITHUB_TOKEN',run.call_args.kwargs['env'])
        self.assertNotIn('GH_TOKEN',run.call_args.kwargs['env'])

    def test_worker_startup_failures_are_not_misclassified_as_product_validation(self):
        self.assertEqual(classify_failure('spawn codex ENOENT'),'worker-unavailable')
        self.assertEqual(classify_failure('codex: unexpected argument --full-auto'),'worker-incompatible')

    def test_rate_limit_is_blocked_with_six_hour_retry_and_no_secret(self):
        plan={'repository':'Jongtae/personal-agentos','iterations':[{'id':'LIVE','milestone':'H0','kind':'live_validation','validation':'python3 verify.py','summary':'live proof'}]}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        runner=Runner([SimpleNamespace(returncode=1,stdout='',stderr='HTTP 429 rate limit')])
        result=self.controller(runner).run_once(dry_run=True)
        self.assertEqual(result['status'],'blocked-external-rate-limit')
        self.assertEqual(result['next_retry_at'],self.clock[0]+21600)
        self.assertNotIn('token',json.dumps(result).lower())
        self.assertEqual(StateStore(self.state).read()['attempts_today'],1)

    def test_retry_cap_waits_until_next_day_without_running_validation(self):
        day='2023-11-14';StateStore(self.state).write({'active':'UX-01','blocked':'UX-01','status':'blocked-external-rate-limit','attempt_day':day,'attempts_today':4,'next_retry_at':0})
        runner=Runner([SimpleNamespace(returncode=0,stdout='OPEN\n',stderr='')])
        result=self.controller(runner).run_once(dry_run=True)
        self.assertEqual(result['attempts_today'],4)
        self.assertEqual(len(runner.calls),0)

    def test_closed_current_issue_is_recorded_without_touching_worktree(self):
        StateStore(self.state).write({'active':'UX-01','issues':{'UX-01':103}})
        runner=Runner([SimpleNamespace(returncode=0,stdout='CLOSED\n',stderr='')])
        result=self.controller(runner).run_once()
        self.assertIn('UX-01',result['completed'])
        self.assertFalse((self.root/'worktrees').exists())

    def test_reconcile_adopts_closed_ux_issue_then_selects_next_iteration(self):
        StateStore(self.state).write({'active':'UX-01','issues':{'UX-01':103}})
        runner=Runner([SimpleNamespace(returncode=0,stdout='CLOSED\n',stderr='')])
        result=self.controller(runner).reconcile()
        self.assertEqual(result['completed'],['UX-01'])
        self.assertEqual(result['active'],'UX-02')
        self.assertEqual(result['status'],'ready-to-run')
        self.assertEqual(self.controller(Runner()).status()['active'],'UX-02')

    def test_timeout_is_recorded_and_never_leaves_running_state(self):
        plan={'repository':'Jongtae/personal-agentos','iterations':[{'id':'LIVE','milestone':'H0','kind':'live_validation','validation':'python3 verify.py','summary':'live proof'}]}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        class TimeoutRunner:
            def run(self, args, cwd=None, timeout=900):
                raise __import__('subprocess').TimeoutExpired(args,timeout)
        result=self.controller(TimeoutRunner()).run_once(dry_run=True)
        self.assertEqual(result['status'],'blocked-delivery-timeout')
        self.assertEqual(result['active'],'LIVE')
        self.assertIn('Timed out after 900 seconds.',result['last_error'])

    def test_github_auth_failure_blocks_before_worker_or_worktree(self):
        StateStore(self.state).write({'active':'UX-01','issues':{'UX-01':103}})
        runner=Runner([SimpleNamespace(returncode=1,stdout='',stderr='HTTP 401: Bad credentials')])
        result=self.controller(runner).run_once()
        self.assertEqual(result['status'],'blocked-blocked-approval')
        self.assertEqual(result['active'],'UX-01')
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
        (self.root/'.git').mkdir();StateStore(self.state).write({'active':'UX-02','completed':['UX-01'],'issues':{'UX-02':104}})
        ok=lambda stdout='':SimpleNamespace(returncode=0,stdout=stdout,stderr='')
        runner=Runner([ok('OPEN\n'),ok(),ok(),ok(),ok(),ok('https://github.com/Jongtae/personal-agentos/pull/99\n'),ok()])
        result=self.controller(runner).run_once()
        self.assertIn('UX-02',result['completed'])
        worktree=self.state.parent/'worktrees'/'ux-02'
        self.assertEqual(runner.calls[2][1],worktree)
        self.assertEqual(runner.calls[2][0][:3],['codex','exec','--approve-for-me'])
        self.assertIn(['gh','pr','merge','https://github.com/Jongtae/personal-agentos/pull/99','--repo','Jongtae/personal-agentos','--squash','--delete-branch'],[call[0] for call in runner.calls])

    def test_launchd_schedule_pins_the_repository_root_and_source_runtime(self):
        runner=Runner([SimpleNamespace(returncode=0,stdout='',stderr=''),SimpleNamespace(returncode=0,stdout='',stderr=''),SimpleNamespace(returncode=0,stdout='',stderr='')]);home=self.root/'home'
        (self.root/'personal_agent').mkdir();(self.root/'personal_agent'/'quickstart.py').write_text('')
        controller=self.controller(runner)
        with patch.object(Path,'home',return_value=home):
            result=controller.install_schedule()
        content=Path(result['path']).read_text()
        self.assertIn(str(controller.root),content)
        self.assertIn('<key>WorkingDirectory</key><string>/</string>',content)
        self.assertNotIn('<key>PYTHONPATH</key>',content)
        self.assertIn('<string>/usr/bin/python3</string><string>-c</string>',content)
        self.assertIn('sys.path.insert(0',content)
        self.assertIn('--scheduled',content)
        self.assertIn(str(controller.state_store.path),content)
        self.assertIn('<integer>21600</integer>',content)
        self.assertEqual(runner.calls[0][0][1],'bootout')
        self.assertEqual(runner.calls[-1][0][1],'print')

    def test_frozen_p7_state_cannot_be_selected_by_ux_plan(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        self.assertNotIn('P7-03a',plan.items)
        self.assertEqual(plan.select({'active':'P7-04','blocked':'P7-03a'})['id'],'UX-01')

    def test_ux_plan_requires_each_predecessor(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        completed=['UX-01','UX-02','UX-03','UX-04']
        self.assertEqual(plan.select({'completed':completed})['id'],'UX-03a')
        completed.append('UX-03a')
        self.assertEqual(plan.select({'completed':completed})['id'],'UX-05')
        completed.append('UX-05')
        self.assertEqual(plan.select({'completed':completed})['id'],'UX-06')
        completed.append('UX-06')
        self.assertEqual(plan.select({'completed':completed})['id'],'MP1-D-01')
        completed.append('MP1-D-01')
        expected=('MP1-I-01','MP1-D-02','MP1-I-02','MP1-D-03','MP1-I-03','MP1-D-04','MP1-I-04','MP1-D-05','MP1-I-05','MP1-D-06','MP1-I-06','MP1-R-01','MP1-R-02','MP1-R-03','MP1-R-04','MP1-R-05','D-MP2-01','I-MP2-01','D-MP2-02','I-MP2-02','D-MP2-03','I-MP2-03')
        for iteration in expected:
            self.assertEqual(plan.select({'completed':completed})['id'],iteration)
            completed.append(iteration)
        self.assertEqual(plan.select({'completed':completed})['id'],'STAB-01')
        completed.append('STAB-01')
        self.assertEqual(plan.select({'completed':completed})['id'],'OP-01')
        completed.append('OP-01')
        self.assertIsNone(plan.select({'completed':completed}))

    def test_ux_plan_keeps_release_before_post_release_conversation_iteration(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        release=plan.items['UX-05']
        follow_up=plan.items['UX-06']
        self.assertEqual(release['kind'],'release')
        self.assertEqual(follow_up['depends_on'],['UX-05'])
        completed=[item['id'] for item in plan.data['iterations']]
        StateStore(self.state).write({'completed':completed,'active':'P7-04','status':'running'})
        result=self.controller(Runner()).run_once(dry_run=True)
        self.assertEqual(result['status'],'complete')
        self.assertNotIn('active',result)

    def test_release_preflight_blocks_before_release_mutations(self):
        plan={'repository':'Jongtae/personal-agentos','iterations':[{'id':'REL','milestone':'TEST','kind':'release','release_validation':['python3 verify.py'],'summary':'release'}]}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan));(self.root/'.git').mkdir()
        runner=Runner([SimpleNamespace(returncode=1,stdout='',stderr='Telegram acceptance not complete')])
        result=self.controller(runner)._run_release(DeliveryPlan(self.root/'delivery-plan.yaml').items['REL'],{})
        self.assertEqual(result['status'],'blocked-validation-failed')
        self.assertEqual(runner.calls[0][0],['python3','verify.py'])
        self.assertEqual(len(runner.calls),1)

    def test_patch_release_version_helpers(self):
        self.assertEqual(DeliveryController._next_patch_version('1.0.3'),'1.0.4')
        with self.assertRaises(Exception):DeliveryController._next_patch_version('1.0')

    def test_completed_hub_state_selects_ux_without_stale_issue(self):
        StateStore(self.state).write({'completed':['P1-01','P7-03'],'status':'complete','milestone':'M7','issue':94})
        controller=self.controller(Runner())
        status=controller.status()
        self.assertEqual(status['active'],'UX-01')
        self.assertEqual(status['milestone'],'AgentOS UX v1.1')
        self.assertEqual(status['issue'],150)

    def test_fully_completed_plan_clears_stale_current_iteration_metadata(self):
        completed=[item['id'] for item in DeliveryPlan(self.root/'delivery-plan.yaml').data['iterations']]
        StateStore(self.state).write({'completed':completed,'active':'P5-02','milestone':'M5','issue':25,'status':'running'})
        result=self.controller(Runner()).run_once(dry_run=True)
        self.assertEqual(result['status'],'complete')
        self.assertNotIn('active',result)
        self.assertNotIn('milestone',result)
        self.assertNotIn('issue',result)
        self.assertEqual(self.controller(Runner()).status()['next_action'],'complete the credential-free owner-approved operating deployment preparation cycle')

    def test_created_ux_issue_uses_its_configured_milestone(self):
        plan=json.loads((self.root/'delivery-plan.yaml').read_text())
        plan['iterations']=[{'id':'UX-99','milestone':'AgentOS UX v1.1','kind':'implementation','summary':'UX task'}]
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        runner=Runner([SimpleNamespace(returncode=0,stdout='https://github.com/Jongtae/personal-agentos/issues/99\n',stderr='')])
        state={}
        issue=self.controller(runner)._ensure_issue(DeliveryPlan(self.root/'delivery-plan.yaml').items['UX-99'],state,False)
        self.assertEqual(issue,99)
        self.assertIn('AgentOS UX v1.1',runner.calls[0][0])

    def test_status_reports_current_iteration(self):
        result=self.controller(Runner()).status()
        self.assertEqual(result['active'],'UX-01')
        self.assertEqual(result['milestone'],'AgentOS UX v1.1')


if __name__=='__main__':unittest.main()
