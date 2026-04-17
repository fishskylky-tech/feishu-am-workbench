"""Stable scene-name registry and dispatch helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .scene_runtime import (
    SceneRequest,
    SceneResult,
    run_archive_refresh_scene,
    run_customer_recent_status_scene,
    run_post_meeting_scene,
    run_todo_capture_and_update_scene,
)

SceneHandler = Callable[[SceneRequest], SceneResult]


class UnknownSceneError(ValueError):
    """Raised when scene dispatch receives an unregistered scene name."""


@dataclass
class SceneRegistry:
    _handlers: dict[str, SceneHandler] = field(default_factory=dict)

    def register(self, scene_name: str, handler: SceneHandler) -> None:
        self._handlers[scene_name] = handler

    def available_scenes(self) -> list[str]:
        return sorted(self._handlers)

    def dispatch(self, request: SceneRequest) -> SceneResult:
        handler = self._handlers.get(request.scene_name)
        if handler is None:
            known = ", ".join(self.available_scenes()) or "none"
            raise UnknownSceneError(
                f"unknown scene '{request.scene_name}'. known scenes: {known}"
            )
        return handler(request)


def build_default_scene_registry() -> SceneRegistry:
    registry = SceneRegistry()
    registry.register("post-meeting-synthesis", run_post_meeting_scene)
    registry.register("customer-recent-status", run_customer_recent_status_scene)
    registry.register("archive-refresh", run_archive_refresh_scene)
    registry.register("todo-capture-and-update", run_todo_capture_and_update_scene)
    return registry


def dispatch_scene(request: SceneRequest, registry: SceneRegistry | None = None) -> SceneResult:
    active_registry = registry or build_default_scene_registry()
    return active_registry.dispatch(request)
