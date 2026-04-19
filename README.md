# 飞书 AM 工作台

<!-- generated-by: gsd-doc-writer -->

飞书 AM 工作台是一个面向客户经理（AM）的智能工作技能，帮助你在飞书上高效完成客户经营工作。

**服务对象：** AM 本身，以及 AM 的智能助手（如 OpenClaw、Hermes 等 Agent）

---

## 工作原理

```
用户输入 → 场景识别 → 上下文拉取 → 实体提取
     ↓                                          ↓
建议审核 ← 分析与判断 ← 结构化摘要
     ↓
用户确认
     ↓
飞书写入（如已确认）
     ↓
结果报告
```

**核心原则：先读清楚，再给建议，最后才行动。**

---

## 五大特点

| 特点 | 说明 |
|------|------|
| **先理解，再判断** | 工作台会先拉取客户的最新上下文——包括最近的联系记录、合同进展、关系变化——然后再给出分析和建议 |
| **先建议，再行动（recommendation-first）** | 所有变更都会先以"建议态"呈现，等你确认后才会真正写回到飞书 |
| **操作有痕迹** | 每一次读、写、更改都有明确的记录和范围，不会发生意外的大范围修改 |
| **实时数据优先（live-first）** | 优先从飞书实时拉取数据，仅在无法访问时才回退到本地文件 |
| **Schema 安全门控** | 写入前验证字段类型、表结构，发现漂移时主动暴露而非静默失败 |

---

## 7 个注册场景

### 1. 会后整理（post-meeting-synthesis）

把会议内容粘贴进来，自动分析并给出档案更新建议。

**输出：** 客户状态更新（风险、机会、关键变化）+ 待办事项 + 档案更新建议

**适合场景：** 刚结束一场客户会议，需要快速沉淀结论和下一步。

---

### 2. 客户状态查询（customer-recent-status）

输入客户名称，快速获得该客户的当前全貌。

**输出：** 四维度客户全貌——风险和机会、关键人关系变化、项目进展、待推进事项

**适合场景：** 明天要见客户，今天快速了解这家客户最近发生了什么。

---

### 3. 档案刷新（archive-refresh）

从多个资料来源自动更新客户档案。

**输出：** 客户历史弧线 + 整合的更新建议

**适合场景：** 资料分散在多个飞书文档里，需要统一归档。

---

### 4. 待办管理（todo-capture-and-update）

自动从会议和文档中提取待办事项，分类整理。

**输出：** 分类待办列表 + 重复检测 + 创建/更新建议

**适合场景：** 会议纪要里的行动项需要统一管理，避免遗漏或重复。

---

### 5. 客户群分析（cohort-scan）

对一类客户进行聚合分析，发现整体风险和机会。

**输出：** 客户群体风险汇总 + 机会聚合分析

**适合场景：** 需要了解某一类客户的整体状况，而非单个客户。

---

### 6. 会前准备（meeting-prep）

输入客户名称和会议目的，自动生成七维度简报。

**输出：**
1. 客户当前状态
2. 关键人物关系
3. 来访目的分析
4. 可能的风险点
5. 可能的机会点
6. 建议的问题
7. 后续推进建议

**适合场景：** 第一次见新客户，或者见重要客户前需要全面准备。

---

### 7. 提案生成（proposal）

输入你的目标和已有的客户材料，自动生成结构化提案草案。

**输出：**
1. 目标是什么
2. 核心判断和建议
3. 主要叙事逻辑
4. 需要争取的资源
5. 还有哪些问题需要确认

**适合场景：** 需要给客户写一份正式的方案或报告，不知道从哪里开始。

---

## 快速上手

### 第一步：确认前置条件

- Python 3.10+（建议 3.11 或 3.12）
- lark-cli 最新稳定版（通过 `lark-cli --version` 确认）
- 已完成飞书登录授权，具备目标 Base、Drive 和 Task 的访问权限

### 第二步：配置环境变量

在仓库根目录创建 `.env` 文件，参考 [config/example.yaml](config/example.yaml)：

```bash
FEISHU_AM_BASE_TOKEN=<你的 Base Token>
FEISHU_AM_CUSTOMER_MASTER_TABLE_ID=<客户主数据表 ID>
FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER=<客户归档文件夹 ID>
FEISHU_AM_MEETING_NOTES_FOLDER=<会议记录文件夹 ID>
FEISHU_AM_TODO_TASKLIST_GUID=<待办清单 ID>
```

### 第三步：诊断环境

```bash
python3 -m runtime .
```

确认三项核心能力状态均为 `available`：
- `base_access: available` — 能读取飞书 Base
- `docs_access: available` — 能读取飞书云文档
- `task_access: available` — 能读写飞书任务

### 第四步：开始使用

配置完成后，通过 Agent（OpenClaw、Hermes 等）即可调用上述 7 个场景。

---

## 目录结构

| 目录 | 说明 |
|------|------|
| `runtime/` | Python 运行时模块（场景执行、网关、数据写入等） |
| `scenes/` | 场景配置（post-meeting-synthesis 和 customer-recent-status 有 expert-cards.yaml） |
| `references/` | 26 个参考文档（字段语义、写入规则、错误处理等） |
| `config/` | 配置模板 |
| `tests/` | 测试套件 |
| `evals/` | 评估用例 |

---

## 相关文档

| 文档 | 内容 |
|------|------|
| [GETTING-STARTED.md](GETTING-STARTED.md) | 详细的环境配置和快速体验指南 |
| [SKILL.md](SKILL.md) | Skill 定义、7 个场景详解、核心工作流 |
| [WORKFLOW.md](WORKFLOW.md) | 10 步核心工作流分步说明 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计（即将提供） |
| [CONFIGURATION.md](CONFIGURATION.md) | 环境变量和配置项详解（即将提供） |
| [SECURITY-MODEL.md](SECURITY-MODEL.md) | 安全模型和写入保护机制 |

---

## License

MIT License - 详见 [LICENSE](LICENSE)
