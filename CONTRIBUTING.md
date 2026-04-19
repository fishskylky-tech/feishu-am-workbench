# 贡献指南

<!-- generated-by: gsd-doc-writer -->

感谢你对飞书 AM 工作台的关注！我们欢迎各种形式的贡献，包括但不限于报告问题、提供建议、改进文档和代码贡献。

---

## 贡献方式

| 方式 | 说明 |
|------|------|
| **报告问题** | Bug 报告、功能请求、Schema 漂移 |
| **改进文档** | 修复错别字、补充示例、完善说明 |
| **代码贡献** | 修复 Bug、实现新功能、优化性能 |
| **分享反馈** | 用户体验改进建议 |

---

## 开发环境配置

详细的环境配置说明请参考 [GETTING-STARTED.md](GETTING-STARTED.md)。

### 基础要求

- Python 3.10+（建议 3.11 或 3.12）
- lark-cli 最新稳定版
- 飞书账号（需具备 Base、Drive 和 Task 的访问权限）

### 快速设置

1. **克隆仓库**

```bash
git clone <仓库地址>
cd feishu-am-workbench
```

2. **创建虚拟环境**

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -e .
```

4. **配置环境变量**

参考 `config/example.yaml` 创建 `.env` 文件：

```bash
FEISHU_AM_BASE_TOKEN=<你的 Base Token>
FEISHU_AM_CUSTOMER_MASTER_TABLE_ID=<客户主数据表 ID>
FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER=<客户归档文件夹 ID>
FEISHU_AM_MEETING_NOTES_FOLDER=<会议记录文件夹 ID>
FEISHU_AM_TODO_TASKLIST_GUID=<待办清单 ID>
```

5. **诊断环境**

```bash
python3 -m runtime .
```

确认三项核心能力状态均为 `available`：

- `base_access: available` — 能读取飞书 Base
- `docs_access: available` — 能读取飞书云文档
- `task_access: available` — 能读写飞书任务

### 运行测试

```bash
pytest
```

---

## 代码规范

### Python 代码风格

- 遵循 **PEP 8** 规范
- 使用有意义的变量和函数命名
- 添加必要的文档字符串
- 保持函数短小专注（建议 < 50 行）

### 提交信息格式

```
<类型>: <描述>

<可选正文>
```

类型可选值：

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构 |
| `docs` | 文档更新 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |
| `perf` | 性能优化 |
| `ci` | CI/CD 相关 |

### 分支命名规范

```
feature/<功能名称>
fix/<问题描述>
docs/<文档类型>
```

---

## Pull Request 流程

### 提交 PR

1. **Fork 仓库** — 点击 GitHub 页面右上角的 Fork 按钮

2. **创建功能分支**

```bash
git checkout -b feature/my-feature
# 或
git checkout -b fix/bug-description
```

3. **开发并测试**

```bash
# 进行代码修改
pytest  # 确保所有测试通过
```

4. **提交代码**

```bash
git add .
git commit -m "feat: 添加新功能描述"
git push -u origin feature/my-feature
```

5. **创建 Pull Request**

在 GitHub 上创建 PR，参考 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md) 填写以下信息：

- **本次变更** — 描述这次改了什么
- **变更原因** — 解决了什么真实问题
- **影响范围** — 勾选受影响的模块
- **验证情况** — 确认测试通过
- **剩余风险** — 列出不确定的部分

### PR 审查要点

审查者会关注以下方面：

- 代码质量和可读性
- 测试覆盖是否充分
- 文档是否同步更新
- 是否有 breaking change
- 是否符合项目的安全模型

### 合并标准

PR 可被合并当且仅当：

- 所有 CI 检查通过
- 至少有一个审查者批准
- 没有未解决的 CRITICAL 或 HIGH 级别问题

---

## Issue 报告指南

### Issue 类型

本项目使用两种主要 Issue 模板：

#### Skill 变更 ([skill-change.md](.github/ISSUE_TEMPLATE/skill-change.md))

适用于行为、规则、映射或工作流调整：

- 背景：当前工作流发生了什么变化
- 问题：当前 skill 哪部分不对或不完整
- 期望行为：你希望 skill 改成什么样
- 影响范围：涉及哪些模块
- 真实例子：尽量提供具体客户、表、字段等

#### Schema 漂移 ([schema-drift.md](.github/ISSUE_TEMPLATE/schema-drift.md))

适用于飞书 Base 或任务清单字段变化：

- 漂移类型：字段改名、删除、新增、选项变化等
- 发生位置：Base/表/字段
- 旧状态 vs 新状态
- 对 skill 的影响
- 期望的安全行为

### 报告问题时请包含

- 清晰的问题描述
- 复现步骤
- 期望行为 vs 实际行为
- 环境详情（Python 版本、lark-cli 版本等）
- 相关截图或日志（如有）

---

## 项目结构参考

| 目录 | 说明 |
|------|------|
| `runtime/` | Python 运行时模块（场景执行、网关、数据写入等） |
| `scenes/` | 场景配置（expert-cards.yaml 定义输入输出审计点） |
| `references/` | 26 个参考文档（字段语义、写入规则、错误处理等） |
| `config/` | 配置模板 |
| `tests/` | 测试套件 |
| `evals/` | 评估用例 |

---

## 联系方式

- **GitHub Issues** — 用于报告问题和功能请求
- **GitHub Discussions** — 用于讨论和提问

---

## 许可

通过贡献代码，你同意你的贡献将按照 [MIT License](LICENSE) 的条款进行许可。

