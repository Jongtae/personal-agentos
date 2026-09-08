"""Minimal stdio MCP bridge; AgentOS, never the engine, owns tool execution."""
import argparse
import json
import sys
import time

from .agent_runtime import Capabilities
from .bounded_execution import AgentOSMcpTools, ExecutionError
from .local_tools import LocalTools
from .quickstart_store import QuickStore


def _send(value):
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n"); sys.stdout.flush()


def serve(data, job_id):
    store = QuickStore(data)
    def record(tool, status, detail):
        with store.db() as db:
            db.execute('INSERT INTO tool_events(job_id,tool,status,detail,created) VALUES (?,?,?,?,?)', (job_id,tool,status,detail,time.time()))
    tools = AgentOSMcpTools(Capabilities(store, None, {}, '', job_id, record, network=LocalTools(), document_access=False,
                                         allowed_tools={'list_notes','save_note','web_search'}))
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method, ident = request.get('method'), request.get('id')
            if method == 'initialize': result = {'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'agentos','version':'1'}}
            elif method == 'tools/list': result = {'tools': tools.definitions()}
            elif method == 'tools/call':
                params = request.get('params', {}); value = tools.call(params.get('name'), params.get('arguments', {}))
                record(params.get('name'), 'succeeded', json.dumps({'scope':'subscription-mcp-bridge'}, ensure_ascii=False))
                result = {'content':[{'type':'text','text':json.dumps(value, ensure_ascii=False)}]}
            elif method == 'notifications/initialized': continue
            else: raise ExecutionError('Unsupported MCP request.')
            if ident is not None: _send({'jsonrpc':'2.0','id':ident,'result':result})
        except (ValueError, ExecutionError, TypeError) as exc:
            if isinstance(locals().get('request'),dict) and request.get('id') is not None:
                _send({'jsonrpc':'2.0','id':request['id'],'error':{'code':-32602,'message':'AgentOS MCP request rejected.'}})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--data',required=True); parser.add_argument('--job',required=True)
    args=parser.parse_args(); serve(args.data, args.job)
