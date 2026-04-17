"""Local runtime package for feishu-am-workbench."""

from .customer_resolver import CustomerResolver
from .diagnostics import build_live_diagnostic, render_live_diagnostic
from .gateway import FeishuWorkbenchGateway
from .lark_cli import LarkCliClient, LarkCliCommandError
from .live_adapter import (
    LarkCliBaseQueryBackend,
    LarkCliCustomerBackend,
    LarkCliResourceProbe,
    LarkCliSchemaBackend,
    LiveCapabilityReporter,
    LiveWorkbenchConfig,
)
from .models import WriteCandidate, WriteExecutionResult
from .resource_resolver import ResourceResolver
from .runtime_sources import RuntimeSourceLoader
from .schema_preflight import SchemaPreflightRunner
from .scene_registry import SceneRegistry, UnknownSceneError, dispatch_scene
from .scene_runtime import SceneRequest, SceneResult
from .semantic_registry import (
    TABLE_PROFILES,
    get_integrated_base_tables,
    get_required_base_tables,
)
from .todo_writer import TodoWriter
from .write_guard import WriteGuard

__all__ = [
    "CustomerResolver",
    "FeishuWorkbenchGateway",
    "LarkCliClient",
    "LarkCliCommandError",
    "LarkCliBaseQueryBackend",
    "LarkCliCustomerBackend",
    "LiveCapabilityReporter",
    "LarkCliResourceProbe",
    "LarkCliSchemaBackend",
    "LiveWorkbenchConfig",
    "ResourceResolver",
    "RuntimeSourceLoader",
    "SchemaPreflightRunner",
    "SceneRegistry",
    "SceneRequest",
    "SceneResult",
    "TABLE_PROFILES",
    "TodoWriter",
    "UnknownSceneError",
    "WriteCandidate",
    "WriteExecutionResult",
    "WriteGuard",
    "build_live_diagnostic",
    "dispatch_scene",
    "get_integrated_base_tables",
    "get_required_base_tables",
    "render_live_diagnostic",
]
