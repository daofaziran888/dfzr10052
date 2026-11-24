"""字段映射·规则管理，产出映射规则数据集。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class FieldMappingService(BaseModuleService):
    MODULE = "field_mapping"
    ENTITY = "映射规则"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["规则编号", "站点编号", "源字段路径", "目标字段", "转换表达式", "规则版本", "生效时间"]
    REQUIRED_FIELDS = ["规则编号", "站点编号", "源字段路径"]
    STATUS_ORDER = ["草拟中", "待验证", "已生效", "已废弃"]
    ACTION_RULES = {"提交验证": "待验证", "生效规则": "已生效", "废弃规则": "已废弃"}
    NEGATIVE_ACTIONS = ["废弃规则"]

    def active_rules_for_site(self, site_no: str) -> list[dict[str, Any]]:
        """获取某站点已生效映射规则。"""
        rows = store.rows(self.MODULE)
        return [
            r for r in rows
            if r.get("站点编号") == site_no and r.get("status") == "已生效"
        ]

    def rules_by_version(self, version: str) -> list[dict[str, Any]]:
        """按规则版本过滤映射规则。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("规则版本") == version]

    def conflicts_between_rules(self, site_no: str) -> list[dict[str, Any]]:
        """检测同站点源字段路径冲突的映射规则。"""
        rows = store.rows(self.MODULE)
        site_rules = [r for r in rows if r.get("站点编号") == site_no]
        seen: dict[str, list[dict[str, Any]]] = {}
        for r in site_rules:
            src = r.get("源字段路径", "")
            if src not in seen:
                seen[src] = []
            seen[src].append(r)
        return [r for paths in seen.values() if len(paths) > 1 for r in paths]

    def discard_old_versions(self, site_no: str, target_version: str) -> int:
        """将指定站点非目标版本的旧映射规则设为已废弃。"""
        rows = store.rows(self.MODULE)
        count = 0
        for r in rows:
            if (
                r.get("站点编号") == site_no
                and r.get("规则版本") != target_version
                and r.get("status") != "已废弃"
            ):
                r["status"] = "已废弃"
                r["abnormal"] = True
                count += 1
        return count