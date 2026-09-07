import subprocess
import tempfile
import unittest
from pathlib import Path

from personal_agent.product_validation import ProductValidator, markdown


class ProductValidationTests(unittest.TestCase):
    def fixture(self):
        folder = tempfile.TemporaryDirectory(); root = Path(folder.name)
        (root / "docs").mkdir(); (root / "personal_agent").mkdir()
        (root / "TASKS.md").write_text("# tasks\n")
        (root / "QUICKSTART.md").write_text("PDF and Office documents are supported.\n")
        (root / "docs/roadmap.md").write_text("## M3 — continuity and installation\nCompleted: yes\n## M4 — extensibility\nCompleted: yes\n## M5 — v1 release\nCompleted: yes\n")
        (root / "personal_agent/quickstart_service.py").write_text("model_ready document_boundary connect_telegram")
        (root / "personal_agent/agent_runtime.py").write_text("delegate_agent")
        (root / "personal_agent/plugins.py").write_text("class PluginRegistry: pass")
        (root / "personal_agent/quickstart.py").write_text("# no plugin interface")
        return folder, root

    def test_stale_documents_fail(self):
        folder, root = self.fixture()
        try:
            (root / "TASKS.md").write_text("| M3 | Persistent runtime and official server install | Planned |\n")
            validator = ProductValidator(root); validator.documentation()
            self.assertEqual(validator.findings[0].status, "failed")
        finally: folder.cleanup()

    def test_delivered_roadmap_wording_is_current(self):
        folder, root = self.fixture()
        try:
            (root / "docs/roadmap.md").write_text("## M3 — continuity and installation\nCompleted: yes\n## M4 — extensibility\nP4-01 delivered\n## M5 — v1 release\nCompleted: yes\n")
            validator = ProductValidator(root); validator.documentation()
            self.assertEqual(validator.findings[0].status, "passed")
        finally: folder.cleanup()

    def test_plugin_registry_without_surface_fails(self):
        folder, root = self.fixture()
        try:
            validator = ProductValidator(root); validator.source_contracts()
            self.assertEqual(next(f for f in validator.findings if f.id == "EXT-001").status, "failed")
        finally: folder.cleanup()

    def test_command_failure_is_reported_without_output_leak(self):
        folder, root = self.fixture()
        try:
            def runner(*args, **kwargs): return subprocess.CompletedProcess(args[0], 1, "", "failed")
            validator = ProductValidator(root, runner=runner)
            self.assertFalse(validator.command(["bad"], "Contract check"))
            self.assertEqual(validator.findings[-1].status, "failed")
        finally: folder.cleanup()

    def test_markdown_contains_all_findings(self):
        folder, root = self.fixture()
        try:
            validator = ProductValidator(root); validator.documentation(); validator.vision_gaps()
            report = validator.report()
            self.assertIn("VISION-001", markdown(report))
        finally: folder.cleanup()
