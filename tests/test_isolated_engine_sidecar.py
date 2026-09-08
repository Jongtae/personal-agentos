import json
import stat
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from personal_agent.isolated_engine_sidecar import IsolatedEngineSidecar, make_handler


class _AgentOSCallback(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        type(self).calls.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "task_id": self.headers.get("X-AgentOS-Task-ID"),
                "content_type": self.headers.get("Content-Type"),
                "request": request,
            }
        )
        response = {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {"content": [{"type": "text", "text": json.dumps({"notes": ["private note"]})}]},
        }
        raw = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
import subprocess
import sys

assert sys.argv[1:6] == ["exec", "--json", "--sandbox", "read-only", "--skip-git-repo-check"]
assert os.listdir(".") == []
settings = {}
index = 6
while index < len(sys.argv) - 1:
    assert sys.argv[index] == "-c"
    name, raw = sys.argv[index + 1].split("=", 1)
    settings[name] = json.loads(raw)
    index += 2
process = subprocess.Popen(
    [settings["mcp_servers.agentos.command"], *settings["mcp_servers.agentos.args"]],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)
def rpc(value, response=True):
    process.stdin.write(json.dumps(value) + "\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline()) if response else None

initialized = rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
assert initialized["result"]["capabilities"] == {"tools": {}}
tools = rpc({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
assert [tool["name"] for tool in tools["result"]["tools"]] == ["list_notes"]
denied = rpc({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"save_note","arguments":{"content":"changed"}}})
assert denied["error"]["code"] == -32601
notes = rpc({"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_notes","arguments":{}}})
process.stdin.close()
process.wait(timeout=2)
assert process.returncode == 0
text = notes["result"]["content"][0]["text"]
print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":text}}))
'''


class IsolatedEngineSidecarTests(unittest.TestCase):
    def setUp(self):
        _AgentOSCallback.calls = []
        self.callback = ThreadingHTTPServer(("127.0.0.1", 0), _AgentOSCallback)
        self.callback_thread = threading.Thread(target=self.callback.serve_forever, daemon=True)
        self.callback_thread.start()
        self.folder = tempfile.TemporaryDirectory()
        self.codex = Path(self.folder.name) / "codex"
        self.codex.write_text(FAKE_CODEX, encoding="utf-8")
        self.codex.chmod(self.codex.stat().st_mode | stat.S_IXUSR)
        callback_url = "http://127.0.0.1:%d/internal/isolated-engine/mcp" % self.callback.server_port
        sidecar = IsolatedEngineSidecar(callback_url, codex_binary=str(self.codex), timeout=5)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(sidecar))
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=1)
        self.callback.shutdown()
        self.callback.server_close()
        self.callback_thread.join(timeout=1)
        self.folder.cleanup()

    def _post(self, payload):
        raw = json.dumps(payload).encode()
        connection = HTTPConnection(*self.server.server_address, timeout=8)
        connection.request("POST", "/execute", body=raw, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        value = json.loads(response.read())
        connection.close()
        return response.status, value

    def test_fake_codex_uses_read_only_bridge_end_to_end(self):
        token = "execution-secret"
        status, response = self._post(
            {"prompt": "list the notes", "engine_id": "codex", "token": token, "task_id": "job-7"}
        )

        self.assertEqual(status, 200)
        self.assertEqual(set(response), {"result"})
        self.assertIn("private note", response["result"])
        self.assertEqual(len(_AgentOSCallback.calls), 1, "denied mutation must not reach AgentOS")
        call = _AgentOSCallback.calls[0]
        self.assertEqual(call["path"], "/internal/isolated-engine/mcp")
        self.assertEqual(call["authorization"], "Bearer " + token)
        self.assertEqual(call["task_id"], "job-7")
        self.assertEqual(call["content_type"], "application/json")
        self.assertEqual(
            call["request"],
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "list_notes", "arguments": {}}},
        )

    def test_execute_contract_rejects_other_engine_and_extra_fields(self):
        base = {"prompt": "x", "engine_id": "codex", "token": "t", "task_id": "j"}
        for payload in ({**base, "engine_id": "claude-code"}, {**base, "store": "/owner"}):
            with self.subTest(payload=payload):
                status, response = self._post(payload)
                self.assertEqual(status, 400)
                self.assertEqual(set(response), {"error"})
        self.assertEqual(_AgentOSCallback.calls, [])


if __name__ == "__main__":
    unittest.main()
