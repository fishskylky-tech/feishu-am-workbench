"""Minimal table profiles and semantic slots for the local personal workflow."""

from __future__ import annotations

from .models import TableProfile


TABLE_PROFILES: dict[str, TableProfile] = {
    "客户主数据": TableProfile(
        table_name="客户主数据",
        table_role="snapshot",
        entity_key="customer_id",
        dedupe_key=["customer_id"],
        default_read_slots=[
            "customer_id",
            "short_name",
            "archive_link",
            "strategy_summary",
            "last_contact_at",
            "next_action_summary",
        ],
        write_slots=[
            "archive_link",
            "strategy_summary",
            "last_contact_at",
            "next_action_summary",
            "strategy_direction",
            "renewal_risk",
        ],
        protected_slots=["strategy_direction", "renewal_risk"],
        strict_enum_slots=["strategy_direction", "renewal_risk"],
        capability_required=True,
    ),
    "行动计划": TableProfile(
        table_name="行动计划",
        table_role="detail",
        entity_key="customer_id",
        dedupe_key=["customer_id", "subject", "due_at"],
        default_read_slots=[
            "customer_id",
            "subject",
            "action_type",
            "status",
            "due_at",
            "completed_at",
            "output",
        ],
        write_slots=[
            "customer_id",
            "subject",
            "action_type",
            "status",
            "due_at",
            "completed_at",
            "output",
        ],
        strict_enum_slots=["action_type", "status"],
        capability_required=True,
    ),
    "客户联系记录": TableProfile(
        table_name="客户联系记录",
        table_role="detail",
        entity_key="customer_id",
        dedupe_key=["customer_id", "title", "contact_date"],
        default_read_slots=[
            "customer_id",
            "title",
            "contact_date",
            "next_contact_summary",
            "key_progress",
            "todo_summary",
            "risk_summary",
            "meeting_note_doc",
        ],
        write_slots=[
            "customer_id",
            "title",
            "contact_date",
            "next_contact_summary",
            "key_progress",
            "todo_summary",
            "risk_summary",
            "meeting_note_doc",
        ],
        capability_required=True,
    ),
    "客户关键人地图": TableProfile(
        table_name="客户关键人地图",
        table_role="detail",
        entity_key="customer_id",
        dedupe_key=["customer_id"],
        default_read_slots=[
            "客户ID",
            "姓名",
            "职位",
            "角色",
            "关系强度",
            "最近联系时间",
            "关键诉求",
            "动态备注",
        ],
        capability_required=False,
    ),
    "合同清单": TableProfile(
        table_name="合同清单",
        table_role="detail",
        entity_key="customer_id",
        dedupe_key=["customer_id"],
        default_read_slots=[
            "客户ID",
            "合同编码",
            "合同类型",
            "合同状态",
            "合同到期日期",
            "回款状态",
            "验收状态",
            "风险提示",
        ],
        capability_required=False,
    ),
    "竞品基础信息表": TableProfile(
        table_name="竞品基础信息表",
        table_role="dimension",
        entity_key="competitor_id",
        dedupe_key=["competitor_id"],
        capability_required=False,
    ),
    "竞品交锋记录": TableProfile(
        table_name="竞品交锋记录",
        table_role="bridge",
        entity_key="customer_id",
        dedupe_key=["customer_id", "competitor_id"],
        capability_required=False,
    ),
}


SEMANTIC_FIELD_REGISTRY: dict[str, dict[str, dict[str, object]]] = {
    "客户主数据": {
        "customer_id": {
            "canonical_name": "客户 ID",
            "aliases": ["客户ID"],
            "allowed_live_types": ["text"],
            "write_policy": "required_lookup",
        },
        "short_name": {
            "canonical_name": "简称",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "read_only_for_match",
        },
        "archive_link": {
            "canonical_name": "客户档案",
            "aliases": [],
            "allowed_live_types": ["text", "url"],
            "write_policy": "safe_update",
        },
        "strategy_summary": {
            "canonical_name": "策略摘要",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "last_contact_at": {
            "canonical_name": "上次接触日期",
            "aliases": [],
            "allowed_live_types": ["datetime", "text"],
            "write_policy": "safe_update",
        },
        "next_action_summary": {
            "canonical_name": "下次行动计划",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "strategy_direction": {
            "canonical_name": "26年策略方向",
            "aliases": ["策略方向"],
            "allowed_live_types": ["single_select"],
            "write_policy": "guarded_update",
            "strict_enum": True,
        },
        "renewal_risk": {
            "canonical_name": "续费风险",
            "aliases": ["续约风险"],
            "allowed_live_types": ["single_select"],
            "write_policy": "guarded_update",
            "strict_enum": True,
        },
    },
    "行动计划": {
        "customer_id": {
            "canonical_name": "客户ID",
            "aliases": ["客户 ID"],
            "allowed_live_types": ["text"],
            "write_policy": "required_lookup",
        },
        "subject": {
            "canonical_name": "具体行动",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "required_create",
        },
        "action_type": {
            "canonical_name": "行动类型_单选",
            "aliases": [],
            "allowed_live_types": ["single_select"],
            "write_policy": "safe_update",
            "strict_enum": True,
        },
        "status": {
            "canonical_name": "完成状态_单选",
            "aliases": [],
            "allowed_live_types": ["single_select"],
            "write_policy": "safe_update",
            "strict_enum": True,
        },
        "due_at": {
            "canonical_name": "计划完成时间",
            "aliases": [],
            "allowed_live_types": ["datetime", "text"],
            "write_policy": "safe_update",
        },
        "completed_at": {
            "canonical_name": "实际完成时间",
            "aliases": [],
            "allowed_live_types": ["datetime", "text"],
            "write_policy": "safe_update",
        },
        "output": {
            "canonical_name": "产出结果",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
    },
    "客户联系记录": {
        "customer_id": {
            "canonical_name": "客户ID",
            "aliases": ["客户 ID"],
            "allowed_live_types": ["text"],
            "write_policy": "required_lookup",
        },
        "title": {
            "canonical_name": "记录标题",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "required_create",
        },
        "contact_date": {
            "canonical_name": "联系日期",
            "aliases": [],
            "allowed_live_types": ["datetime", "text"],
            "write_policy": "safe_update",
        },
        "next_contact_summary": {
            "canonical_name": "下次联系计划",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "key_progress": {
            "canonical_name": "关键进展",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "todo_summary": {
            "canonical_name": "待办事项",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "risk_summary": {
            "canonical_name": "客户顾虑/风险",
            "aliases": [],
            "allowed_live_types": ["text"],
            "write_policy": "safe_update",
        },
        "meeting_note_doc": {
            "canonical_name": "会议纪要文档",
            "aliases": [],
            "allowed_live_types": ["text", "url"],
            "write_policy": "safe_update",
        },
    },
}


def get_table_profile(table_name: str) -> TableProfile | None:
    return TABLE_PROFILES.get(table_name)


def get_required_base_tables() -> list[str]:
    return [
        profile.table_name
        for profile in TABLE_PROFILES.values()
        if profile.capability_required
    ]


def get_integrated_base_tables() -> list[str]:
    return list(TABLE_PROFILES.keys())
