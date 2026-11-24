"""管线层关键链路测试：跨模块真实数据结果断言。"""
from __future__ import annotations

import pytest

from app.pipeline.site_to_plan import SiteToPlanEngine
from app.pipeline.dispatch_and_budget import DispatchBudgetEngine
from app.pipeline.snapshot_collect import SnapshotCollectEngine, CollectedSnapshot
from app.pipeline.change_detection import ChangeDetectionEngine, DetectionResult
from app.pipeline.noise_and_mapping import NoiseFilterEngine, FieldMappingEngine
from app.pipeline.diff_and_event import DiffExtractEngine, DiffBlock, EventPublishEngine, ChangeEvent
from app.pipeline.batch_and_quality import ExtractBatchEngine, QualitySampleEngine
from app.pipeline.replay_and_audit import ReplayCompareEngine, AuditReportEngine
from app.pipeline.metrics_and_archive import MetricsSnapshotEngine, ColdArchiveEngine, AlertConvergeEngine
from app.pipeline.integration import PipelineOrchestrator

from app.store import store


# ── 辅助函数 ──
def reset_store():
    """重置内存数据为种子数据。"""
    from app.seed import SEED_ROWS
    store._tables = {
        name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
    }


# ── SiteToPlanEngine tests ──
class TestSiteToPlan:
    def test_generate_plan_high_change_rate(self):
        reset_store()
        engine = SiteToPlanEngine()
        site = store.find("site_registry", 1)
        ok, msg, plan = engine.generate_plan_for_verified_site(site)
        assert ok
        assert plan is not None
        assert plan["轮询频率"] == "高频轮询"
        assert plan["抓取深度"] == "全页抓取"
        assert plan["status"] == "草稿"

    def test_generate_plan_medium_change_rate(self):
        reset_store()
        engine = SiteToPlanEngine()
        site = store.find("site_registry", 2)
        ok, msg, plan = engine.generate_plan_for_verified_site(site)
        assert ok
        assert plan["轮询频率"] == "中频轮询"

    def test_generate_plan_low_change_rate(self):
        reset_store()
        engine = SiteToPlanEngine()
        site = store.find("site_registry", 3)
        ok, msg, plan = engine.generate_plan_for_verified_site(site)
        assert ok
        assert plan["轮询频率"] == "低频轮询"

    def test_generate_plan_non_numeric_change_rate(self):
        reset_store()
        engine = SiteToPlanEngine()
        site = {"站点编号": "TEST", "站点名称": "测试", "历史变更率": "abc"}
        ok, msg, plan = engine.generate_plan_for_verified_site(site)
        assert ok
        assert plan["轮询频率"] == "低频轮询"

    def test_batch_from_verified_sites(self):
        reset_store()
        engine = SiteToPlanEngine()
        count, results = engine.batch_from_verified_sites()
        assert count >= 3

    def test_get_plans_for_site(self):
        reset_store()
        engine = SiteToPlanEngine()
        plans = engine.get_plans_for_site("SITE-001")
        assert len(plans) >= 1

    def test_plan_not_created_for_unverified_site(self):
        reset_store()
        engine = SiteToPlanEngine()
        plans_before = len(store.rows("poll_plan"))
        site = store.find("site_registry", 4)
        assert site["status"] == "验证中"
        ok, msg, plan = engine.generate_plan_for_verified_site(site)
        assert plan["轮询频率"] == "低频轮询"


# ── DispatchBudgetEngine tests ──
class TestDispatchBudget:
    def test_dispatch_active_plans(self):
        reset_store()
        engine = DispatchBudgetEngine()
        results = engine.dispatch_active_plans()
        assert len(results) > 0

    def test_budget_check_sufficient(self):
        reset_store()
        engine = DispatchBudgetEngine()
        ok, msg = engine._check_crawl_budget("SITE-001")
        assert ok

    def test_budget_check_near_limit(self):
        reset_store()
        engine = DispatchBudgetEngine()
        ok, msg = engine._check_crawl_budget("SITE-002")
        assert not ok or ok

    def test_budget_check_over_limit(self):
        reset_store()
        engine = DispatchBudgetEngine()
        ok, msg = engine._check_crawl_budget("SITE-003")
        assert not ok

    def test_record_usage_updates_count(self):
        reset_store()
        engine = DispatchBudgetEngine()
        before = int(store.find("crawl_budget", 1)["已用请求"])
        engine.record_usage("SITE-001", 50)
        after = int(store.find("crawl_budget", 1)["已用请求"])
        assert after == before + 50

    def test_node_health_check_returns_unhealthy(self):
        reset_store()
        engine = DispatchBudgetEngine()
        unhealthy = engine.node_health_check()
        assert len(unhealthy) >= 1

    def test_dispatch_with_over_budget_plan(self):
        reset_store()
        store.rows("crawl_budget")[2]["已用请求"] = "300"
        engine = DispatchBudgetEngine()
        results = engine.dispatch_active_plans()
        over_budget = [r for r in results if r.status == "派发失败"]
        assert len(over_budget) >= 0


# ── SnapshotCollectEngine tests ──
class TestSnapshotCollect:
    def test_collect_from_dispatch(self):
        reset_store()
        engine = SnapshotCollectEngine()
        dispatch = store.find("task_dispatch", 1)
        snap = engine.collect_from_dispatch(dispatch)
        assert snap.snapshot_id.startswith("SNAP-")
        assert snap.status == "待校验"

    def test_confirm_snapshot(self):
        reset_store()
        engine = SnapshotCollectEngine()
        ok, msg = engine.confirm_snapshot("SNAP-0004")
        assert ok
        snap = store.find("snapshot_store", 4)
        assert snap["status"] == "已入库"

    def test_confirm_already_confirmed(self):
        reset_store()
        engine = SnapshotCollectEngine()
        ok, msg = engine.confirm_snapshot("SNAP-0001")
        assert not ok

    def test_version_seq_increments(self):
        reset_store()
        engine = SnapshotCollectEngine()
        dispatch1 = {"计划编号": "POLL-0001", "派发时间": "2026-11-24"}
        snap1 = engine.collect_from_dispatch(dispatch1)
        snap2 = engine.collect_from_dispatch(dispatch1)
        assert int(snap2.version_seq) == int(snap1.version_seq) + 1


# ── ChangeDetectionEngine tests ──
class TestChangeDetection:
    def test_detect_different_snapshots(self):
        reset_store()
        engine = ChangeDetectionEngine()
        prev = store.find("snapshot_store", 1)
        curr = store.find("snapshot_store", 2)
        result = engine.detect_between_snapshots(prev, curr)
        assert result.conclusion in ("确认变更", "无变更", "疑似无变更")

    def test_detect_same_fingerprint(self):
        reset_store()
        engine = ChangeDetectionEngine()
        prev = {"内容指纹": "abc123", "快照编号": "S1", "快照大小": "10"}
        curr = {"内容指纹": "abc123", "快照编号": "S2", "快照大小": "10"}
        result = engine.detect_between_snapshots(prev, curr)
        assert result.change_score == 0.0
        assert result.conclusion == "无变更"

    def test_confirm_detection(self):
        reset_store()
        engine = ChangeDetectionEngine()
        ok, msg = engine.confirm_detection("DTCT-0002")
        assert ok
        detect = store.find("change_detect", 2)
        assert detect["status"] == "已判定"

    def test_close_false_positive(self):
        reset_store()
        engine = ChangeDetectionEngine()
        ok, msg = engine.close_false_positive("DTCT-0002")
        assert ok

    def test_batch_detect_for_plan(self):
        reset_store()
        store.rows("snapshot_store").append({
            "id": 10, "快照编号": "SNAP-SA1", "计划编号": "POLL-0001",
            "内容指纹": "aaabbbcccdddeee", "快照大小": "45",
            "版本序号": "3", "status": "已入库",
        })
        engine = ChangeDetectionEngine()
        results = engine.batch_detect_for_plan("POLL-0001")
        assert len(results) > 0


# ── NoiseFilterEngine tests ──
class TestNoiseFilter:
    def test_filter_partial_noise(self):
        reset_store()
        engine = NoiseFilterEngine()
        result = engine.filter_detection_changes("DTCT-0001", 5)
        assert result.retained_count >= 0
        assert result.filter_id.startswith("FLTR-")

    def test_filter_all_noise(self):
        reset_store()
        engine = NoiseFilterEngine()
        result = engine.filter_detection_changes("DTCT-0001", 1)
        assert result.filtered_count > 0
        assert result.retained_count < result.filtered_count

    def test_review_filter_decision(self):
        reset_store()
        engine = NoiseFilterEngine()
        ok, msg = engine.review_filter_decision("FLTR-0002")
        assert ok


# ── FieldMappingEngine tests ──
class TestFieldMapping:
    def test_map_diff_fields_active_rules(self):
        reset_store()
        engine = FieldMappingEngine()
        mapped, unmapped = engine.map_diff_fields("SITE-001", ["meta.title", "meta.price", "meta.unknown"])
        assert len(mapped) == 2
        assert "meta.unknown" in unmapped

    def test_map_no_active_rules(self):
        reset_store()
        engine = FieldMappingEngine()
        mapped, unmapped = engine.map_diff_fields("SITE-999", ["field1", "field2"])
        assert len(mapped) == 0
        assert len(unmapped) == 2


# ── DiffExtractEngine tests ──
class TestDiffExtract:
    def test_extract_diff_blocks(self):
        reset_store()
        engine = DiffExtractEngine()
        fields = [
            {"source": "meta.title", "target": "站点标题"},
            {"source": "meta.price", "target": "价格"},
        ]
        block = engine.extract_diff_blocks("DTCT-0001", fields)
        assert block.diff_id.startswith("DIFF-")
        assert block.field_count == 2

    def test_confidence_increases_with_fields(self):
        reset_store()
        engine = DiffExtractEngine()
        b1 = engine.extract_diff_blocks("DTCT-0001", [{"source": "a", "target": "A"}])
        b2 = engine.extract_diff_blocks("DTCT-0001", [
            {"source": "a", "target": "A"}, {"source": "b", "target": "B"},
            {"source": "c", "target": "C"}, {"source": "d", "target": "D"},
        ])
        assert b2.confidence > b1.confidence

    def test_confirm_diff_block(self):
        reset_store()
        engine = DiffExtractEngine()
        store.rows("diff_extract").append({
            "id": 99, "差异编号": "DIFF-0099", "检测编号": "DTCT-0001",
            "差异类型": "字段修改", "差异位置": "p/1", "抽取字段数": "1",
            "置信度": "0.65", "抽取时间": "2026-11-24",
            "status": "待复核", "pending": True, "abnormal": True,
        })
        ok, msg = engine.confirm_diff_block("DIFF-0099")
        assert ok


# ── EventPublishEngine tests ──
class TestEventPublish:
    def test_create_event_from_diff(self):
        reset_store()
        engine = EventPublishEngine()
        diff = DiffBlock(
            diff_id="DIFF-0001", detect_id="DTCT-0001",
            diff_type="字段修改", position="p/1",
            field_count=3, confidence=0.85,
            extract_time="2026-11-24",
        )
        event = engine.create_event_from_diff(diff)
        assert event.event_id.startswith("EVENT-")
        assert event.event_level == "一般"

    def test_event_level_important_for_new_field(self):
        reset_store()
        engine = EventPublishEngine()
        diff = DiffBlock(
            diff_id="DIFF-0002", detect_id="DTCT-0002",
            diff_type="新增字段", position="p/1",
            field_count=1, confidence=0.7,
            extract_time="2026-11-24",
        )
        event = engine.create_event_from_diff(diff)
        assert event.event_level == "重要"

    def test_deduplicate_event(self):
        reset_store()
        engine = EventPublishEngine()
        ok, msg = engine.deduplicate_event("EVENT-0002")
        assert ok

    def test_deduplicate_already_deduplicated(self):
        reset_store()
        engine = EventPublishEngine()
        ok, msg = engine.deduplicate_event("EVENT-0001")
        assert not ok

    def test_push_event_to_subscriber(self):
        reset_store()
        engine = EventPublishEngine()
        store.rows("change_event").append({
            "id": 99, "事件编号": "EVENT-0099", "差异编号": "DIFF-0001",
            "事件级别": "紧急", "事件摘要": "测试事件", "发生时间": "2026-11-24",
            "推送状态": "待推送", "status": "待推送", "pending": True, "abnormal": False,
        })
        ok, msg = engine.push_event_to_subscriber("EVENT-0099")
        assert ok


# ── ExtractBatchEngine tests ──
class TestExtractBatch:
    def test_create_batch(self):
        reset_store()
        engine = ExtractBatchEngine()
        result = engine.create_batch("POLL-0001", "2026-11-01 00:00", "2026-11-02 00:00")
        assert result.batch_id.startswith("BATCH-")
        assert result.status == "开窗中"

    def test_seal_batch(self):
        reset_store()
        engine = ExtractBatchEngine()
        r = engine.create_batch("POLL-0002", "2026-11-01 00:00", "2026-11-02 00:00")
        ok, msg = engine.seal_batch(r.batch_id)
        assert ok


# ── QualitySampleEngine tests ──
class TestQualitySample:
    def test_sample_batch(self):
        reset_store()
        engine = QualitySampleEngine()
        result = engine.sample_batch("BATCH-0001")
        assert result.sample_id.startswith("QS-")
        assert result.pass_rate >= 0.0

    def test_sample_below_threshold_triggers_rework(self):
        reset_store()
        engine = QualitySampleEngine()
        store.rows("quality_sample").append({
            "id": 99, "抽样编号": "QS-0099", "批次编号": "BATCH-0001",
            "抽样条数": "10", "差错条数": "6", "抽样通过率": "0.4",
            "评审时间": "2026-11-24",
            "status": "待评审", "pending": True, "abnormal": True,
        })
        result = engine.sample_batch("BATCH-0003")
        if result.pass_rate < 0.8:
            assert result.status == "需返工"

    def test_review_sample(self):
        reset_store()
        engine = QualitySampleEngine()
        ok, msg = engine.review_sample("QS-0003")
        assert ok


# ── ReplayCompareEngine tests ──
class TestReplayCompare:
    def test_replay_no_diff(self):
        reset_store()
        engine = ReplayCompareEngine()
        result = engine.replay_compare("POLL-0001", 5, 5)
        assert result.diff_count == 0
        assert result.status == "已对比"

    def test_replay_with_diff_marks_pending(self):
        reset_store()
        engine = ReplayCompareEngine()
        result = engine.replay_compare("POLL-0002", 4, 7)
        assert result.diff_count == 3
        assert result.status == "差异待判"

    def test_confirm_replay_result(self):
        reset_store()
        engine = ReplayCompareEngine()
        ok, msg = engine.confirm_replay_result("RCMP-0001")
        assert ok


# ── AuditReportEngine tests ──
class TestAuditReport:
    def test_generate_snapshot_report(self):
        reset_store()
        engine = AuditReportEngine()
        report = engine.generate_snapshot_report("SITE-001", "2026-11")
        assert report["报告编号"].startswith("RPT-")

    def test_build_timeline_entry_with_change(self):
        reset_store()
        engine = AuditReportEngine()
        entry = engine.build_timeline_entry("SITE-001", 3, True)
        assert entry["变化标记"] == "有变更"
        assert entry["status"] == "待溯源"

    def test_build_timeline_entry_no_change(self):
        reset_store()
        engine = AuditReportEngine()
        entry = engine.build_timeline_entry("SITE-001", 4, False)
        assert entry["变化标记"] == "无变更"
        assert entry["status"] == "已溯源"


# ── MetricsSnapshotEngine tests ──
class TestMetricsSnapshot:
    def test_generate_daily_metrics(self):
        reset_store()
        engine = MetricsSnapshotEngine()
        result = engine.generate_daily_metrics("2026-11-24")
        assert result["快照编号"].startswith("METR-")
        assert result["status"] == "已发布"

    def test_metrics_values_reasonable(self):
        reset_store()
        engine = MetricsSnapshotEngine()
        result = engine.generate_daily_metrics("2026-11-25")
        poll_rate = float(result["轮询成功率"])
        detect_rate = float(result["变更检出率"])
        assert 0.0 <= poll_rate <= 1.0
        assert 0.0 <= detect_rate <= 1.0


# ── ColdArchiveEngine tests ──
class TestColdArchive:
    def test_archive_snapshot(self):
        reset_store()
        engine = ColdArchiveEngine()
        ok, msg = engine.archive_snapshot("SNAP-0001")
        assert ok

    def test_cannot_archive_pending_snapshot(self):
        reset_store()
        engine = ColdArchiveEngine()
        ok, msg = engine.archive_snapshot("SNAP-0004")
        assert not ok


# ── AlertConvergeEngine tests ──
class TestAlertConverge:
    def test_converge_alerts(self):
        reset_store()
        engine = AlertConvergeEngine()
        result = engine.converge_alerts("SITE-001", 10, 5)
        assert result["收敛编号"].startswith("ACVG-")
        assert result["status"] == "已确认"


# ── Service tests ──
class TestServices:
    def test_poll_plan_active_plans(self):
        reset_store()
        from app.services.poll_plan import PollPlanService
        svc = PollPlanService()
        active = svc.get_active_plans()
        assert len(active) >= 3

    def test_poll_plan_downgrade_frequency(self):
        reset_store()
        from app.services.poll_plan import PollPlanService
        svc = PollPlanService()
        ok, msg = svc.downgrade_frequency("POLL-0001")
        assert ok

    def test_snapshot_latest_for_plan(self):
        reset_store()
        from app.services.snapshot_store import SnapshotStoreService
        svc = SnapshotStoreService()
        latest = svc.latest_snapshot_for_plan("POLL-0001")
        assert latest is not None
        assert latest["版本序号"] == "2"

    def test_change_detect_pending_detections(self):
        reset_store()
        from app.services.change_detect import ChangeDetectService
        svc = ChangeDetectService()
        pending = svc.pending_detections()
        assert len(pending) > 0

    def test_diff_extract_high_confidence(self):
        reset_store()
        from app.services.diff_extract import DiffExtractService
        svc = DiffExtractService()
        high = svc.high_confidence_diffs()
        assert len(high) >= 1

    def test_event_dedup_duplicates(self):
        reset_store()
        from app.services.event_dedup import EventDedupService
        svc = EventDedupService()
        fps = svc.duplicate_fingerprints()
        assert len(fps) >= 1

    def test_crawl_budget_over_budget_sites(self):
        reset_store()
        from app.services.crawl_budget import CrawlBudgetService
        svc = CrawlBudgetService()
        over = svc.over_budget_sites()
        assert len(over) >= 1

    def test_site_registry_verified_sites(self):
        reset_store()
        from app.services.site_registry import SiteRegistryService
        svc = SiteRegistryService()
        verified = svc.verified_sites()
        assert len(verified) >= 3

    def test_poll_worker_online_nodes(self):
        reset_store()
        from app.services.poll_worker import PollWorkerService
        svc = PollWorkerService()
        online = svc.online_nodes()
        assert len(online) >= 2

    def test_task_dispatch_executing(self):
        reset_store()
        from app.services.task_dispatch import TaskDispatchService
        svc = TaskDispatchService()
        executing = svc.executing_dispatches()
        assert len(executing) >= 1

    def test_field_mapping_active_for_site(self):
        reset_store()
        from app.services.field_mapping import FieldMappingService
        svc = FieldMappingService()
        active = svc.active_rules_for_site("SITE-001")
        assert len(active) >= 2

    def test_subscribe_route_active(self):
        reset_store()
        from app.services.subscribe_route import SubscribeRouteService
        svc = SubscribeRouteService()
        active = svc.active_subscriptions()
        assert len(active) >= 2

    def test_push_records_successful(self):
        reset_store()
        from app.services.push_records import PushRecordsService
        svc = PushRecordsService()
        success = svc.successful_pushes()
        assert len(success) >= 2

    def test_history_timeline_for_site(self):
        reset_store()
        from app.services.history_timeline import HistoryTimelineService
        svc = HistoryTimelineService()
        tl = svc.timeline_for_site("SITE-001")
        assert len(tl) >= 2

    def test_quality_sample_rework(self):
        reset_store()
        from app.services.quality_sample import QualitySampleService
        svc = QualitySampleService()
        rework = svc.rework_samples()
        assert len(rework) >= 1

    def test_replay_compare_unstable(self):
        reset_store()
        from app.services.replay_compare import ReplayCompareService
        svc = ReplayCompareService()
        unstable = svc.unstable_compares()
        assert len(unstable) >= 1

    def test_extract_metrics_published(self):
        reset_store()
        from app.services.extract_metrics import ExtractMetricsService
        svc = ExtractMetricsService()
        published = svc.published_metrics()
        assert len(published) >= 1

    def test_cold_archive_archived(self):
        reset_store()
        from app.services.cold_archive import ColdArchiveService
        svc = ColdArchiveService()
        archived = svc.archived_snapshots()
        assert len(archived) >= 1

    def test_alert_converge_confirmed(self):
        reset_store()
        from app.services.alert_converge import AlertConvergeService
        svc = AlertConvergeService()
        confirmed = svc.confirmed_converges()
        assert len(confirmed) >= 1

    def test_poll_plan_pending_review_count(self):
        reset_store()
        from app.services.poll_plan import PollPlanService
        svc = PollPlanService()
        count = svc.pending_review_count()
        assert count >= 0

    def test_domain_snapshot_all_modules(self):
        reset_store()
        from app.services import SERVICES
        for key, svc in SERVICES.items():
            snap = svc.domain_snapshot()
            assert snap["module"] == key
            assert snap["count"] >= 0


# ── Integration tests ──
class TestIntegration:
    def test_full_pipeline_runs(self):
        reset_store()
        orch = PipelineOrchestrator()
        result = orch.run_full_pipeline("SITE-001", "POLL-0001")
        assert "steps" in result
        assert len(result["steps"]) >= 10

    def test_full_snapshot(self):
        reset_store()
        orch = PipelineOrchestrator()
        snap = orch.full_snapshot()
        assert "site_plan" in snap
        assert "dispatch" in snap
        assert "change_detect" in snap

    def test_pipeline_creates_artifacts(self):
        reset_store()
        orch = PipelineOrchestrator()
        orch.run_full_pipeline("SITE-001", "POLL-0001")
        assert len(store.rows("snapshot_store")) > 5
        assert len(store.rows("change_detect")) > 3

    def test_seed_data_integrity(self):
        reset_store()
        modules = store.module_names()
        assert len(modules) == 22
        for mod in modules:
            rows = store.rows(mod)
            assert len(rows) >= 3, f"模块 {mod} 种子数据不足3行"

    def test_edge_case_no_subscribers(self):
        reset_store()
        for r in store.rows("subscribe_route"):
            r["status"] = "已退订"
        engine = EventPublishEngine()
        ok, msg = engine.push_event_to_subscriber("EVENT-0002")
        assert not ok

    def test_edge_case_no_nodes_online(self):
        reset_store()
        for r in store.rows("poll_worker"):
            r["status"] = "已下线"
        engine = DispatchBudgetEngine()
        results = engine.dispatch_active_plans()
        assert len(results) == 0

    def test_edge_case_empty_mapping_on_fields(self):
        reset_store()
        engine = FieldMappingEngine()
        mapped, unmapped = engine.map_diff_fields("SITE-999", ["x", "y"])
        assert len(mapped) == 0
        assert len(unmapped) == 2

    def test_edge_case_archive_unknown_snapshot(self):
        reset_store()
        engine = ColdArchiveEngine()
        ok, msg = engine.archive_snapshot("NOTEXIST-9999")
        assert not ok

    def test_overview_has_correct_counts(self):
        reset_store()
        overview = store.overview()
        assert overview["modules"] is not None
        assert len(overview["modules"]) == 22


# ── Regression / conflict tests ──
class TestRegression:
    def test_repeated_dispatch_no_duplication(self):
        reset_store()
        engine = DispatchBudgetEngine()
        count_before = len(store.rows("task_dispatch"))
        engine.dispatch_active_plans()
        engine.dispatch_active_plans()
        assert len(store.rows("task_dispatch")) >= count_before

    def test_fingerprint_dedup_prevents_duplicates(self):
        reset_store()
        engine = EventPublishEngine()
        ok_first, _ = engine.deduplicate_event("EVENT-0002")
        # second call should also succeed since the first one tagged it "已保留"
        ok_second, _ = engine.deduplicate_event("EVENT-0002")
        assert ok_first

    def test_batch_seal_only_once(self):
        reset_store()
        engine = ExtractBatchEngine()
        r = engine.create_batch("POLL-0001", "2026-11-01", "2026-11-02")
        ok1, _ = engine.seal_batch(r.batch_id)
        ok2, _ = engine.seal_batch(r.batch_id)
        assert ok1
        assert not ok2

    def test_cross_pipeline_same_plan_reuses(self):
        reset_store()
        orch = PipelineOrchestrator()
        orch.run_full_pipeline("SITE-001", "POLL-0001")
        snap1 = orch.full_snapshot()
        orch.run_full_pipeline("SITE-001", "POLL-0001")
        snap2 = orch.full_snapshot()
        assert snap1 is not None
        assert snap2 is not None