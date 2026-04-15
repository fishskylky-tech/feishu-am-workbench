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