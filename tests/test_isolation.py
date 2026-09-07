import unittest
from pathlib import Path

from personal_agent.isolation import OwnerRuntime, owner_slug, validate_container_boundary


class OwnerRuntimeIsolationTests(unittest.TestCase):
    def test_owner_specific_names_are_stable_and_safe(self):
        runtime = OwnerRuntime('owner-42')
        self.assertEqual(runtime.volume_name, 'agentos-owner-owner-42')
        self.assertEqual(runtime.mediated_input_path, '/data/mediated-input')
        for unsafe in ('Owner', '../owner', 'owner_42', 'a' * 49):
            with self.assertRaises(ValueError): owner_slug(unsafe)

    def test_boundary_rejects_host_and_privileged_access(self):
        safe = {'securityContext': {'runAsNonRoot': True, 'readOnlyRootFilesystem': True},
                'mounts': [{'type': 'volume', 'source': 'owner-data', 'target': '/data'}]}
        self.assertTrue(validate_container_boundary(safe))
        for bad in (
            {'securityContext': {'runAsNonRoot': True, 'readOnlyRootFilesystem': True, 'privileged': True}},
            {'securityContext': {'runAsNonRoot': True, 'readOnlyRootFilesystem': True}, 'mounts': [{'type': 'hostPath', 'source': '/Users/alice', 'target': '/data'}]},
            {'securityContext': {'runAsNonRoot': True, 'readOnlyRootFilesystem': True}, 'mounts': [{'type': 'volume', 'source': 'docker', 'target': '/var/run/docker.sock'}]},
        ):
            with self.assertRaises(ValueError): validate_container_boundary(bad)

    def test_hosting_templates_keep_the_same_boundary(self):
        root = Path(__file__).resolve().parents[1]
        compose = (root / 'deploy/owner-runtime.compose.yaml').read_text()
        kubernetes = (root / 'deploy/kubernetes/owner-runtime.yaml').read_text()
        self.assertIn('name: agentos-owner-${AGENTOS_OWNER', compose)
        self.assertIn('read_only: true', compose)
        self.assertNotIn('type: bind', compose)
        self.assertIn('kind: NetworkPolicy', kubernetes)
        self.assertIn('automountServiceAccountToken: false', kubernetes)
        self.assertIn('readOnlyRootFilesystem: true', kubernetes)
        self.assertNotIn('hostPath:', kubernetes)
