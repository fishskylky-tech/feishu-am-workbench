# Testing

本文档说明 `feishu-am-workbench` 当前如何验证“这次改动真的可信”。

这里不追求重型 benchmark，而是追求对当前 live-first 工作流真正有约束力的验证。

## 1. 测试分层

当前仓库可以分成 3 层验证：

### 自动化单元/集成切片

- `tests/test_env_loader.py`
- `tests/test_runtime_smoke.py`
- `tests/test_meeting_output_bridge.py`
- `tests/test_eval_runner.py`
- `tests/test_validation_assets.py`

### 结构化 eval 资产

- `evals/evals.json`
- `evals/runner.py`
- `evals/meeting_output_bridge.py`

### 人工 live 验证

- 真实飞书工作区的 capability 检查
- meeting 场景输出审计字段复核
- fallback evidence 质量复核
- human UAT

## 2. 最常用测试命令

### 快速切片

```bash
python3 -m unittest tests.test_meeting_output_bridge -q
```

适合修改会议场景、上下文恢复、fallback 路由、审计字段时快速回归。

### Phase 3 / 当前核心切片

```bash
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q
```

适合在发 PR 前确认：

- 环境加载没坏
- runtime capability 逻辑没坏
- meeting recovery 没回退
- 文档/版本/验证资产仍然一致

### 更完整的回归

```bash
python3 -m unittest tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner tests.test_validation_assets
```

## 3. 人工验证重点

自动化通过不等于 live 场景一定可信。以下项仍然需要人工确认：

1. archive / meeting-note fallback 在真实 Drive 中的候选质量
2. 写回前 preflight / guard 在真实任务和表结构上的行为
3. 高风险字段是否仍然保持 recommendation-only

## 4. 发 PR 前建议清单

至少确认：

1. 相关 unittest 切片通过
2. 如果改了文档或版本，`tests.test_validation_assets` 通过
3. 需要时补一条真实会议样本验证
4. 文档与实际行为一致
5. 未把 `.planning/` 噪音带进 PR 评审面

## 5. 当前可信口径

截至当前状态，最稳定的验证结论是：

- Phase 3 自动化切片已通过
- Phase 3 code review clean
- security audit `threats_open: 0`
- human UAT 4/4 passed

这说明当前 meeting 场景的核心上下文恢复闭环可信，但不代表所有写回路径都已完全成熟。

## Test framework and setup

当前仓库提交到版本库中的自动化测试以 Python 标准库 `unittest` 为主，没有发现仓库内的 `pytest`、coverage 或 CI 测试配置文件。

运行前准备：

- 在仓库根目录执行测试
- 激活本地虚拟环境，当前仓库默认使用 `.venv`
- 如果要做 live 验证或跑依赖飞书资源的命令，先按 `.env.example` 准备本地 `.env`

已验证可直接工作的全量命令是：

```bash
source .venv/bin/activate
python -m unittest discover -s tests -q
```

该命令当前会执行 `tests/` 下的 115 个测试用例。

## Running tests

运行全量测试：

```bash
source .venv/bin/activate
python -m unittest discover -s tests -q
```

运行当前最常用的核心回归切片：

```bash
source .venv/bin/activate
python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q
```

只运行单个测试文件：

```bash
source .venv/bin/activate
python -m unittest tests.test_meeting_output_bridge -q
```

只运行单个测试方法：

```bash
source .venv/bin/activate
python -m unittest tests.test_eval_runner.EvalRunnerTests.test_cli_returns_json_and_exit_code -q
```

仓库里没有定义 watch mode；需要重复回归时，直接重复执行上面的切片命令即可。

## Writing new tests

当前测试命名约定是：

- 文件名放在 `tests/` 目录下，使用 `test_*.py`
- 测试类继承 `unittest.TestCase`
- 测试方法使用 `test_*` 命名

现有测试里最常见的写法有三类：

- 纯函数或配置加载测试直接在测试文件里构造输入，例如 `tests/test_env_loader.py`
- CLI 或桥接层测试使用 `subprocess.run`、`redirect_stdout`、`unittest.mock.patch` 做切片验证，例如 `tests/test_eval_runner.py` 和 `tests/test_meeting_output_bridge.py`
- 真实会议样本回归使用 `tests/fixtures/transcripts/` 下的固定转写文件，避免把样本直接写死在断言里

当前仓库没有独立的共享测试 helper 模块；常量、fixture 路径和 mock 组装主要放在各自的测试文件中，就近维护。

新增测试时，优先沿用现有模式：

- 如果验证环境变量或文件加载，优先使用 `tempfile.TemporaryDirectory()` 创建临时输入
- 如果验证命令行入口，优先通过 `subprocess.run` 断言退出码和标准输出
- 如果验证 runtime 或 scene 行为，优先用 `unittest.mock.patch` 隔离 live 依赖，再用固定 transcript fixture 做回归

## Coverage requirements

仓库当前没有配置数值化覆盖率门槛。

未发现以下任一覆盖率配置来源：

- `.github/workflows/` 下的 coverage job
- `pytest` / `pytest-cov` 仓库级配置
- `coverage.py`、`.coveragerc`、`c8`、`nyc` 等阈值文件

因此当前口径是：`No coverage threshold configured.`

现阶段更实际的约束来自关键切片是否通过，以及 `tests.test_validation_assets` 对版本、验证资产和里程碑文档的一致性检查。

## CI integration

仓库中未检测到 `.github/workflows/` 下的测试工作流文件，因此没有可引用的 CI job、触发条件或平台内测试命令。

当前测试执行方式以本地运行为主：

- 使用 `python -m unittest` 直接运行 `tests/` 目录
- 用 `evals/runner.py` 和 `evals/meeting_output_bridge.py` 做结构化案例复核
- 用 `VALIDATION.md` 约束 baseline、green 和 regression 的执行口径

如果后续补上 CI，建议优先把本节里的全量命令作为最小自动化入口，而不是重新定义另一套测试命令。
