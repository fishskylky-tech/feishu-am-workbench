# Configuration

本文档说明 `feishu-am-workbench` 的本地运行时配置边界。

核心原则只有两条：

1. 真实环境信息留在本地，不进仓库
2. skill 的业务规则与个人飞书环境配置分离

## 1. 当前配置来源

当前仓库的运行时配置主要来自两类来源：

### 进程环境变量

优先级最高。`FEISHU_AM_*` 如果已经在 shell 中 export，runtime 会直接使用它们。

### 仓库根目录 `.env`

`runtime/env_loader.py` 会在运行入口显式加载 `.env`，把其中的 `FEISHU_AM_*` 补充到当前进程环境。

规则是：

- 显式环境变量优先
- `.env` 只做补充
- `.env` 不应提交到仓库

## 2. 当前常见配置项

当前最常见的本地输入包括：

- `FEISHU_AM_WORKBENCH_BASE_URL`
- `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
- `FEISHU_AM_MEETING_NOTES_FOLDER`
- `FEISHU_AM_TODO_TASKLIST_GUID`
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID`
- `FEISHU_AM_TODO_PRIORITY_FIELD_GUID`

这些值共同决定：

- runtime 能否解析 Base
- 能否定位客户档案和会议纪要目录
- Todo writer 能否完成 preflight 与写入

## 3. 配置模板与示例

仓库中已经提供两类公开配置资产：

- [config/template.yaml](config/template.yaml)
  - 通用模板，适合定义应该有哪些配置块
- [config/example.yaml](config/example.yaml)
  - 脱敏示例，适合参考字段和结构

这两份文件可以进仓库，因为它们不应该包含任何真实 token 或真实资源 id。

## 4. 相关配置契约

如果你要理解更完整的配置设计，继续看：

- [CONFIG-MODEL.md](CONFIG-MODEL.md)
  - 面向未来多人/多 workspace 的配置分层设计
- [references/live-schema-preflight.md](references/live-schema-preflight.md)
  - 写前 preflight 的 live 契约
- [references/schema-compatibility.md](references/schema-compatibility.md)
  - schema drift 与兼容策略

## 5. 不应提交的内容

以下内容都不应该进入 git：

- 真实 Base token
- 真实 folder token
- 真实 tasklist guid
- 任何能直接定位个人飞书工作台资源的私有 id
- 本地 `.env`

## 6. 常见排查顺序

如果 runtime 行为异常，建议按顺序排查：

1. `.env` 是否存在且格式正确
2. shell 中是否已有同名 `FEISHU_AM_*` 变量覆盖了 `.env`
3. `python3 -m runtime .` 的 capability 结果是什么
4. 飞书 scope 是否足够
5. 对应 Base / Drive / Task 资源是否仍存在

## 7. 当前边界

当前仓库已经具备模板和本地运行时加载能力，但还不是一个通用的多人配置平台。

也就是说：

- 现在已经适合个人环境稳定运行
- 未来可以演进为多 workspace 配置模型
- 但这不是当前 phase 的主线目标

## Environment Variables

当前仓库里能被代码直接验证的运行时环境变量如下。表中的“必需”指的是要拿到完整 live capability 所需的最小集合，不等同于进程启动时会立即抛错。

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `FEISHU_AM_WORKBENCH_BASE_URL` | 可选 | 无 | Base 链接回退源。如果 `FEISHU_AM_BASE_TOKEN` 或 `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` 未显式设置，runtime 会从 URL 路径解析 base token，并从 `table` 查询参数解析客户主数据表 id。 |
| `FEISHU_AM_BASE_TOKEN` | 条件必需 | 回退到 `FEISHU_AM_WORKBENCH_BASE_URL` 中解析出的 base token | live Base 读取与 schema preflight 的私有 Base token。若未设置，`ResourceResolver` 会把 `base_token` 标记为缺失。 |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` | 可选 | 回退到 `FEISHU_AM_WORKBENCH_BASE_URL` 中的 `table` 参数 | 客户主数据表 id。主要用于构造 live table target。 |
| `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER` | 必需 | 无 | 客户档案目录 token。缺失时 docs capability 会降级，诊断会提示补齐该变量。 |
| `FEISHU_AM_MEETING_NOTES_FOLDER` | 必需 | 无 | 会议纪要目录 token。缺失时 docs capability 会降级，诊断会提示补齐该变量。 |
| `FEISHU_AM_TODO_TASKLIST_GUID` | 必需 | 无 | Todo tasklist guid。缺失时 task capability 会降级，写入路径无法建立完整 preflight。 |
| `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID` | 可选 | 空值 | Todo 中“客户”自定义字段 guid 覆盖项。`.env.example` 明确把它标为 optional override。 |
| `FEISHU_AM_TODO_PRIORITY_FIELD_GUID` | 可选 | 空值 | Todo 中“优先级”自定义字段 guid 覆盖项。`.env.example` 明确把它标为 optional override。 |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE` | 可选 | 优先使用已解析的 `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID`，否则回退到 `客户主数据` | live Base 中客户主数据表的目标名覆盖项。 |
| `FEISHU_AM_CONTACT_LOG_TABLE` | 可选 | `客户联系记录` | live Base 中联系记录表的目标名覆盖项。 |
| `FEISHU_AM_ACTION_PLAN_TABLE` | 可选 | `行动计划` | live Base 中行动计划表的目标名覆盖项。 |

## Config File Format

当前 runtime 真正会自动读取的配置文件只有仓库根目录 `.env`。`runtime/env_loader.py` 的实现是一个极简 loader，支持的语法边界如下：

- 只读取简单的 `KEY=VALUE` 行
- 允许以 `export KEY=VALUE` 形式书写
- 允许单引号或双引号包裹 value
- 忽略空行、注释行和不含 `=` 的行
- 默认不覆盖 shell 中已经存在的同名环境变量

最小可用示例：

```bash
FEISHU_AM_BASE_TOKEN=app_example_base_token
FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER=fld_customer_archive_example
FEISHU_AM_MEETING_NOTES_FOLDER=fld_meeting_notes_example
FEISHU_AM_TODO_TASKLIST_GUID=00000000-0000-4000-8000-000000000001
```

仓库中的 [config/template.yaml](config/template.yaml) 和 [config/example.yaml](config/example.yaml) 仍然有价值，但当前代码里没有发现自动读取这两份 YAML 的运行时路径。它们更适合用作结构模板、脱敏示例和未来配置模型的设计输入，而不是当前运行入口的直接配置源。

## Required vs Optional Settings

当前实现里，没有发现“缺少某个环境变量就直接在 import 或 CLI 启动阶段抛异常退出”的硬校验。实际行为是：runtime 先加载 `.env`，再由 `ResourceResolver` 和 capability reporter 把缺失项体现在诊断结果里。

对完整 live capability 来说，当前会被当作核心资源键检查的只有 4 项：

- `base_token`
- `customer_archive_folder`
- `meeting_notes_folder`
- `todo_tasklist_guid`

对应到环境变量时，规则是：

- `base_token` 可以由 `FEISHU_AM_BASE_TOKEN` 直接提供，也可以回退到 `FEISHU_AM_WORKBENCH_BASE_URL`
- `customer_archive_folder` 需要 `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
- `meeting_notes_folder` 需要 `FEISHU_AM_MEETING_NOTES_FOLDER`
- `todo_tasklist_guid` 需要 `FEISHU_AM_TODO_TASKLIST_GUID`

其余配置项目前都属于可选增强项：

- `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` 主要用于更精确地锁定客户主数据表，但可由 Base URL 回退解析
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID` 和 `FEISHU_AM_TODO_PRIORITY_FIELD_GUID` 是 Todo 自定义字段覆盖项，不设置时保持空值
- `FEISHU_AM_CUSTOMER_MASTER_TABLE`、`FEISHU_AM_CONTACT_LOG_TABLE`、`FEISHU_AM_ACTION_PLAN_TABLE` 是表目标名覆盖项，不设置时使用代码内置默认名

## Defaults

当前源码中能确认的默认值和回退规则如下：

| Variable | Default | Where it is set |
| --- | --- | --- |
| `FEISHU_AM_BASE_TOKEN` | 回退到 `FEISHU_AM_WORKBENCH_BASE_URL` 解析出的 Base token | `runtime/runtime_sources.py` |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID` | 回退到 `FEISHU_AM_WORKBENCH_BASE_URL` 的 `table` 查询参数 | `runtime/runtime_sources.py` |
| `FEISHU_AM_CUSTOMER_MASTER_TABLE` | 已解析的客户主数据表 id；若仍不可用则回退到 `客户主数据` | `runtime/live_adapter.py` |
| `FEISHU_AM_CONTACT_LOG_TABLE` | `客户联系记录` | `runtime/live_adapter.py` |
| `FEISHU_AM_ACTION_PLAN_TABLE` | `行动计划` | `runtime/live_adapter.py` |
| `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID` | 空值 | `runtime/runtime_sources.py` |
| `FEISHU_AM_TODO_PRIORITY_FIELD_GUID` | 空值 | `runtime/runtime_sources.py` |

除了变量本身的默认值，`.env` 加载器还有两个固定行为默认值：

- 默认文件名是 `.env`
- 默认 `override=false`，也就是 shell 已有值优先于 `.env`

## Per-environment overrides

当前仓库里能被直接发现的环境文件只有仓库根目录 `.env` 和示例文件 `.env.example`。没有检测到 `.env.development`、`.env.production`、`.env.test` 这类按环境自动切换的文件，也没有发现根据环境名自动选择不同配置文件的代码路径。

因此，当前项目的分环境策略实际上是：

- 用 `.env.example` 维护公开的键名清单和示例值
- 在本地根目录 `.env` 中放当前工作环境的私有值
- 如果 shell 里已经 export 了同名变量，shell 值覆盖 `.env`

这意味着开发、验证或未来的 CI 环境切换，当前都依赖外部注入同名 `FEISHU_AM_*` 变量，而不是依赖仓库内多套环境文件自动切换。
