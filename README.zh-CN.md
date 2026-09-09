# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS 是以所有者掌控的文件和文件夹为中心的本地优先个人智能体。它保留源材料，在对话和工作中使用材料，将可复用结果保存为普通文件，并在 Mac 上按用户隔离的运行时中保留策略、工作队列、审批、证据和恢复状态。

体验是对话和工作（包括个人 Telegram 机器人），而不是要求反复选择已连接材料的文件管理器。AgentOS 不只是消息中继：它选择助手、实施工具和数据边界、持久化工作状态，并记录结果及其证据。

## 当前方向

文件和文件夹是材料基础；对话和工作是体验。连接的参考文件夹默认只读，AgentOS 仅在所有者授权的受管工作空间中写入新材料和结果。原件与提取文本、摘要、草稿和最终记录保持区分；可重建的搜索索引与持久的工作、审批、证据、恢复和认证状态分离。外部 AI、消息工具或其他智能体传输需要独立的策略/审批边界。

版本 1.0.3 以及 Hub v2/Drive 的交付记录仍作为历史证据保留，并非当前产品选择器。当前活动计划是 [#314 文件和文件夹个人工作空间](https://github.com/Jongtae/personal-agentos/issues/314)，其首个实现尚未开始。Drive 等服务连接器是可选的导入/服务操作，不是存储基础；AgentOS 不新增云同步引擎或中央认证服务。

所有者状态可通过 `scripts/agentos-backup.py DATA ARCHIVE` 和 `scripts/agentos-restore.py ARCHIVE EMPTY_DATA` 在本地运行时之间迁移。归档经过完整性检查，包含记忆、工作证据和已审核的助手声明；不包含凭据、会话、本地文件夹授权、引擎/模型选择或 Telegram 配对。请显式认领并重新连接目标运行时。

## 开发安装

```sh
brew install jongtae/agentos/agentos
agentos start
```

在 v2 面向消费者的安装程序完成前，Homebrew 路径仍面向开发者和自托管用户。

## 治理

每个活跃的 Hub v2 里程碑都有 GitHub issue、分支、PR、自动化验证和具名的真实验收证据。实现前请阅读 [AGENTS.md](AGENTS.md)、[PRD.md](PRD.md)、[TASKS.md](TASKS.md) 和[路线图](docs/roadmap.md)。
