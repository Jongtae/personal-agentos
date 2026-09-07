"""Policy-owned, local-first assistant orchestration for MP1 capabilities.

Adapters are injected and deliberately have no HTTP or channel surface.  This
module is the only boundary allowed to select and invoke them.
"""
import time

from .capabilities import CapabilityRegistry


class AssistantRequestError(ValueError):
    pass


class PersonalAssistantOrchestrator:
    def __init__(self, store, *, drive=None, a2a=None, calendar=None, now=time.time):
        self.store, self.drive, self.a2a, self.calendar, self.now = store, drive, a2a, calendar, now
        self.registry = CapabilityRegistry(store)

    def _evidence(self, kind, state, recovery=None, **metadata):
        """Persist only lifecycle metadata; never prompts, secrets, or content."""
        rows = self.store.config('personal_assistant_evidence', [])
        event = {'kind': kind, 'state': state, 'at': self.now()}
        if recovery:
            event['recovery'] = recovery
        event.update({key: value for key, value in metadata.items() if value not in (None, '', [], {})})
        rows.append(event)
        self.store.put('personal_assistant_evidence', rows[-100:])
        return event

    @staticmethod
    def _request(value):
        if not isinstance(value, dict) or not isinstance(value.get('message'), str) or not value['message'].strip():
            raise AssistantRequestError('자연어 요청이 필요합니다.')
        owner = value.get('owner_id')
        if not isinstance(owner, str) or not owner:
            raise AssistantRequestError('소유자 식별이 필요합니다.')
        return value['message'].strip(), owner

    @staticmethod
    def classify(message):
        """Classify only a deliberately small, owner-readable MP1 vocabulary.

        The optional structured fields accompanying a channel request are data
        for a selected action, never authority to select it.  A model cannot
        turn an arbitrary request into a delegation or an external action by
        supplying an `intent` value.
        """
        if message.startswith('Drive 검색:'):
            return 'drive-search'
        if message.startswith('A2A 위임:'):
            return 'a2a-delegate'
        if message.startswith('일정 초안:'):
            return 'calendar-create'
        if any(token in message for token in ('내 메모', '개인 공간', '저장한 결과')):
            return 'local'
        return 'unknown'

    def handle(self, value):
        """Classify one owner request and return an owner-safe result envelope.

        Selection comes from the owner's message; only the explicit Korean
        delegation form can invoke an A2A peer.  It avoids treating a model
        suggestion or a channel-supplied action field as authorization.
        """
        message, owner = self._request(value)
        intent = self.classify(message)
        if intent == 'local':
            space = self.store.personal_space()
            evidence = self._evidence('local', 'completed', memory_count=space['memory_count'], result_count=space['result_count'])
            return {'state': 'completed', 'response': '개인 공간의 기억과 저장 결과를 확인했습니다.', 'evidence': evidence}
        if intent == 'drive-search':
            try:
                self.registry.require_enabled('google-drive-read', 'read')
                if self.drive is None:
                    raise AssistantRequestError('Google Drive 연결을 먼저 설정하세요.')
                rows = self.drive.search(value.get('query', message))
                safe = [{'id': row.get('id', ''), 'name': row.get('name', ''), 'mime_type': row.get('mime_type', '')} for row in rows[:20] if isinstance(row, dict)]
                evidence = self._evidence('drive-search', 'completed', result_count=len(safe))
                return {'state': 'completed', 'response': 'Google Drive에서 관련 파일을 찾았습니다.', 'sources': safe, 'evidence': evidence}
            except (ValueError, AssistantRequestError) as exc:
                evidence = self._evidence('drive-search', 'blocked', 'Drive 연결 상태를 확인하거나 다시 연결하세요.')
                return {'state': 'blocked', 'response': str(exc), 'evidence': evidence}
        if intent == 'a2a-delegate':
            try:
                self.registry.require_enabled('compatibility-a2a-peer', 'delegate')
                if self.a2a is None:
                    raise AssistantRequestError('A2A test peer가 연결되지 않았습니다.')
                delegation = self.a2a.delegate({'explicit': True, 'prompt': message})
                evidence = self._evidence('a2a-delegate', 'requested', delegation_id=delegation['id'])
                return {'state': 'requested', 'response': '명시한 작업을 호환성 Agent에 위임했습니다.', 'delegation_id': delegation['id'], 'evidence': evidence}
            except (ValueError, AssistantRequestError) as exc:
                evidence = self._evidence('a2a-delegate', 'blocked', '연결 상태를 확인하거나 로컬 답변을 사용하세요.')
                return {'state': 'blocked', 'response': str(exc), 'evidence': evidence}
        if intent == 'calendar-create':
            try:
                self.registry.require_enabled('google-calendar-create', 'calendar.events')
                if self.calendar is None or not isinstance(value.get('event'), dict):
                    raise AssistantRequestError('일정 초안 정보를 확인하세요.')
                draft = self.calendar.draft(value['event'])
                evidence = self._evidence('calendar-draft', 'awaiting-approval', draft_id=draft['id'])
                return {'state': 'awaiting-approval', 'response': '일정 초안을 만들었습니다. 내용을 확인한 뒤 승인하세요.', 'draft': draft, 'evidence': evidence}
            except (ValueError, AssistantRequestError) as exc:
                evidence = self._evidence('calendar-draft', 'blocked', '일정 연결 상태와 초안 정보를 확인하세요.')
                return {'state': 'blocked', 'response': str(exc), 'evidence': evidence}
        evidence = self._evidence('unknown', 'fallback', '요청을 더 구체적으로 설명하거나 사용 가능한 연결을 확인하세요.')
        return {'state': 'fallback', 'response': '이 요청에 사용할 검토된 capability를 찾지 못했습니다.', 'evidence': evidence}
