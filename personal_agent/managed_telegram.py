"""Narrow managed-control-plane boundary for personal Telegram bots.

The control plane creates and owns Telegram bot credentials.  An owner runtime
receives only a revocable relay capability; message bodies are passed through
for delivery/polling and are never persisted by this client.
"""
from .providers import ProviderError


class ManagedBotProvisioner:
    """Provider interface; deployments must supply the managed relay client."""
    def provision(self):
        raise ProviderError('관리형 Telegram 봇 서비스가 아직 이 AgentOS 환경에 연결되지 않았습니다.')

    def call(self, relay_capability, method, body):
        raise ProviderError('관리형 Telegram 봇 릴레이에 연결할 수 없습니다.')

    def revoke(self, relay_capability):
        # Revocation is best effort: local disabling always takes effect first.
        return None


def provisioned_bot(record):
    """Validate the deliberately small, credential-free provisioning result."""
    if not isinstance(record, dict):
        raise ProviderError('관리형 Telegram 봇 생성 응답이 올바르지 않습니다.')
    username, capability = record.get('username'), record.get('relay_capability')
    if (not isinstance(username, str) or not username or len(username) > 128 or
            not isinstance(capability, str) or not 16 <= len(capability) <= 512):
        raise ProviderError('관리형 Telegram 봇 생성 응답에 필요한 식별자가 없습니다.')
    return username, capability
