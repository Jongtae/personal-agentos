import tempfile
import unittest
import json
from pathlib import Path
from types import SimpleNamespace

from personal_agent.handoff import Candidate, GithubCliBoundary, HandoffError, Issue, StateHandoffLoop


class FakeGithub:
    def __init__(self, issues):
        self.rows = {row.number: row for row in issues}; self.comments = []; self.transitions = []
        self.candidates = {}; self.active = set(); self.timeout_once = False
    def issues(self): return list(self.rows.values())
    def transition(self, number, old, new):
        row = self.rows[number]
        if row.queue_state() != old: return False
        row.labels.discard(old); row.labels.add(new); self.transitions.append((number, old, new)); return True
    def comment_exists(self, number, marker): return any(a == number and b == marker for a, b, _ in self.comments)
    def comment(self, number, marker, text):
        self.comments.append((number, marker, text))
        if self.timeout_once: self.timeout_once = False; raise TimeoutError()
    def claim_winner(self, number, marker):
        prefix = ":".join(marker.split(":")[:4]) + ":"
        claims = [value for issue, value, _ in self.comments if issue == number and prefix in value]
        return bool(claims) and claims[0] == marker
    def candidate(self, number): return self.candidates.get(number)
    def execution_active(self, number, lease): return number in self.active


def goal(number, state="agent:ready", ok=True):
    return Issue(number, {state}, "## Executable goal\n## Allowed authority", authorized=ok, dependencies_satisfied=ok)


class HandoffTests(unittest.TestCase):
    def setUp(self): self.temp = tempfile.TemporaryDirectory(); self.state = Path(self.temp.name) / "handoff.json"
    def tearDown(self): self.temp.cleanup()

    def test_end_to_end_dynamic_state_handoff_creates_artifact_and_reuses_rework(self):
        ready, later = goal(47), goal(981)
        gh = FakeGithub([ready, later]); artifacts = []; heads = iter(["a" * 40, "b" * 40])
        def executor(issue, feedback):
            artifact = Path(self.temp.name) / f"implementation-{issue.number}-{len(artifacts)}.txt"; artifact.write_text("real bounded implementation")
            artifacts.append((issue.number, feedback, artifact)); candidate = Candidate(issue.number, issue.number + 100, next(heads), "main", "success", evidence="tests")
            gh.candidates[issue.number] = candidate; return candidate
        calls = []
        def reviewer(issue, candidate):
            calls.append((issue.number, candidate.head)); return ["fixture regression"] if len(calls) == 1 else []
        loop = StateHandoffLoop(gh, self.state, executor, reviewer, worker_id="worker-a")
        self.assertEqual(loop.tick("implementer")["state"], "agent:review")
        self.assertEqual(gh.rows[47].queue_state(), "agent:review")
        self.assertEqual(loop.tick("reviewer")["state"], "agent:rework")
        self.assertEqual(loop.tick("implementer")["state"], "agent:review")
        self.assertEqual(loop.tick("reviewer")["state"], "agent:approved")
        self.assertEqual(gh.rows[47].queue_state(), "agent:approved")
        self.assertEqual(gh.rows[981].queue_state(), "agent:ready")
        self.assertTrue(all(path.read_text() == "real bounded implementation" for _, _, path in artifacts))
        self.assertIn("fixture regression", artifacts[1][1]["findings"])
        claims = [marker for _, marker, _ in gh.comments if ":claim:" in marker]
        self.assertTrue(any(":47:ready:" in marker for marker in claims))
        self.assertTrue(any(":47:rework:" in marker for marker in claims))
        self.assertEqual(len(gh.comments), 6)

    def test_rework_precedes_ready_and_invalid_states_never_start(self):
        rework, ready = goal(90, "agent:rework"), goal(12)
        invalid = Issue(13, {"agent:ready", "agent:review"}, authorized=True, dependencies_satisfied=True)
        blocked = Issue(14, {"agent:blocked"}, authorized=True, dependencies_satisfied=True)
        unauthorized = goal(15, ok=False); gh = FakeGithub([ready, rework, invalid, blocked, unauthorized]); invoked = []
        def executor(issue, feedback):
            invoked.append(issue.number); c = Candidate(issue.number, 1, "c" * 40, "main", "pending"); gh.candidates[issue.number] = c; return c
        result = StateHandoffLoop(gh, self.state, executor).tick("implementer")
        self.assertEqual(result["issue"], 90); self.assertEqual(invoked, [90]); self.assertEqual(ready.queue_state(), "agent:ready")

    def test_pending_ci_and_missing_candidate_cannot_reach_reviewer(self):
        row = goal(201); gh = FakeGithub([row])
        def executor(issue, feedback):
            c = Candidate(issue.number, 2, "d" * 40, "main", "pending"); gh.candidates[issue.number] = c; return c
        loop = StateHandoffLoop(gh, self.state, executor, lambda *_: [])
        self.assertEqual(loop.tick("implementer")["action"], "awaiting-ci")
        self.assertEqual(row.queue_state(), "agent:working")
        row.labels = {"agent:review"}
        self.assertEqual(loop.tick("reviewer")["action"], "candidate-not-reviewable")

    def test_dispatch_only_tick_never_claims_or_strands_ready_issue(self):
        row = goal(250); gh = FakeGithub([row])
        result = StateHandoffLoop(gh, self.state).tick("implementer")
        self.assertEqual(result["action"], "dispatch-required")
        self.assertEqual(row.queue_state(), "agent:ready")
        self.assertEqual(gh.transitions, [])

    def test_cli_boundary_requires_explicit_owner_and_dependency_markers(self):
        rows = [
            {"number": 701, "state": "OPEN", "labels": [{"name": "agent:ready"}], "body": "## Executable goal\n## Allowed authority"},
            {"number": 702, "state": "OPEN", "labels": [{"name": "agent:ready"}], "body": "## Executable goal\n## Allowed authority\n<!-- agentos:owner-authorized -->\n<!-- agentos:dependencies-satisfied -->"},
        ]
        def runner(_): return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")
        found = GithubCliBoundary("example/repo", runner).issues()
        self.assertFalse(found[0].authorized); self.assertFalse(found[0].dependencies_satisfied)
        self.assertTrue(found[1].authorized); self.assertTrue(found[1].dependencies_satisfied)

    def test_identical_ticks_and_comment_timeout_are_idempotent(self):
        row = goal(300); gh = FakeGithub([row]); runs = []
        def executor(issue, feedback):
            runs.append(issue.number); c = Candidate(issue.number, 3, "e" * 40, "main", "success"); gh.candidates[issue.number] = c; return c
        gh.timeout_once = True; loop = StateHandoffLoop(gh, self.state, executor)
        self.assertEqual(loop.tick("implementer")["state"], "agent:review")
        self.assertEqual(loop.tick("implementer")["action"], "idle")
        self.assertEqual(runs, [300]); self.assertEqual(len(gh.comments), 2)

    def test_existing_cross_writer_claim_loses_without_executor_or_label_write(self):
        row = goal(350); gh = FakeGithub([row]); gh.comment(350, "agentos-handoff:claim:350:ready:other:nonce", "other lease")
        loop = StateHandoffLoop(gh, self.state, lambda *_: self.fail("losing writer executed"), worker_id="mine")
        self.assertEqual(loop.tick("implementer")["action"], "claim-raced")
        self.assertEqual(row.queue_state(), "agent:ready")

    def test_active_writer_and_lock_prevent_duplicate_execution(self):
        row = goal(401, "agent:working"); gh = FakeGithub([row]); gh.active.add(401)
        loop = StateHandoffLoop(gh, self.state, lambda *_: self.fail("must not execute"))
        self.assertEqual(loop.tick("implementer")["action"], "writer-already-active")
        handle = loop.state.locked()
        try:
            with self.assertRaisesRegex(HandoffError, "already running"): loop.tick("implementer")
        finally: handle.close()

    def test_stale_candidate_rejects_approval(self):
        row = goal(501, "agent:review"); gh = FakeGithub([row])
        first = Candidate(501, 5, "f" * 40, "main", "success"); gh.candidates[501] = first
        loop = StateHandoffLoop(gh, self.state, reviewer=lambda *_: [])
        loop.state.write({"candidate": first.__dict__})
        def changed(*_):
            gh.candidates[501] = Candidate(501, 5, "g" * 40, "main", "success"); return []
        loop.reviewer = changed
        self.assertEqual(loop.tick("reviewer")["action"], "stale-review-rejected")
        self.assertEqual(row.queue_state(), "agent:review")

    def test_disappearing_candidate_rejects_approval_without_crash(self):
        row = goal(502, "agent:review"); gh = FakeGithub([row])
        first = Candidate(502, 5, "h" * 40, "main", "success"); gh.candidates[502] = first
        def disappear(*_):
            gh.candidates.pop(502); return []
        loop = StateHandoffLoop(gh, self.state, reviewer=disappear)
        loop.state.write({"candidate": first.__dict__})
        self.assertEqual(loop.tick("reviewer")["action"], "stale-review-rejected")
        self.assertEqual(row.queue_state(), "agent:review")


if __name__ == "__main__": unittest.main()
