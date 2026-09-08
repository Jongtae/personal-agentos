"""Owner-runtime isolation contract used by local and hosted deployment paths.

This module deliberately describes deployment boundaries only. It never mounts
or enumerates a Mac directory, starts a container, or grants an execution
engine access to the host.
"""
from dataclasses import dataclass
import re

_OWNER_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?$")
_FORBIDDEN_MOUNT_PARTS = ("/var/run/docker.sock", "/Users/", "/home/", "${HOME}", "~")


def owner_slug(owner_id):
    """Return a safe, stable deployment identifier for one owner."""
    if not isinstance(owner_id, str) or not _OWNER_ID.fullmatch(owner_id):
        raise ValueError("owner id must be 1-48 lowercase letters, digits, or internal hyphens")
    return owner_id


@dataclass(frozen=True)
class OwnerRuntime:
    owner_id: str

    @property
    def volume_name(self):
        return "agentos-owner-" + owner_slug(self.owner_id)

    @property
    def kubernetes_name(self):
        return "agentos-" + owner_slug(self.owner_id)

    @property
    def mediated_input_path(self):
        return "/data/mediated-input"


def validate_container_boundary(spec):
    """Reject container settings that would bridge an owner runtime to its host."""
    security = spec.get("securityContext", {})
    if security.get("privileged") is True or security.get("allowPrivilegeEscalation") is True:
        raise ValueError("privileged owner runtimes are not permitted")
    if security.get("runAsNonRoot") is not True or security.get("readOnlyRootFilesystem") is not True:
        raise ValueError("owner runtime must be non-root with a read-only root filesystem")
    for mount in spec.get("mounts", []):
        source = str(mount.get("source", "")); target = str(mount.get("target", ""))
        if mount.get("type") == "hostPath" or any(part in source or part in target for part in _FORBIDDEN_MOUNT_PARTS):
            raise ValueError("host paths and Docker sockets are not permitted")
        if target == "/data" and mount.get("readOnly") is True:
            raise ValueError("the owner data volume must be writable by its runtime")
    return True
