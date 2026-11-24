"""噪声过滤与字段映射 管线：检测结果→噪声过滤→字段映射→差异解析。

核心行为：
- 确认变更的检测结果进入噪声过滤池
- 时间戳抖动、广告位轮换等噪声被滤除
- 通过噪声过滤的变更按字段映射规则解析差异字段
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.store import store


@dataclass
class NoiseFilterResult:
    filter_id: str
    detect_id: str
    filter_rule: str
    filtered_count: int
    retained_count: int
    filter_time: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "filter_id": self.filter_id,
            "detect_id": self.detect_id,
            "filter_rule": self.filter_rule,
            "filtered_count": self.filtered_count,
            "retained_count": self.retained_count,
            "filter_time": self.filter_time,
        }


class NoiseFilterEngine:
    """噪声过滤引擎：识别并滤除时间戳抖动、广告轮换等非内容变更。"""

    NOISE_PATTERNS = ["timestamp_noise", "ad_rotation", "counter_update", "css_style"]

    def filter_detection_changes(
        self, detect_id: str, raw_diff_count: int,
    ) -> NoiseFilterResult:
        """对一次检测结果的差异区块进行噪声过滤。"""
        rows = store.rows("noise_filter")
        filter_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1

        filtered = 0
        for pattern in self.NOISE_PATTERNS:
            if raw_diff_count > 0 and raw_diff_count < 3 and pattern == "timestamp_noise":
                filtered += raw_diff_count
            elif pattern == "ad_rotation" and raw_diff_count > 5:
                filtered += 1
            elif pattern == "css_style" and raw_diff_count > 3:
                filtered += 1

        retained = raw_diff_count - filtered
        if filtered == raw_diff_count:
            rule = "全过滤-纯噪声"
        elif filtered > 0:
            rule = "部分过滤-含有效差异"
        else:
            rule = "无噪声-全保留"

        result = NoiseFilterResult(
            filter_id=f"FLTR-{filter_id:04d}",
            detect_id=detect_id,
            filter_rule=rule,
            filtered_count=filtered,
            retained_count=retained,
            filter_time="2026-11-24",
        )

        entry = {
            "id": filter_id,
            "过滤编号": result.filter_id,
            "检测编号": detect_id,
            "过滤规则": rule,
            "被滤条数": str(filtered),
            "保留条数": str(retained),
            "过滤时间": result.filter_time,
            "status": "已确认" if rule != "全过滤-纯噪声" else "待复核",
            "pending": rule == "全过滤-纯噪声",
            "abnormal": rule == "全过滤-纯噪声",
        }
        rows.append(entry)
        return result

    def review_filter_decision(self, filter_id: str) -> tuple[bool, str]:
        """复核过滤判定。"""
        rows = store.rows("noise_filter")
        for r in rows:
            if r.get("过滤编号") == filter_id:
                r["status"] = "已确认"
                r["pending"] = False
                return True, f"过滤记录 {filter_id} 已复核确认"
        return False, f"过滤记录 {filter_id} 不存在"

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("noise_filter")
        return {
            "total_filters": len(rows),
            "confirmed": sum(1 for r in rows if r.get("status") == "已确认"),
            "pending_review": sum(1 for r in rows if r.get("status") == "待复核"),
        }


class FieldMappingEngine:
    """字段映射引擎：将源站字段按映射规则转换为标准字段。"""

    @staticmethod
    def map_diff_fields(
        site_no: str, raw_diff_fields: list[str],
    ) -> tuple[list[dict[str, str]], list[str]]:
        """按站点注册的映射规则转换差异字段。"""
        mappings = [
            m for m in store.rows("field_mapping")
            if m.get("站点编号") == site_no and m.get("status") == "已生效"
        ]
        mapped: list[dict[str, str]] = []
        unmapped: list[str] = []
        source_to_target = {m.get("源字段路径", ""): m.get("目标字段", "") for m in mappings}

        for field in raw_diff_fields:
            if field in source_to_target:
                mapped.append({"source": field, "target": source_to_target[field], "status": "已映射"})
            else:
                unmapped.append(field)

        return mapped, unmapped

    def snapshot(self) -> dict[str, Any]:
        rows = store.rows("field_mapping")
        return {
            "total_mappings": len(rows),
            "active": sum(1 for r in rows if r.get("status") == "已生效"),
        }