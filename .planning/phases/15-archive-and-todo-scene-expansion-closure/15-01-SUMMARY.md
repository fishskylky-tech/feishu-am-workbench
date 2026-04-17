---
phase: 15-archive-and-todo-scene-expansion-closure
plan: 01
subsystem: archive-and-todo-scenes
tags: [scene-runtime, archive-refresh, todo-follow-on]
provides:
  - archive-refresh scene behavior on the shared contract
  - todo-capture-and-update scene behavior on the shared contract
requirements-completed: [SCENE-06]
completed: 2026-04-17
---

# Phase 15 Plan 01 Summary

Phase 15 把第一波剩余两个 scene 名称都收进了共享 contract：`archive-refresh` 提供 recommendation-first refresh 行为，`todo-capture-and-update` 提供 follow-on candidate 整理并在确认后继续走现有 Todo writer。

## What Changed

- `runtime/scene_registry.py` 注册了 `archive-refresh` 与 `todo-capture-and-update`
- `runtime/scene_runtime.py` 新增两个 scene adapter，但没有引入第二套写路径
- archive refresh 保持 recommendation-first，不虚构新的文档写回能力
- Todo follow-on 仍在确认后走 `run_confirmed_todo_write()` + `TodoWriter`

## Verification

- `source .venv/bin/activate && python -m unittest tests.test_runtime_smoke -q`