"""Validated declarations for AgentOS roles and bounded local tools."""
import json
from pathlib import Path

HOST_ACTIONS={'web_search','weather','list_roots','find_files','read_file','list_notes','save_note','list_agents','delegate_agent'}

BUILTIN_MANIFEST={'version':1,'tools':[{'id':name,'host_action':name,'mode':'read_only' if name not in ('save_note','delegate_agent') else 'bounded_write'} for name in sorted(HOST_ACTIONS)],'roles':[{'id':'researcher','name':'조사 에이전트','permissions':['read_only']},{'id':'reviewer','name':'검토 에이전트','permissions':['read_only']}]}

def validate(manifest):
 if not isinstance(manifest,dict) or manifest.get('version')!=1:raise ValueError('매니페스트 버전 1이 필요합니다.')
 tools=manifest.get('tools',[]);roles=manifest.get('roles',[])
 if not isinstance(tools,list) or not isinstance(roles,list):raise ValueError('tools와 roles는 목록이어야 합니다.')
 ids=set()
 for tool in tools:
  if not isinstance(tool,dict) or not isinstance(tool.get('id'),str) or tool['id'] in ids or tool.get('host_action') not in HOST_ACTIONS:raise ValueError('허용하지 않은 도구 매니페스트입니다.')
  ids.add(tool['id'])
 for role in roles:
  if not isinstance(role,dict) or not isinstance(role.get('id'),str) or not isinstance(role.get('permissions',[]),list) or any(permission not in ('read_only','bounded_write') for permission in role['permissions']):raise ValueError('허용하지 않은 역할 매니페스트입니다.')
 return manifest

def load(path):
 return validate(json.loads(Path(path).read_text()))
