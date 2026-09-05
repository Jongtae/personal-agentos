# AgentOS — install, configure, talk

AgentOS is a self-hosted personal agent preview. One local process serves a Korean web setup and chat interface. Docker and Kubernetes are not required. Homebrew installs Python automatically; model runtimes and model weights are separate.

## Install on macOS

Install Homebrew from [brew.sh](https://brew.sh) if needed, then:

```sh
brew install jongtae/agentos/agentos
agentos start
```

The browser opens a private first-time setup link at `http://127.0.0.1:8787`. Set an administrator password (12+ characters), choose a model provider, enter its endpoint and model name, and press Save then Test connection. API keys stay on this computer in a private file; they are not sent to GitHub. Cloud model requests send conversation content to your selected provider.

Supported connections: Ollama (an already running local model server), OpenAI-compatible Chat Completions endpoints, and Anthropic Messages. Bring your own model access; no paid model subscription is included.

## First task

In web chat, enter `/note Review the launch on Friday`, then `/notes`. These work without a model. After connecting a model, try `/summarize` or a normal conversation.

## Telegram

Create your own bot using Telegram's BotFather, paste its token into Settings, and open the generated pairing link in your own Telegram account. Only the paired private account can submit work. The web interface and Telegram share conversation history and notes. AgentOS uses outbound polling, so no public inbound port is needed for Telegram. Use a dedicated bot without an existing webhook.

The computer must remain running and awake for remote requests to be processed. This preview does not install a background login service. Keep the terminal open; Ctrl-C stops AgentOS.

## Restart and update

```sh
agentos start
# Stop the process before upgrading:
brew update
brew upgrade jongtae/agentos/agentos
agentos start
```

Data persists in `~/.local/share/agentos`; uninstalling the formula does not delete it. Back up the entire data directory while AgentOS is stopped. This directory contains your private conversations and credentials; credentials have filesystem permissions, not application-level encryption.

If the browser does not open, use the link in `~/.local/share/agentos/private/setup-link.txt` locally. Do not share that file before setup. After setup, open `http://127.0.0.1:8787` and log in. An occupied port can be changed using `agentos start --port 8788`.

## Remote host / source installation

Python 3.12+ on macOS or Linux is required for source execution:

```sh
python3 -m personal_agent.quickstart start --no-browser
```

On a remote host, keep the default loopback binding and connect through SSH forwarding (`ssh -L 8787:127.0.0.1:8787 your-host`). Open the setup link through that tunnel. Public managed hosting, TLS termination, mobile apps and Kubernetes packaging are future deployment work.

## Preview scope

Implemented: single owner, password login, model adapters, persistent chat and notes, queued requests, private Telegram pairing and deduplication. Interrupted model work and uncertain Telegram delivery are shown without automatic replay.

Not yet implemented: arbitrary tool execution, calendar/email integrations, plugin installation, multiple assistants, desktop/mobile applications, unattended service management, or multi-user hosting. This is the first installation-to-task slice, not the complete AgentOS ecosystem.

Tests use simulated provider and Telegram responses, plus a real local HTTP server for setup/chat/authentication. Live provider and Telegram testing requires your credentials.

Source and Homebrew formula: [Jongtae/homebrew-agentos](https://github.com/Jongtae/homebrew-agentos).
