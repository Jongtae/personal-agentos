import tempfile
from pathlib import Path
import pytest
from personal_agent.portable_state import export_owner_state,restore_owner_state
from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart_store import QuickStore


def test_restore_refuses_nonempty_target_and_never_nests_state():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder); source=QuickStore(root/"source"); archive=export_owner_state(source.root,root/"owner.tar.gz")
        target=root/"target"; target.mkdir(); (target/"existing").write_text("preserve")
        with pytest.raises(ValueError,match="empty"):restore_owner_state(archive,target)
        assert (target/"existing").read_text()=="preserve"
        (target/"existing").unlink(); restore_owner_state(archive,target)
        assert (target/"private"/"quickstart.db").is_file(); assert not (target/"agentos-owner-state").exists()


def test_restore_quarantines_incomplete_jobs_without_replay_or_duplicate():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder); source=QuickStore(root/"source")
        queued=source.enqueue("queued work","restore-queued"); running=source.enqueue("running work","restore-running")
        with source.db() as db:db.execute("UPDATE jobs SET status='running',delivery='sending' WHERE id=?",(running,))
        restored=QuickStore(restore_owner_state(export_owner_state(source.root,root/"owner.tar.gz"),root/"restored"))
        assert restored.job(queued)["status"]=="interrupted"; assert restored.job(running)["status"]=="interrupted"
        assert restored.job(running)["delivery"]=="unknown"
        assert restored.enqueue("queued work","restore-queued")==queued; assert AgentService(restored).run_one() is False


def test_portable_restore_excludes_engine_profile_and_selection():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder); source=QuickStore(root/"source"); source.put("subscription_engine",{"id":"codex"})
        profile=source.root.parent/"engine-profile"; profile.mkdir(); (profile/"auth.json").write_text("fixture-secret")
        restored_path=restore_owner_state(export_owner_state(source.root,root/"owner.tar.gz"),root/"restored")
        assert QuickStore(restored_path).config("subscription_engine") is None
        assert not (restored_path/"engine-profile").exists()
