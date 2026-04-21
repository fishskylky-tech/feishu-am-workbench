<!-- generated-by: gsd-doc-writer -->

# 开发指南

本文档面向希望扩展或修改飞书 AM 工作台项目的开发者。

## 项目结构

```
feishu-am-workbench/
├── runtime/              # Python 运行时核心模块
│   ├── __main__.py       # CLI 入口
│   ├── scene_runtime.py  # 主场景执行器（73KB+）
│   ├── scene_registry.py # 场景注册与分发
│   ├── live_adapter.py   # 飞书 API 集成（41KB+）
│   ├── expert_analysis_helper.py  # 专家分析辅助
│   ├── models.py        # 数据模型定义
│   ├── confirmation_checklist.py # 确认清单
│   ├── expert_card_loader.py     # 专家卡片加载器
│   ├── gateway.py       # 飞书工作台网关
│   ├── schema_preflight.py       # Schema 预检
│   ├── todo_writer.py   # Todo 写入
│   ├── lark_cli.py      # Lark CLI 客户端
│   ├── runtime_sources.py       # 运行时源加载
│   ├── customer_resolver.py      # 客户解析
│   ├── diagnostics.py   # 诊断工具
│   └── ...
├── scenes/              # 场景配置
│   ├── customer-recent-status/
│   │   └── expert-cards.yaml
│   └── post-meeting-synthesis/
│       └── expert-cards.yaml
├── tests/               # 测试套件
├── references/          # 参考文档（26份）
├── config/              # 配置模板
└── SKILL.md             # 技能定义
```

## 开发环境搭建

### 前提条件

- Python >= 3.11
- 虚拟环境（推荐）

### 步骤

```bash
# 1. 克隆仓库
git clone <repository-url>
cd feishu-am-workbench

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 4. 安装依赖
pip install -e .

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际值
```

### 验证安装

```bash
python -m runtime diagnose
```

## 核心模块说明

### scene_runtime.py（主场景执行器）

场景执行的核心逻辑，包含所有场景的处理函数：

- `run_post_meeting_scene()` - 会后总结场景
- `run_customer_recent_status_scene()` - 客户现状查询
- `run_meeting_prep_scene()` - 会前准备
- `run_proposal_scene()` - 提案/报告生成
- `run_archive_refresh_scene()` - 档案刷新
- `run_todo_capture_and_update_scene()` - Todo 捕获更新
- `run_cohort_scan_scene()` - 客户群分析

关键数据结构：
- `SceneRequest` - 场景请求
- `SceneResult` - 场景结果
- `EvidenceContainer` - 证据容器（Phase 16 引入）

### scene_registry.py（场景注册）

场景的注册与分发中心。添加新场景时需要在此注册。

```python
def build_default_scene_registry() -> SceneRegistry:
    registry = SceneRegistry()
    registry.register("post-meeting-synthesis", run_post_meeting_scene)
    registry.register("customer-recent-status", run_customer_recent_status_scene)
    # ... 注册更多场景
    return registry
```

### live_adapter.py（飞书 API 集成）

负责与飞书 Base 和 Todo 的所有交互：
- 客户主数据查询
- 会议纪要读写
- 合同/行动计划/联系记录/竞品表操作
- Todo 创建与更新

### models.py（数据模型）

定义所有核心数据结构和类型：
- `CustomerMatch` - 客户匹配结果
- `CustomerResolution` - 客户解析结果
- `ContextRecoveryResult` - 上下文恢复结果
- `WriteCandidate` - 写入候选
- `TableProfile` - 表配置

### expert_analysis_helper.py（专家分析辅助）

Phase 16 引入的专家分析基础设施：
- `EvidenceContainer` - 证据容器
- `EvidenceSource` - 证据源
- `ExpertAnalysisHelper` - 分析辅助类

### confirmation_checklist.py（确认清单）

用户确认流程相关：
- `build_meeting_prep_checklist()` - 会前准备确认清单
- `build_proposal_checklist()` - 提案确认清单
- `build_archive_refresh_checklist()` - 档案刷新确认清单

### expert_card_loader.py（专家卡片加载器）

加载场景目录下的 `expert-cards.yaml` 配置。

### schema_preflight.py（Schema 预检）

在写入飞书前验证表结构和字段类型是否匹配。

### todo_writer.py（Todo 写入）

Todo 项目的创建与更新逻辑。

## 添加新场景

### 步骤 1：创建场景配置

在 `scenes/{scene-name}/` 目录下创建 `expert-cards.yaml`：

```yaml
input_review:
  enabled: true
  expert_name: "材料审核专家"
  review_type: "materials_audit"
  check_signals:
    - "遗漏的关联信息"
    - "前后不一致的事实"
  output_field: "input_audit_notes"

output_review:
  enabled: true
  expert_name: "经营顾问"
  review_type: "recommendation_audit"
  check_signals:
    - "专业性"
    - "业务逻辑"
    - "可执行性"
  output_field: "output_audit_notes"
  block_on_flags:
    - "业务逻辑"
    - "超出范围"
```

### 步骤 2：注册场景

在 `runtime/scene_registry.py` 中添加注册：

```python
from .scene_runtime import run_new_scene

def build_default_scene_registry() -> SceneRegistry:
    registry = SceneRegistry()
    # ... 现有注册
    registry.register("new-scene-name", run_new_scene)
    return registry
```

### 步骤 3：实现场景逻辑

在 `runtime/scene_runtime.py` 中实现场景函数：

```python
def run_new_scene(request: SceneRequest) -> SceneResult:
    # 1. 解析请求
    # 2. 获取证据容器
    # 3.执行业务逻辑
    # 4. 构建确认清单
    # 5. 返回 SceneResult
```

## 修改运行时模块

### 修改数据模型（models.py）

数据模型使用 `@dataclass` 装饰器。修改时注意：
- 保持向后兼容
- 更新所有引用处
- 添加测试覆盖

### 修改 API 交互（live_adapter.py）

飞书 API 交互的修改要点：
- 始终使用 `schema_preflight.py` 验证写入
- 处理 API 限流和错误
- 记录诊断信息

### 修改专家分析逻辑（expert_analysis_helper.py）

Phase 16 引入的专家分析基础设施：
- `EvidenceContainer.sources` 跟踪所有证据源
- `critical_source_missing` 触发硬停止
- `write_ceiling` 控制写入上限

## 代码规范

### Python 规范

- **类型注解**：所有函数签名必须包含类型注解
- **PEP 8**：遵循 PEP 8 规范
- **不可变性**：优先使用不可变数据结构

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomerMatch:
    customer_id: str
    short_name: str
    confidence: float = 1.0
```

### 文件组织

- **模块大小**：单个文件不超过 800 行
- **高内聚**：相关功能放在一起
- **按功能组织**：而非按类型组织

### 错误处理

- 显式处理所有错误
- 提供有意义的错误消息
- 记录详细上下文（服务端）

## 运行测试

### 运行全部测试

```bash
pytest tests/ -v
```

### 运行特定测试文件

```bash
pytest tests/test_scene_runtime.py -v
```

### 运行特定测试类

```bash
pytest tests/test_scene_runtime.py::TestExpertAnalysisHelperAssemble -v
```

### 运行带覆盖率

```bash
pytest tests/ --cov=runtime --cov-report=term-missing
```

### 测试目录结构

```
tests/
├── test_scene_runtime.py      # 场景运行时测试
├── test_confirmation_checklist.py  # 确认清单测试
├── test_expert_card_loader.py # 专家卡片加载器测试
├── test_archive_refresh_scene.py   # 档案刷新场景测试
├── test_meeting_prep_scene.py  # 会前准备场景测试
├── test_proposal_scene.py      # 提案场景测试
├── test_cohort_scan.py         # 客户群分析测试
├── test_live_bitable_integration.py  # 飞书 Bitable 集成测试
├── test_runtime_smoke.py       # 冒烟测试
└── ...
```

## 调试技巧

### 本地诊断

```bash
python -m runtime diagnose
```

输出运行时配置状态、所有资源是否正确配置。

### 场景调试

```bash
python -m runtime scene post-meeting-synthesis \
    --customer-query "测试客户" \
    --eval-name "测试" \
    --transcript-file /path/to/transcript.txt \
    --json
```

### 查看详细日志

设置环境变量启用详细日志：

```bash
export FEISHU_DEBUG=1
python -m runtime scene ...
```

### 常见问题

**Q: 场景提示 "unknown scene"**
- 检查 `scene_registry.py` 是否已注册该场景
- 确认函数名拼写正确

**Q: 飞书 API 调用失败**
- 检查 `.env` 中的 `FEISHU_AM_BASE_TOKEN` 是否正确
- 确认飞书应用权限是否包含所需 API
- 运行 `python -m runtime diagnose` 检查配置

**Q: 写入被阻止**
- 检查 `write_guard.py` 的阻止原因
- 确认 `schema_preflight.py` 验证通过
- 查看错误消息中的具体字段

**Q: 专家分析触发硬停止**
- 确认关键数据源（customer_master, contact_records）可用
- 检查 `evidence_container.missing_critical_sources`

## 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构
- [CONFIGURATION.md](./CONFIGURATION.md) - 配置指南
- [GETTING-STARTED.md](../GETTING-STARTED.md) - 快速上手
- [references/](./references/) - 26 份参考文档
