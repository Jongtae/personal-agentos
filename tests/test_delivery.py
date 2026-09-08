import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from personal_agent.delivery import DeliveryController, DeliveryError, DeliveryPlan, StateStore


class Runner:
    def __init__(self, results=None):
        self.calls=[]; self.results=list(results or [])

    def run(self, args, cwd=None, timeout=900):
        self.calls.append((list(args), Path(cwd) if cwd else None))
        return self.results.pop(0) if self.results else SimpleNamespace(returncode=0, stdout='', stderr='')


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'repo'; self.root.mkdir()
        source=Path(__file__).parents[1]/'delivery-plan.yaml'
        (self.root/'delivery-plan.yaml').write_text(source.read_text())
        self.state=self.root/'state.json'; self.clock=[1_700_000_000]

    def tearDown(self):
        self.temp.cleanup()

    def controller(self, runner=None):
        return DeliveryController(self.root, self.state, runner or Runner(), now=lambda: self.clock[0])

    def activate_governance_goal(self):
        plan=json.loads((self.root/'delivery-plan.yaml').read_text())
        plan['history']['documented_completed_iterations'].remove('GOV-01')
        plan['next_goal']={'id':'GOV-01','status':'active'}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))

    def test_packaged_delivery_plan_matches_repository_plan(self):
        root=Path(__file__).parents[1]
        self.assertEqual(json.loads((root/'delivery-plan.yaml').read_text()), json.loads((root/'personal_agent/delivery-plan.yaml').read_text()))

    def test_only_explicit_owner_activated_goal_can_be_selected(self):
        altered=json.loads((self.root/'delivery-plan.yaml').read_text())
        altered['history']['documented_completed_iterations'].remove('GOV-01')
        altered['next_goal']={'id':'GOV-01','status':'active'}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(altered))
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        self.assertEqual(plan.select({})['id'], 'GOV-01')
        altered['next_goal']['status']='requires-explicit-owner-approval'
        (self.root/'delivery-plan.yaml').write_text(json.dumps(altered))
        self.assertIsNone(DeliveryPlan(self.root/'delivery-plan.yaml').select({}))

    def test_top_goal_stays_selectable_after_its_inventory_substep_closes(self):
        plan=DeliveryPlan(self.root/'delivery-plan.yaml')
        self.assertIn('TOP-00', plan.documented_completed())
        self.assertEqual(plan.next_goal()['id'], 'TOP')
        self.assertEqual(plan.select({})['id'], 'TOP')

    def test_top_goal_migrates_a_documented_legacy_block_before_resuming(self):
        StateStore(self.state).write({
            'active':'UX-05', 'blocked':'UX-05', 'status':'blocked-validation-failed',
            'issues':{'UX-05':154},
        })
        runner=Runner([SimpleNamespace(returncode=0, stdout='OPEN\n', stderr='')])
        result=self.controller(runner).run_once()
        self.assertEqual(result['status'], 'manual-governance-execution-required')
        self.assertEqual(result['active'], 'TOP')
        self.assertNotIn('blocked', result)
        self.assertIn('TOP-00', result['completed'])

    def test_no_active_goal_refuses_automatic_selection_or_issue_creation(self):
        plan={'repository':'Jongtae/personal-agentos','iterations':[{'id':'NEW','issue':99,'milestone':'test','summary':'new work'}], 'next_goal':{}}
        (self.root/'delivery-plan.yaml').write_text(json.dumps(plan))
        controller=self.controller()
        self.assertIsNone(controller.plan.select({}))
        self.assertEqual(controller.run_once(dry_run=True)['status'], 'awaiting-owner-activated-goal')
        with self.assertRaisesRegex(DeliveryError, 'cannot create an issue'):
            controller._ensure_issue({'id':'NEW','milestone':'test','summary':'new work'}, {}, False)

    def test_closed_issue_does_not_complete_or_select_successor(self):
        self.activate_governance_goal()
        runner=Runner([SimpleNamespace(returncode=0, stdout='CLOSED\n', stderr='')])
        StateStore(self.state).write({'active':'GOV-01','issues':{'GOV-01':168}})
        result=self.controller(runner).reconcile()
        self.assertEqual(result['status'], 'completion-evidence-required')
        self.assertNotIn('GOV-01', result.get('completed', []))
        self.assertEqual(result['active'], 'GOV-01')

    def test_completion_requires_current_evidence_matrix(self):
        controller=self.controller()
        item=controller.plan.items['GOV-01']
        with self.assertRaisesRegex(DeliveryError, 'Completion rejected'):
            controller._complete(item, {'issues':{'GOV-01':168}})
        with self.assertRaisesRegex(DeliveryError, 'Completion rejected'):
            controller._complete(item, {'issues':{'GOV-01':168}, 'evidence_audit':{
                'merged_pr':'https://example.test/pr/1', 'required_ci':'passed', 'closeout':True, 'requirements':'mapped'}})

    def test_run_never_launches_worker_or_merges(self):
        self.activate_governance_goal()
        runner=Runner([SimpleNamespace(returncode=0, stdout='OPEN\n', stderr='')])
        result=self.controller(runner).run_once(dry_run=False)
        self.assertEqual(result['status'], 'manual-governance-execution-required')
        self.assertFalse(any(call[0][0] in {'codex','git'} for call in runner.calls))

    def test_blocked_goal_does_not_retry_or_contact_github_without_changed_condition(self):
        self.activate_governance_goal()
        runner=Runner()
        StateStore(self.state).write({'active':'GOV-01','blocked':'GOV-01','status':'blocked-blocked-approval','issues':{'GOV-01':168}})
        result=self.controller(runner).run_once()
        self.assertEqual(result['status'], 'blocked-awaiting-changed-condition')
        self.assertEqual(runner.calls, [])

    def test_release_helper_fails_closed_without_mutation(self):
        runner=Runner()
        item={'id':'REL','milestone':'test','summary':'release'}
        result=self.controller(runner)._run_release(item,{})
        self.assertEqual(result['status'], 'blocked-manual-governance-execution-required')
        self.assertEqual(runner.calls, [])

    def test_schedule_cannot_create_a_second_delivery_loop(self):
        with self.assertRaisesRegex(DeliveryError, 'one existing goal-resume heartbeat'):
            self.controller().install_schedule()

    def test_state_does_not_persist_sensitive_or_unreviewed_evidence(self):
        saved=StateStore(self.state).write({'active':'GOV-01','status':'blocked','api_key':'secret','evidence_audit':{'requirements':'private'}})
        self.assertEqual(saved, {'active':'GOV-01','status':'blocked'})


if __name__ == '__main__':
    unittest.main()
