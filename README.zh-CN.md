# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS 是一个本地优先的个人智能体运行时。它将所有者的记忆、上下文、工具权限、工作队列、审批和证据保存在其 Mac 上按用户隔离的运行时中，同时使用 Codex 或 Claude Code 等已连接的 AI 执行引擎完成工作。

日常使用入口是个人 Telegram 机器人。AgentOS 不只是消息中继：它选择助手、实施工具和数据边界、持久化工作状态，并记录结果及其证据。

## 当前基线

版本 1.0.3 仍是持续维护的自托管 API 模型预览版。Hub v2 是当前产品路线图：订阅连接的执行引擎、由所有者在 BotFather 创建并私密配对到本地运行时的 Telegram 机器人，以及选择加入的本地上下文收件箱。机器人令牌仅输入一次，只保存在本地私密连接存储中，并会从设置、事件、导出、日志和验收报告中排除。请参阅 [Hub v2 产品基础](docs/agentos-hub-v2.ko.md)。

所有者状态可通过 `scripts/agentos-backup.py DATA ARCHIVE` 和 `scripts/agentos-restore.py ARCHIVE EMPTY_DATA` 在本地运行时之间迁移。归档经过完整性检查，包含记忆、工作证据和已审核的助手声明；不包含凭据、会话、本地文件夹授权、引擎/模型选择或 Telegram 配对。请显式认领并重新连接目标运行时。

## 开发安装

```sh
brew install jongtae/agentos/agentos
agentos start
```

在 v2 面向消费者的安装程序完成前，Homebrew 路径仍面向开发者和自托管用户。

## 治理

每个活跃的 Hub v2 里程碑都有 GitHub issue、分支、PR、自动化验证和具名的真实验收证据。实现前请阅读 [AGENTS.md](AGENTS.md)、[PRD.md](PRD.md)、[TASKS.md](TASKS.md) 和[路线图](docs/roadmap.md)。
