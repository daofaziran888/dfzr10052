"""差异解析与事件发布 管线：映射字段差异→生成差异块→事件去重→订阅推送。

核心行为：
- 映射后差异生成差异块条目（差异类型、位置、置信度）
- 差异块转换为变更事件并去重
- 去重后事件匹配订阅路由推送
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.store import store


@dataclass
class DiffBlock:
    diff_id: str
    detect_id: str
    diff_type: str
    position: str
    field_count: int
    confidence: float
    extract_time: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "diff_id": self.diff_id,
            "detect_id": self.detect_id,
            "diff_type": self.diff_type,
            "position": self.position,
            "field_count": self.field_count,
            "confidence": self.confidence,
            "extract_time": self.extract_time,
        }


@dataclass
class ChangeEvent:
    event_id: str
    diff_id: str
    event_level: str
    summary: str
    occur_time: str
    push_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "diff_id": self.diff_id,
            "event_level": self.event_level,
            "summary": self.summary,
            "occur_time": self.occur_time,
            "push_status": self.push_status,
        }


class DiffExtractEngine:
    """差异解析引擎：从变更检测中解析字段级差异块。"""

    def extract_diff_blocks(
        self, detect_id: str, mapped_fields: list[dict[str, str]],
        diff_type: str = "字段修改",
    ) -> DiffBlock:
        """从映射字段生成差异块条目。"""
        rows = store.rows("diff_extract")
        diff_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        field_count = len(mapped_fields)
        confidence = round(0.5 + field_count * 0.1, 2) if field_count > 0 else 0.5

        block = DiffBlock(
            diff_id=f"DIFF-{diff_id:04d}",
            detect_id=detect_id,
            diff_type=diff_type,
            position=f"path/{field_count}",
            field_count=field_count,
            confidence=confidence,
            extract_time="2026-11-24",
        )

        entry = {
            "id": diff_id,
            "差异编号": block.diff_id,
            "检测编号": detect_id,
            "差异类型": diff_type,
            "差异位置": block.position,
            "抽取字段数": str(field_count),
            "置信度": str(confidence),
            "抽取时间": block.extract_time,
            "status": "待复核" if confidence < 0.7 else "已确认",
            "pending": confidence < 0.7,
            "abnormal": confidence < 0.7,
        }
        rows.append(entry)
        return block

    def confirm_diff_block(self, diff_id: str) -> tuple[bool, str]:
        """确认差异块。"""
        rows = store.rows("diff_extract")
        for r in rows:
            if r.get("差异编号") == diff_id:
                r["status"] = "已确认"
                r["pending"] = False
                return True, f"差异块 {diff_id} 已确认"
        return False, f"差异块 {diff_id} 不存在"


class EventPublishEngine:
    """变更事件发布引擎：差异块→事件→去重→推送。"""

    EVENT_LEVELS = {"字段修改": "一般", "新增字段": "重要", "删除字段": "紧急"}

    def create_event_from_diff(self, diff_block: DiffBlock) -> ChangeEvent:
        """将确认差异块转换为变更事件。"""
        rows = store.rows("change_event")
        event_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        level = self.EVENT_LEVELS.get(diff_block.diff_type, "一般")
        summary = f"源站变更-{diff_block.diff_type}-{diff_block.field_count}个字段"

        event = ChangeEvent(
            event_id=f"EVENT-{event_id:04d}",
            diff_id=diff_block.diff_id,
            event_level=level,
            summary=summary,
            occur_time=diff_block.extract_time,
            push_status="待推送",
        )

        entry = {
            "id": event_id,
            "事件编号": event.event_id,
            "差异编号": diff_block.diff_id,
            "事件级别": level,
            "事件摘要": summary,
            "发生时间": event.occur_time,
            "推送状态": "待推送",
            "status": "待推送",
            "pending": True,
            "abnormal": False,
        }
        rows.append(entry)
        return event

    def deduplicate_event(self, event_id: str) -> tuple[bool, str]:
        """检查事件是否已存在重复指纹。"""
        events = store.rows("change_event")
        target = None
        for e in events:
            if e.get("事件编号") == event_id:
                target = e
                break
        if target is None:
            return False, f"事件 {event_id} 不存在"

        event_dedup_rows = store.rows("event_dedup")
        dup_id = max((int(r.get("id", 0)) for r in event_dedup_rows), default=0) + 1

        existing = [
            d for d in event_dedup_rows
            if d.get("事件编号") == event_id and d.get("去重结论") == "已去重"
        ]
        if existing:
            return False, f"事件 {event_id} 已被去重"

        dup_entry = {
            "id": dup_id,
            "去重编号": f"DEDP-{dup_id:04d}",
            "事件编号": event_id,
            "重复指纹": f"fp_{event_id}_20261124",
            "命中批次": "BATCH-001",
            "去重结论": "已保留",
            "去重时间": "2026-11-24",
            "status": "已保留",
            "pending": False,
            "abnormal": False,
        }
        event_dedup_rows.append(dup_entry)
        return True, f"事件 {event_id} 去重完成，已保留"

    def push_event_to_subscriber(self, event_id: str) -> tuple[bool, str]:
        """推送事件到匹配的订阅方。"""
        events = store.rows("change_event")
        target = None
        for e in events:
            if e.get("事件编号") == event_id:
                target = e
                break
        if target is None:
            return False, f"事件 {event_id} 不存在"

        level = target.get("事件级别", "一般")
        subscribers = [
            s for s in store.rows("subscribe_route")
            if s.get("status") == "已激活"
            and (s.get("事件级别过滤") == "全部" or s.get("事件级别过滤") == level)
        ]
        if not subscribers:
            target["推送状态"] = "待推送"
            target["status"] = "待推送"
            return False, f"事件 {event_id} 无匹配订阅方"

        push_rows = store.rows("push_records")
        push_id = max((int(r.get("id", 0)) for r in push_rows), default=0) + 1

        for sub in subscribers:
            push_entry = {
                "id": push_id,
                "推送编号": f"PUSH-{push_id:04d}",
                "事件编号": event_id,
                "订阅编号": sub.get("订阅编号", ""),
                "推送时间": "2026-11-24",
                "推送结果": "已成功",
                "重试次数": "0",
                "status": "已成功",
                "pending": False,
                "abnormal": False,
            }
            push_rows.append(push_entry)
            push_id += 1

        target["推送状态"] = "已推送"
        target["status"] = "已推送"
        target["pending"] = False
        return True, f"事件 {event_id} 已推送到 {len(subscribers)} 个订阅方"

    def snapshot(self) -> dict[str, Any]:
        events = store.rows("change_event")
        return {
            "total_events": len(events),
            "pending_push": sum(1 for e in events if e.get("推送状态") == "待推送"),
            "pushed": sum(1 for e in events if e.get("推送状态") == "已推送"),
        }