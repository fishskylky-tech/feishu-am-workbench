---
phase: 12-scene-runtime-contract-and-boundary-freeze
plan: 01
subsystem: scene-runtime-contract
tags: [scene-runtime, routing, contract, compatibility]
provides:
  - shared scene request/result contract
  - explicit scene registry dispatch seam
  - compatibility routing from meeting-write-loop to post-meeting-synthesis
requirements-completed: [SCENE-01, SCENE-02]
completed: 2026-04-17
---

# Phase 12: Scene Runtime Contract And Boundary Freeze Summary

**Plan 12-01 把 scene runtime 从架构概念变成了可执行 contract：runtime 现在有统一的 scene request/result 结构、显式 scene router，以及指向 `post-meeting-synthesis` 的兼容入口。**

## Accomplishments

- 新增 `runtime/scene_runtime.py`，定义 `SceneRequest`、`SceneResult` 和首个 `run_post_meeting_scene()` adapter。
- 新增 `runtime/scene_registry.py`，把稳定 scene 名称映射到显式 handler，并对未知 scene 做确定性失败。
- 将 `runtime/__main__.py` 重构为薄入口，新增 `python -m runtime scene ...` 命令，并把 `meeting-write-loop` 改为 `post-meeting-synthesis` 的 compatibility wrapper。
- 复用现有 gateway、context recovery、candidate generation 和 confirmed write 路径，没有引入第二套 write surface。
- 在 `tests/test_runtime_smoke.py` 中加入 scene result、scene dispatch 和 CLI compatibility 回归测试。

## Verification

- `source .venv/bin/activate && python -m unittest tests.test_runtime_smoke -q`

## Outcome

- SCENE-01 和 SCENE-02 已有可执行实现，而不再只是文档约定。
- 后续 scene 扩展可以复用统一 contract，而不是继续在 root CLI 堆积一串一次性 operator 逻辑。