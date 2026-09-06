# AgentOS contribution workflow

## Product priority

Personal AgentOS is a personal, self-hosted agent runtime. Every task must
advance one or more of these outcomes:

- reliable user-owned runtime behavior
- lower setup and operations cost
- safe capability ownership and transparent execution
- continuity across web, Telegram, restart, and update

Do not expand Kubernetes, appliance, or UI polish work unless it directly
advances one of these outcomes.

## Required lifecycle

Every milestone and iteration uses:

1. a GitHub issue
2. a matching branch
3. small intentional commits
4. a pull request with validation evidence
5. merge, issue closeout, and a ledger entry

Iteration issues use `[P<phase>-NN] <user outcome>`. Epic issues use
`EPIC: Stage <stage> / Phase <phase> <name>`. Use `feature/`, `fix/`,
`docs/`, `build/`, or `experiment/` prefixes for public branches.

Before implementation, record user outcome, runtime impact, acceptance
criteria, non-goals, and targeted tests in the issue. Before closeout, update
`TASKS.md`, `docs/roadmap.md`, and `docs/issue-branch-ledger.jsonl` together.

## Truthfulness and safety

- A capability is complete only when its actual execution is observed.
- Tests, mocks, and live acceptance are different evidence and must be named
  separately in PRs.
- Default to connected-folder read access. Do not add arbitrary shell access,
  external writes, or access outside user-approved folders without a dedicated
  approval design and acceptance suite.
- Never claim that a model, Telegram, Docker, or Homebrew path works unless
  that exact path was tested.

## Pull request closeout

Every PR states what changed, why, validation evidence, known limitations,
data/security impact, and the issue it closes. Squash merge feature work into
`main` after validation passes. Release work is only complete after the
version tag, GitHub Release, Homebrew Formula update, and installed smoke test
all succeed.
