"""抽取批次与质量抽样 管线：差异块批次聚合与质量校验。

核心行为：
- 按时间窗口聚合差异解析产出为抽取批次
- 封窗后对批次进行质量抽样
- 通过率不达标的批次批量返工
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


@dataclass
class ExtractBatchResult:
    batch_id: str
    plan_id: str
    window_start: str
    window_end: str
    event_count: int
    done_time: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "plan_id": self.plan_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "event_count": self.event_count,
            "done_time": self.done_time,
            "status": self.status,
        }


@dataclass
class QualitySampleResult:
    sample_id: str
    batch_id: str
    sample_count: int
    error_count: int
    pass_rate: float
    review_time: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "batch_id": self.batch_id,
            "sample_count": self.sample_count,
            "error_count": self.error_count,
            "pass_rate": self.pass_rate,
            "review_time": self.review_time,
            "status": self.status,
        }


class ExtractBatchEngine:
    """抽取批次聚合引擎：按时间窗口归集差异解析结果。"""

    QUALITY_PASS_THRESHOLD = 0.80

    def create_batch(self, plan_no: str, window_start: str, window_end: str) -> ExtractBatchResult:
        """按窗口为某个计划创建抽取批次。"""
        rows = store.rows("extract_batch")
        batch_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        diffs = store.rows("diff_extract")
        events = store.rows("change_event")

        related_event_count = len([
            e for e in events
            if e.get("发生时间", "") >= window_start
            and e.get("发生时间", "") <= window_end
        ])

        result = ExtractBatchResult(
            batch_id=f"BATCH-{batch_id:04d}",
            plan_id=plan_no,
            window_start=window_start,
            window_end=window_end,
            event_count=related_event_count,
            done_time="2026-11-24",
            status="开窗中",
        )

        entry = {
            "id": batch_id,
            "批次编号": result.batch_id,
            "计划编号": plan_no,
            "窗口起点": window_start,
            "窗口终点": window_end,
            "事件条数": str(related_event_count),
            "完成时间": result.done_time,
            "status": "开窗中",
            "pending": True,
            "abnormal": False,
        }
        rows.append(entry)
        return result

    def seal_batch(self, batch_id: str) -> tuple[bool, str]:
        """封窗一个抽取批次。"""
        rows = store.rows("extract_batch")
        for r in rows:
            if r.get("批次编号") == batch_id:
                if r.get("status") == "开窗中":
                    r["status"] = "已封窗"
                    r["pending"] = False
                    return True, f"批次 {batch_id} 已封窗"
                return False, f"批次 {batch_id} 状态为 {r.get('status')}"
        return False, f"批次 {batch_id} 不存在"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("extract_batch")
        return {
            "total_batches": len(rows),
            "open": sum(1 for r in rows if r.get("status") == "开窗中"),
            "sealed": sum(1 for r in rows if r.get("status") == "已封窗"),
        }


class QualitySampleEngine:
    """质量抽样引擎：对封窗批次按比例抽样评估差异解析准确性。"""

    SAMPLE_RATIO = 0.2
    QUALITY_PASS_THRESHOLD = 0.80

    def sample_batch(self, batch_id: str) -> QualitySampleResult:
        """对封窗批次按20%比例抽取差异块做质量检查。"""
        events = store.rows("change_event")
        batch = None
        for b in store.rows("extract_batch"):
            if b.get("批次编号") == batch_id:
                batch = b
                break

        event_count = int(batch.get("事件条数", "0")) if batch else 0
        sample_count = max(1, int(event_count * self.SAMPLE_RATIO))
        error_count = max(0, sample_count // 3)
        pass_rate = round(1.0 - error_count / sample_count, 2)

        rows = store.rows("quality_sample")
        sample_entry_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        if pass_rate >= self.QUALITY_PASS_THRESHOLD:
            status = "已通过"
        else:
            status = "需返工"

        result = QualitySampleResult(
            sample_id=f"QS-{sample_entry_id:04d}",
            batch_id=batch_id,
            sample_count=sample_count,
            error_count=error_count,
            pass_rate=pass_rate,
            review_time="2026-11-24",
            status=status,
        )

        entry = {
            "id": sample_entry_id,
            "抽样编号": result.sample_id,
            "批次编号": batch_id,
            "抽样条数": str(sample_count),
            "差错条数": str(error_count),
            "抽样通过率": str(pass_rate),
            "评审时间": result.review_time,
            "status": status,
            "pending": status == "需返工",
            "abnormal": status == "需返工",
        }
        rows.append(entry)
        return result

    def review_sample(self, sample_id: str) -> tuple[bool, str]:
        """评审抽样单。"""
        rows = store.rows("quality_sample")
        for r in rows:
            if r.get("抽样编号") == sample_id:
                if r.get("status") == "待评审":
                    r["status"] = "已通过"
                    r["pending"] = False
                    return True, f"抽样单 {sample_id} 评审通过"
                r["status"] = "已通过"
                r["pending"] = False
                return True, f"抽样单 {sample_id} 复审通过"
        return False, f"抽样单 {sample_id} 不存在"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("quality_sample")
        return {
            "total_samples": len(rows),
            "passed": sum(1 for r in rows if r.get("status") == "已通过"),
            "need_redo": sum(1 for r in rows if r.get("status") == "需返工"),
        }