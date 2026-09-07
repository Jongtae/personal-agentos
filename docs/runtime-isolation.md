# Owner runtime isolation

H1-02 establishes the deployment boundary for one owner. It does not run a Codex or Claude Code turn; that is H2-01 work and must use AgentOS-owned tools.

Each owner gets a separate OCI runtime (or managed lightweight VM equivalent), a dedicated persistent data volume, and an empty temporary workspace. The image runs as UID 10001 with a read-only root filesystem, no Linux capabilities, no privilege escalation, no host network, and no Docker socket. A source file is never mounted from the Mac: the companion may copy an owner-approved snapshot into the separate read-only `mediated-input` volume. Future AgentOS tools must expose only the approved subset.

`deploy/owner-runtime.compose.yaml` is the self-hosted rendering. Set a unique, lowercase `AGENTOS_OWNER` only after validating it with `owner_slug`; the volume name is owner-specific. It deliberately has no bind mounts.

`deploy/kubernetes/owner-runtime.yaml` is the managed-hosting translation. The control plane renders one namespace, PVC, and deployment per validated owner ID. It does not receive personal content, tool payloads, or provider credentials. The namespace disables service-account token mounting and begins with a default-deny network policy. Any ingress, egress, document transfer, or engine integration must be added later as a narrow, tested, approval-aware policy.

## H2-01 subscription-engine boundary

Subscription CLIs are launched by AgentOS without a shell, in a newly created per-turn directory with a fixed minimal environment and a 120-second limit. The adapter accepts structured final output only. It exposes a small AgentOS-owned MCP facade (`list_notes`, explicit `save_note`, and public `web_search`); it does not pass a database handle, host paths, document roots, arbitrary environment variables, or credentials to the engine. Every selected-engine turn is recorded as a `subscription_engine` tool event. This is an automated boundary implementation, not evidence that an owner's Codex or Claude Code subscription has completed a live turn.
