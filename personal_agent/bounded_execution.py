"""Bounded subscription-engine execution owned by AgentOS.

This module is deliberately independent of the API-key provider path.  An
engine gets a fresh, empty working directory and a small MCP tool catalogue;
it never receives the owner store, a host path, or arbitrary shell access.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile


MAX_PROMPT_BYTES = 48_000
MAX_OUTPUT_BYTES = 96_000
MAX_TIMEOUT_SECONDS = 120


MCP_TOOLS = (
    {'name': 'list_notes', 'description': 'List saved AgentOS notes.'},
    {'name': 'save_note', 'description': 'Save an explicitly requested personal note.',
     'input_schema': {'type': 'object', 'properties': {'content': {'type': 'string', 'maxLength': 12000}}, 'required': ['content'], 'additionalProperties': False}},
    {'name': 'web_search', 'description': 'Search public web snippets through AgentOS.',
     'input_schema': {'type': 'object', 'properties': {'query': {'type': 'string', 'maxLength': 500}}, 'required': ['query'], 'additionalProperties': False}},
)


class ExecutionError(ValueError):
    """A safe, user-visible execution-boundary failure."""


@dataclass(frozen=True)
class ExecutionResult:
    content: str
    engine: str
    exit_code: int


class AgentOSMcpTools:
    """The only tool facade that may be offered to a subscription engine."""
    def __init__(self, capabilities):
        self.capabilities = capabilities

    def definitions(self):
        # Return JSON-compatible copies: callers must not mutate the contract.
        return json.loads(json.dumps(MCP_TOOLS))

    def call(self, name, arguments):
        if not isinstance(arguments, dict):
            raise ExecutionError('MCP 도구 인수는 객체여야 합니다.')
        allowed = {
            'list_notes': set(),
            'save_note': {'content'},
            'web_search': {'query'},
        }
        if name not in allowed or set(arguments) - allowed[name]:
            raise ExecutionError('허용하지 않은 AgentOS MCP 도구 또는 인수입니다.')
        if name == 'list_notes' and arguments:
            raise ExecutionError('list_notes에는 인수가 없습니다.')
        if name in ('save_note', 'web_search'):
            value = arguments.get('content' if name == 'save_note' else 'query')
            if not isinstance(value, str) or not value.strip():
                raise ExecutionError('MCP 도구의 필수 문자열 인수가 비어 있습니다.')
        # Capabilities is AgentOS-owned and applies its normal validation,
        # document boundary, evidence and idempotency rules.
        return self.capabilities.execute(name, arguments)


class BoundedExecutionAdapter:
    """Start an official subscription CLI with no shell and no inherited env.

    The adapter intentionally has no generic argv, cwd, environment, or tool
    configuration parameters.  Expanding those is a security design change,
    not an engine prompt option.
    """
    def __init__(self, finder=None, runner=subprocess.run, runtime_root='/data/engine-runs'):
        from shutil import which
        self.finder = finder or which
        self.runner = runner
        self.runtime_root = Path(runtime_root)

    def command(self, engine_id, binary, prompt, mcp_config):
        if engine_id == 'codex':
            # `exec` is non-interactive and JSON output is required so prose
            # around an answer cannot be mistaken for execution evidence.
            return [binary, 'exec', '--json', '--sandbox', 'read-only', '--skip-git-repo-check', prompt]
        if engine_id == 'claude-code':
            return [binary, '-p', prompt, '--output-format', 'json', '--strict-mcp-config', '--mcp-config', str(mcp_config)]
        raise ExecutionError('지원하는 구독 엔진을 선택하세요.')

    @staticmethod
    def _content(engine_id, raw):
        if len(raw.encode()) > MAX_OUTPUT_BYTES:
            raise ExecutionError('엔진 응답이 안전한 크기 제한을 초과했습니다.')
        try:
            # Codex's machine output is JSONL.  Only examine its last complete
            # event, never concatenate progress/event text into an answer.
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
            data = records[-1]
        except (TypeError, ValueError, IndexError):
            raise ExecutionError('엔진이 요구된 구조화된 응답을 반환하지 않았습니다.') from None
        if engine_id == 'codex':
            # Codex exec emits JSONL; accepting one final object only avoids
            # accidentally treating tool/event transcripts as the answer.
            if isinstance(data, dict):
                item = data.get('item', {})
                content = (data.get('content') or data.get('output') or
                           (item.get('text') if isinstance(item, dict) else None))
            else:
                content = None
        else:
            content = data.get('result') if isinstance(data, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ExecutionError('엔진 응답에 최종 텍스트 결과가 없습니다.')
        return content[:24_000]

    def execute(self, engine_id, prompt, tools):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode()) > MAX_PROMPT_BYTES:
            raise ExecutionError('요청은 비어 있지 않은 48KB 이하의 텍스트여야 합니다.')
        binaries = {'codex': 'codex', 'claude-code': 'claude'}
        if engine_id not in binaries:
            raise ExecutionError('지원하는 구독 엔진을 선택하세요.')
        binary = self.finder(binaries[engine_id])
        if not binary:
            raise ExecutionError('연결한 구독 엔진 CLI를 격리된 런타임에서 찾지 못했습니다.')
        # Only declarative tool metadata is written here.  Tool calls must be
        # served by the AgentOS MCP bridge, never by engine-provided commands.
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self.runtime_root, prefix='turn-') as folder:
            run_dir = Path(folder)
            config = run_dir / 'agentos-mcp.json'
            config.write_text(json.dumps({'tools': tools.definitions()}, ensure_ascii=False), encoding='utf-8')
            env = {'HOME': str(run_dir), 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}
            try:
                completed = self.runner(self.command(engine_id, binary, prompt, config), cwd=run_dir,
                                        env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                        text=True, timeout=MAX_TIMEOUT_SECONDS, shell=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ExecutionError('구독 엔진을 안전한 시간 안에 실행하지 못했습니다.') from exc
            if completed.returncode != 0:
                raise ExecutionError('구독 엔진이 작업을 완료하지 못했습니다.')
            return ExecutionResult(self._content(engine_id, completed.stdout), engine_id, completed.returncode)
