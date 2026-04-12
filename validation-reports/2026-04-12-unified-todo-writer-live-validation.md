# Unified Todo Writer Live Validation

日期：2026-04-12

## 目标

验证 unified Todo writer 在真实 Feishu 环境下，是否已能稳定产出这 3 类可审计结果：

- `blocked`
- `duplicate`
- `create`

## 执行环境

- runtime diagnostic: `base_access=available`、`docs_access=available`、`task_access=available`
- tasklist: `神策`
- writer: `runtime/todo_writer.py`

## 样本结果

### 1. blocked

样本：

- candidate 不带 owner
- customer: `联合利华（UFS）`

结果：

- `attempted=false`
- `allowed=false`
- `preflight_status=blocked`
- `guard_status=blocked`
- `dedupe_decision=no_write`
- `executed_operation=blocked`
- `blocked_reasons=["owner_unresolved"]`

结论：

- 符合预期
- 没有真实写入

### 2. duplicate

样本：

- 基于真实现有任务 `ea0d6e95-4ae0-4dff-92e0-b6e43bc8b414`
- 现有任务标题：`联合利华-AI埋点产品介绍给触脉（王奇）`
- 候选标题：`跟进联合利华 AI 埋点产品介绍给触脉确认`

第一轮结果：

- 错误创建了新任务
- 已立即清理

根因：

- dedupe tokenizer 对中文连续文本、连字符和括号拆分不足

修正后第二轮结果：

- `attempted=false`
- `allowed=false`
- `preflight_status=safe`
- `guard_status=allowed`
- `dedupe_decision=update_existing`
- `executed_operation=blocked`
- `blocked_reasons=["semantic_duplicate_detected"]`
- `remote_object_id="ea0d6e95-4ae0-4dff-92e0-b6e43bc8b414"`

结论：

- 修正后符合预期
- 没有重复写入

### 2.1 duplicate -> update auto patch

样本：

- 先创建 1 条带 `VALIDATION` 标记的 seed task
- 再提交一个近重复 candidate
- 由 unified Todo writer 自动命中 duplicate 并走 `update()` 路径

结果：

- `attempted=true`
- `allowed=true`
- `dedupe_decision=update_existing`
- `executed_operation=update`
- `remote_object_id` 等于 seed task guid

实际确认：

- summary 已更新为新标题
- description 已更新为新说明
- due 已更新为新时间

清理：

- seed task 已在验证后删除

结论：

- duplicate -> update 的自动 patch 路径已在真实 Feishu 环境验证通过

### 3. create

样本：

- 标题：`VALIDATION｜unified Todo writer create sample｜2026-04-12B`
- owner: `ou_8855be9f7b67cf309ff7e2fb800dcbb5`
- customer: `联合利华（UFS）`
- priority: `中`

结果：

- `attempted=true`
- `allowed=true`
- `preflight_status=safe`
- `guard_status=allowed`
- `dedupe_decision=create_new`
- `executed_operation=create`
- `remote_object_id="eadb178b-6cce-487e-b8d9-16f75c67f277"`

清理：

- 已在验证后调用真实 delete 清理该任务

结论：

- 符合预期

## 总结

当前 unified Todo writer 已在真实 Feishu 环境下跑通：

- blocked
- duplicate
- create
- duplicate -> update

当前仍需后续继续补强的点：

- dedupe 仍是第一版规则，当前只证明最小闭环成立
- duplicate -> update 已打通自动 patch
- create_subtask 当前为默认 recommendation-only，需显式确认（`confirm_create_subtask=true`）才执行真实写入
