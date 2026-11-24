"""领域服务注册表：通用资源路由按模块 key 分派到独立业务服务。"""
from __future__ import annotations

from app.services.base import BaseModuleService
from app.services.poll_plan import PollPlanService
from app.services.snapshot_store import SnapshotStoreService
from app.services.change_detect import ChangeDetectService
from app.services.diff_extract import DiffExtractService
from app.services.change_event import ChangeEventService
from app.services.field_mapping import FieldMappingService
from app.services.extract_batch import ExtractBatchService
from app.services.crawl_budget import CrawlBudgetService
from app.services.site_registry import SiteRegistryService
from app.services.poll_worker import PollWorkerService
from app.services.task_dispatch import TaskDispatchService
from app.services.noise_filter import NoiseFilterService
from app.services.event_dedup import EventDedupService
from app.services.subscribe_route import SubscribeRouteService
from app.services.push_records import PushRecordsService
from app.services.snapshot_report import SnapshotReportService
from app.services.history_timeline import HistoryTimelineService
from app.services.quality_sample import QualitySampleService
from app.services.replay_compare import ReplayCompareService
from app.services.extract_metrics import ExtractMetricsService
from app.services.cold_archive import ColdArchiveService
from app.services.alert_converge import AlertConvergeService

SERVICES: dict[str, BaseModuleService] = {
    "poll_plan": PollPlanService(),
    "snapshot_store": SnapshotStoreService(),
    "change_detect": ChangeDetectService(),
    "diff_extract": DiffExtractService(),
    "change_event": ChangeEventService(),
    "field_mapping": FieldMappingService(),
    "extract_batch": ExtractBatchService(),
    "crawl_budget": CrawlBudgetService(),
    "site_registry": SiteRegistryService(),
    "poll_worker": PollWorkerService(),
    "task_dispatch": TaskDispatchService(),
    "noise_filter": NoiseFilterService(),
    "event_dedup": EventDedupService(),
    "subscribe_route": SubscribeRouteService(),
    "push_records": PushRecordsService(),
    "snapshot_report": SnapshotReportService(),
    "history_timeline": HistoryTimelineService(),
    "quality_sample": QualitySampleService(),
    "replay_compare": ReplayCompareService(),
    "extract_metrics": ExtractMetricsService(),
    "cold_archive": ColdArchiveService(),
    "alert_converge": AlertConvergeService(),
}


def service_for(module: str) -> BaseModuleService | None:
    return SERVICES.get(module)
