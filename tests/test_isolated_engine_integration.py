import json
import secrets
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from personal_agent.isolated_engine_gateway import IsolatedEngineGateway
from personal_agent.isolated_engine_gateway import InvalidGatewayEndpoint
from personal_agent.quickstart import ISOLATED_MCP_PATH, configured_service, make_handler
from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart_store import QuickStore
from personal_agent.subscription_engines import SubscriptionEngines


class _EngineHandler(BaseHTTPRequestHandler):
    agentos_address = None
    callbacks = []
    engine_payloads = []

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length))
        type(self).engine_payloads.append(payload)
        rpc = {'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call',
               'params': {'name': 'list_notes', 'arguments': {}}}
        raw_rpc = json.dumps(rpc, separators=(',', ':')).encode()
        connection = HTTPConnection(*type(self).agentos_address, timeout=2)
        connection.request('POST', ISOLATED_MCP_PATH, body=raw_rpc, headers={
            'Authorization': 'Bearer ' + payload['token'],
            'X-AgentOS-Task-ID': payload['task_id'],
            'Content-Type': 'application/json',
        })
        response = connection.getresponse()
        callback = json.loads(response.read())
        connection.close()
        type(self).callbacks.append((payload, rpc, response.status, callback))
        result = callback['result']['content'][0]['text']
        raw = json.dumps({'result': result}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


class IsolatedEngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        _EngineHandler.callbacks = []
        _EngineHandler.engine_payloads = []
        self.engine = ThreadingHTTPServer(('127.0.0.1', 0), _EngineHandler)
        self.engine_thread = threading.Thread(target=self.engine.serve_forever, daemon=True)
        self.engine_thread.start()
        self.folder = tempfile.TemporaryDirectory()
        self.store = QuickStore(Path(self.folder.name) / 'data')
        gateway = IsolatedEngineGateway(
            f'http://127.0.0.1:{self.engine.server_port}/execute')
        engines = SubscriptionEngines(finder=lambda _name: '/runtime/codex', clock=lambda: 1)
        self.service = AgentService(self.store, subscription_engines=engines,
                                    isolated_engine_adapter=gateway)
        self.agentos = ThreadingHTTPServer(
            ('127.0.0.1', 0), make_handler(self.service, ['public.example.test']))
        self.agentos_thread = threading.Thread(target=self.agentos.serve_forever, daemon=True)
        self.agentos_thread.start()
        _EngineHandler.agentos_address = self.agentos.server_address
        self.service.connect_subscription_engine(
            {'engine': 'codex', 'officially_authenticated': True})

    def tearDown(self):
        self.agentos.shutdown()
        self.agentos.server_close()
        self.agentos_thread.join(timeout=1)
        self.engine.shutdown()
        self.engine.server_close()
        self.engine_thread.join(timeout=1)
        self.folder.cleanup()

    def _callback(self, rpc, *, token='', task_id='', headers=None):
        raw = rpc if isinstance(rpc, bytes) else json.dumps(rpc).encode()
        request_headers = {'Content-Type': 'application/json'}
        if token:
            request_headers['Authorization'] = 'Bearer ' + token
        if task_id:
            request_headers['X-AgentOS-Task-ID'] = task_id
        request_headers.update(headers or {})
        connection = HTTPConnection(*self.agentos.server_address, timeout=2)
        connection.request('POST', ISOLATED_MCP_PATH, body=raw, headers=request_headers)
        response = connection.getresponse()
        body = json.loads(response.read())
        connection.close()
        return response.status, body

    def test_selected_subscription_engine_uses_token_bound_read_only_proxy(self):
        with self.store.db() as db:
            db.execute('INSERT INTO notes VALUES (?,?,?)', ('note-1', 'Isolated note', 1))
        job_id = self.store.enqueue('show my notes', 'isolated-integration')

        self.assertTrue(self.service.run_one())

        job = self.store.job(job_id)
        self.assertEqual(job['provider'], 'subscription')
        self.assertIn('Isolated note', job['response'])
        payload, rpc, status, callback = _EngineHandler.callbacks[0]
        self.assertEqual(status, 200)
        self.assertEqual(callback['id'], 7)
        self.assertEqual(payload['task_id'], job_id)
        self.assertEqual(set(payload), {'prompt', 'engine_id', 'token', 'task_id'})
        self.assertEqual(len(__import__('base64').urlsafe_b64decode(payload['token'] + '==')), 32)
        for forbidden in ('store', 'profile', 'path', 'home', 'credential'):
            self.assertNotIn(forbidden, json.dumps(payload).lower())

        replay_status, replay = self._callback(rpc, token=payload['token'], task_id=job_id)
        self.assertEqual(replay_status, 200)
        self.assertEqual(replay['error']['code'], -32001)

    def test_callback_rejects_bad_token_browser_auth_and_other_tools(self):
        rpc = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
               'params': {'name': 'list_notes', 'arguments': {}}}
        status, bad = self._callback(rpc, token=secrets.token_urlsafe(32), task_id='job')
        self.assertEqual(status, 200)
        self.assertEqual(bad['error']['code'], -32001)

        status, unauthenticated = self._callback(
            rpc, task_id='job', headers={'Cookie': 'agentos_session=not-an-engine-token'})
        self.assertEqual(status, 401)
        self.assertIn('error', unauthenticated)

        for name, arguments in (
            ('save_note', {'content': 'no'}),
            ('web_search', {'query': 'no'}),
        ):
            with self.subTest(tool=name):
                unavailable = dict(rpc)
                unavailable['params'] = {'name': name, 'arguments': arguments}
                status, rejected = self._callback(
                    unavailable, token=secrets.token_urlsafe(32), task_id='job')
                self.assertEqual(status, 200)
                self.assertEqual(rejected['error']['code'], -32601)

        status, public = self._callback(
            rpc, token=secrets.token_urlsafe(32), task_id='job',
            headers={'Host': 'public.example.test'})
        self.assertEqual(status, 403)
        self.assertIn('error', public)

    def test_startup_uses_only_explicit_safe_isolated_engine_environment(self):
        ordinary = configured_service(self.store, {})
        self.assertIsNone(ordinary.isolated_engine_adapter)
        self.assertEqual(ordinary.settings()['subscription_execution']['mode'],
                         'bounded-agentos-mcp')

        isolated = configured_service(
            self.store,
            {'AGENTOS_ISOLATED_ENGINE_URL': 'http://127.0.0.1:9876/execute'},
        )
        self.assertIsInstance(isolated.isolated_engine_adapter, IsolatedEngineGateway)
        self.assertEqual(isolated.settings()['subscription_execution']['mode'],
                         'isolated-agentos-mcp')

        with patch('personal_agent.isolated_engine_gateway.HTTPConnection',
                   side_effect=AssertionError('network must not be contacted')):
            with self.assertRaises(InvalidGatewayEndpoint):
                configured_service(
                    self.store,
                    {'AGENTOS_ISOLATED_ENGINE_URL': 'http://example.com:9876/execute'},
                )


if __name__ == '__main__':
    unittest.main()
