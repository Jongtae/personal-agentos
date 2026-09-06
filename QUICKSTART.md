# AgentOS — install, configure, talk

AgentOS is a self-hosted personal agent preview. One local process serves a Korean web setup and chat interface. Docker and Kubernetes are not required. Homebrew installs Python automatically; model runtimes and model weights are separate.

## Install on macOS

Install Homebrew from [brew.sh](https://brew.sh) if needed, then:

```sh
brew install jongtae/agentos/agentos
agentos start
```

The browser opens at `http://127.0.0.1:8787`. Click **바로 시작하기** (Start now). There is no setup code to enter. A login password is optional for local use; expand **비밀번호 설정 · 선택** to set one (12+ characters). Without a password, anyone using this computer can access the agent through its local address. Then choose a model provider, endpoint and model name, and use Save and Test connection. API keys stay in a private local file. Cloud requests send conversation content to your selected provider.


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

If the browser does not open, use the link in `~/.local/share/agentos/private/setup-link.txt` locally. Do not share that file before setup. After setup, open `http://127.0.0.1:8787`; log in only if you chose a password. An occupied port can be changed using `agentos start --port 8788`.

## Remote host / source installation

Python 3.12+ on macOS or Linux is required for source execution:

```sh
python3 -m personal_agent.quickstart start --no-browser
```

On a remote host, keep the default loopback binding and connect through SSH forwarding (`ssh -L 8787:127.0.0.1:8787 your-host`). Open the setup link through that tunnel. Public managed hosting, TLS termination, mobile apps and Kubernetes packaging are future deployment work.

## Preview scope

Implemented: single owner, password login, model adapters, persistent chat and notes, queued requests, private Telegram pairing and deduplication. Interrupted model work and uncertain Telegram delivery are shown without automatic replay.

Not yet implemented: arbitrary shell execution, calendar/email integrations, plugin installation, external agent-engine connections, desktop/mobile applications, unattended service management, or multi-user hosting. This is the first installation-to-task slice, not the complete AgentOS ecosystem.

Tests use simulated provider and Telegram responses, plus a real local HTTP server for setup/chat/authentication. Live provider and Telegram testing requires your credentials.

Source and Homebrew formula: [Jongtae/homebrew-agentos](https://github.com/Jongtae/homebrew-agentos).

## General tool runtime (0.2.0)

Normal messages use a shared native tool-call loop. The model selects from web search,
weather, connected-folder search/read, personal notes, and built-in researcher/reviewer
agents. No keyword rule forces weather or search. OpenRouter's free router chooses a
model for each request; that model is kept for the remainder of the tool loop.
Free-provider availability and quotas can still interrupt a request; failures are shown.

Under **연결 설정 → 내 파일 연결**, register specific folders on the AgentOS host.
Only connected UTF-8 text files up to 1 MB are supported (16,000 characters per read).
PDF/Office extraction is not implemented. When using a cloud model, requested file
contents are sent to that model. Mobile clients access the host's connected folders.

Try these in the same conversation:
- “Kubernetes 공식 문서를 검색해 줘.”
- “내 파일에서 Aurora 출시 계획을 찾아서 읽어 줘.”
- “그 내용을 검토 에이전트에게 전달해 줘.”
- “이제 도구 없이 안녕이라고만 답해 줘.”
- “출시 검토가 필요하다고 메모해 줘.”

Specialists run separate conversations with the configured model provider and read-only
tools. They are not external Codex/Claude Code processes. Recursive delegation and
shell commands are unavailable. **최근 도구 실행 기록** shows actual tool execution.

`python3 -m unittest discover -s tests -q` checks local contracts and errors.
`scripts/verify_general_agent.py` runs live multi-topic acceptance with the configured
provider in a temporary store; `--installed` verifies the Homebrew installation.
It creates a synthetic local document and never changes personal chat or notes.
