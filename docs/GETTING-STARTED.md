# 快速上手

本指南将帮助你完成飞书 AM 工作台的完整配置。无论你是自行使用还是通过 Agent（OpenClaw、Hermes）调用，都能从这里开始。

---

## 前置要求

在开始之前，请确保你具备以下条件：

| 要求 | 说明 | 如何确认 |
|------|------|----------|
| Python 3.10+ | 工作台的运行环境 | 终端输入 `python3 --version` |
| lark-cli | 飞书命令行工具 | 终端输入 `lark-cli --version` |
| 飞书企业版账号 | 需要访问你的企业 Base | 联系企业管理员 |
| 管理员权限 | 首次配置时需要 | 用于开通应用权限 |

---

## 安装步骤

### 第一步：克隆项目

如果你是首次使用，需要先获取项目代码：

```bash
git clone <仓库地址>
cd feishu-am-workbench
```

### 第二步：创建 Python 虚拟环境

为了避免与系统其他 Python 项目冲突，建议使用独立环境：

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

激活成功后，终端提示符前面会显示 `(.venv)` 标记。

### 第三步：安装依赖

```bash
pip install -e .
```

安装过程可能需要 1-3 分钟，视网络情况而定。

### 第四步：配置飞书凭证

飞书 AM 工作台需要访问你的飞书 Base、文档和待办，这些权限通过环境变量配置。

**复制配置文件：**

```bash
cp .env.example .env
```

**编辑 .env 文件，填入你的飞书凭证：**

```bash
# 使用文本编辑器打开
vim .env
# 或者
nano .env
```

`.env.example` 中包含以下配置项：

| 配置项 | 说明 | 如何获取 |
|--------|------|----------|
| `FEISHU_AM_BASE_TOKEN` | 飞书 Base 应用令牌 | 打开 Base 应用，从 URL 复制 |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` | 客户主数据表 ID | 在 Base 中打开客户表，从 URL 复制 |
| `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER` | 客户档案文件夹 | 在 Drive 中找到文件夹，复制链接 |
| `FEISHU_AM_MEETING_NOTES_FOLDER` | 会议纪要文件夹 | 在 Drive 中找到文件夹，复制链接 |
| `FEISHU_AM_TODO_TASKLIST_GUID` | 待办清单 ID | 在飞书待办应用中找到对应清单 |

> **提示**：如果你不确定如何获取某个 ID，可以先跳过该项，运行后面的诊断命令时系统会提示具体缺少什么。

---

## 验证配置

配置完成后，运行诊断命令检查环境是否就绪：

```bash
python -m runtime diagnose
```

诊断结果会显示三项核心能力的状态：

| 能力 | 正常状态 | 异常状态 |
|------|----------|----------|
| `base_access` | `available` | `unavailable` |
| `docs_access` | `available` | `unavailable` |
| `task_access` | `available` | `unavailable` |

如果全部显示 `available`，说明配置成功。如果有异常，系统会提示具体原因。

---

## 快速开始

配置完成后，你可以通过以下方式使用工作台。

### 方式一：通过 Python 模块使用

适合需要在自己系统中集成工作台功能的开发者：

```python
from runtime import dispatch_scene, SceneRequest

# 执行客户状态查询场景
result = dispatch_scene(SceneRequest(
    scene_name="customer-recent-status",
    repo_root=Path("."),
    customer_query="某客户公司",
    inputs={}
))

# 打印结果
print(result)
```

### 方式二：通过命令行使用

适合快速测试或手动执行场景：

```bash
# 查询客户状态
python -m runtime scene customer-recent-status --customer-query "某客户公司"

# 整理会议内容
python -m runtime meeting-write-loop \
    --eval-name "测试" \
    --transcript-file /path/to/transcript.txt \
    --customer-query "某客户公司"

# 会前准备
python -m runtime scene customer-recent-status --customer-query "某客户公司" --topic-text "初次拜访"
```

### 方式三：通过 Agent 使用（推荐）

飞书 AM 工作台设计为主要通过 Agent 使用，如 OpenClaw 或 Hermes。你只需用自然语言描述你的需求：

```
帮我查一下某客户公司最近的状况
刚开完一个客户会议，会议记录是：xxxxx
明天要见某客户，帮我准备一下
```

Agent 会自动调用合适的场景并返回结果。

---

## 场景使用示例

### 场景 1：客户状态查询

当你需要快速了解一个客户的最新状况时使用：

```bash
python -m runtime scene customer-recent-status --customer-query "某客户公司"
```

**输出示例：**

```
客户：某客户公司

【风险】
- 合同即将到期（剩余 15 天）
- 上月联系次数减少

【机会】
- 新项目需求讨论中
- 关键人职级提升，决策链缩短

【待推进】
- [ ] 跟进合同续约
- [ ] 安排与技术负责人会面
```

### 场景 2：会后整理

当你刚结束一场客户会议，需要快速沉淀结论时使用：

```bash
python -m runtime meeting \
    --eval-name "测试" \
    --transcript-file /path/to/transcript.txt \
    --customer-query "某客户公司"
```

工作台会自动：
1. 提取关键人、项目、风险点、机会点
2. 比对客户档案中的历史记录
3. 生成更新建议和待办事项

### 场景 3：会前准备

当你需要为即将到来的客户会议做准备时使用：

```bash
python -m runtime scene customer-recent-status --customer-query "某客户公司" --topic-text "季度业务回顾"
```

**输出示例：**

```
【客户当前状态】
- 上季度合作金额：50万
- 项目进度：Phase 2 开发中
- 最近联系：3周前

【关键人物】
- 张总（CEO）：主要决策人
- 李经理（IT负责人）：技术对接

【来访目的分析】
- 季度回顾，预期讨论下阶段预算

【建议问题】
1. Phase 2 验收标准是否明确？
2. 下季度预算规模？
3. 有无新业务机会？
```

---

## 故障排除

### 问题 1：连接失败

**症状**：诊断命令显示 `base_access: unavailable`

**排查步骤**：

1. **确认 lark-cli 已安装且登录**
   ```bash
   lark-cli --version
   lark-cli auth status
   ```

2. **确认 Base Token 正确**
   打开飞书 Base 应用，检查 URL：
   ```
   https://xxx.feishu.cn/base/xxxxxxxxxx?table=yyyyyyyyyy
   ```
   - URL 中 `/base/` 后面的部分是 `BASE_TOKEN`
   - `?table=` 后面的部分是 `TABLE_ID`

3. **确认网络可以访问飞书**
   ```bash
   ping open.feishu.cn
   ```

### 问题 2：权限不足

**症状**：API 调用返回 403 错误

**排查步骤**：

1. 打开 [飞书开放平台](https://open.feishu.cn/)
2. 进入你的应用后台
3. 检查以下权限是否已开通：
   - `base:app` - 读取 Base 数据
   - `docx:document` - 读写文档
   - `task:task` - 读写任务
4. 开通权限后，需要**发布新版本**使权限生效

### 问题 3：找不到客户档案文件夹

**症状**：提示 `archive folder not found`

**解决方法**：

1. 打开飞书 Drive
2. 找到或创建一个名为「客户档案」的文件夹
3. 点击文件夹右上角的「...」→「复制链接」
4. 链接格式：`https://xxx.feishu.cn/drive/folder/xxxxxxxxxx`
5. 提取最后一段字符（文件夹 Token），填入 `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`

### 问题 4：Python 版本不兼容

**症状**：`SyntaxError` 或 `ImportError`

**解决方法**：

```bash
# 检查 Python 版本
python3 --version

# 如果低于 3.10，需要升级
# macOS:
brew install python@3.11

# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11
```

### 问题 5：虚拟环境激活失败

**症状**：`command not found: python` 或 `No module named 'runtime'`

**解决方法**：

1. 确认虚拟环境已激活（终端前面有 `(.venv)` 标记）
2. 如果没有，重新激活：
   ```bash
   source .venv/bin/activate
   ```
3. 确认使用的是虚拟环境中的 Python：
   ```bash
   which python
   ```

---

## 环境变量说明

工作台运行时依赖以下环境变量，完整说明参见 [CONFIGURATION.md](CONFIGURATION.md)。

### 必需变量

| 变量名 | 说明 |
|--------|------|
| `FEISHU_AM_BASE_TOKEN` | 飞书 Base 应用令牌 |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` | 客户主数据表 ID |
| `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER` | 客户档案文件夹 Token |
| `FEISHU_AM_MEETING_NOTES_FOLDER` | 会议纪要文件夹 Token |
| `FEISHU_AM_TODO_TASKLIST_GUID` | 待办清单 GUID |

### 可选变量

| 变量名 | 说明 |
|--------|------|
| `FEISHU_AM_WORKBENCH_BASE_URL` | 完整 Base URL，可自动解析其他值 |
| `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID` | 待办客户字段 GUID |
| `FEISHU_AM_TODO_PRIORITY_FIELD_GUID` | 待办优先级字段 GUID |

---

## 下一步

配置完成后，你可以进一步了解：

| 文档 | 内容 |
|------|------|
| [SKILL.md](../SKILL.md) | 完整的 7 个场景详解和使用场景 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构和核心组件说明 |
| [CONFIGURATION.md](CONFIGURATION.md) | 环境变量和配置项详解 |
| [WORKFLOW.md](../WORKFLOW.md) | 9 步核心工作流分步说明 |

如果你在配置过程中遇到问题，可以：

1. 查看上方「故障排除」章节
2. 检查 [CONFIGURATION.md](CONFIGURATION.md) 中的常见配置问题
3. 在 GitHub Issues 中搜索类似问题
