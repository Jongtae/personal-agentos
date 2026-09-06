# Personal AgentOS

Personal AgentOS is a self-hosted personal agent for one owner. It runs on a
Mac or a single Linux server, keeps its conversations and configuration under
the owner's control, and can be reached through the web and Telegram.

The current preview supports model-backed conversation, web search, weather,
connected text files, notes, and bounded researcher/reviewer roles. Every
tool run is recorded in the conversation UI.

## Product direction

The v1 goal is a dependable personal runtime: install it, connect a model and
Telegram, give it a task, and see the work it actually performed. This project
does not build an operating system. Kubernetes, multi-tenant hosting, native
mobile apps, and external coding-engine adapters are post-v1 tracks.

## Install

macOS installation currently uses the Homebrew tap:

```sh
brew install jongtae/agentos/agentos
agentos start
```

See [Quickstart](QUICKSTART.md) for setup, privacy boundaries, and supported
model connections.

## Development workflow

Product work is issue-first and PR-centered. Read these in order before a new
iteration:

1. [AGENTS.md](AGENTS.md)
2. [PRD.md](PRD.md)
3. [TASKS.md](TASKS.md)
4. [Roadmap](docs/roadmap.md)

Each task has an issue, branch, focused validation, PR, merge, and closeout
record. The Homebrew tap is a separate release integration, not the product
source of truth.

## Validation

```sh
python3 -m unittest discover -s tests -q
python3 scripts/quickstart_install_check.py
python3 scripts/verify_general_agent.py --installed --model minimax/minimax-m2.7:free
```

The final command needs a configured model key and uses a temporary test store.
