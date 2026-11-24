# 巡更工坊 · 源站变更轮询与差异抽取平台

面向轮询计划、站点快照、变更检测、差异抽取、变更事件订阅推送与噪声过滤的源站变更采集平台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/WorkbenchView.vue|tsx  全部模块共享工作台
│   ├── src/data/modules.ts              18个业务模块配置
│   ├── src/api/              统一请求封装
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/resource.py  通用查询/导出/登记/动作接口
│   ├── app/services/<key>.py    每个模块独立领域逻辑
│   ├── app/services/base.py     共享服务骨架
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8009/api/health`

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5182/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8009`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 轮询计划 | `poll_plan` | 计划单 | 计划编号、站点编号、轮询频率 |
| 快照存储 | `snapshot_store` | 站点快照 | 快照编号、计划编号、抓取时间 |
| 变更检测 | `change_detect` | 检测结果 | 检测编号、快照编号、前序快照 |
| 差异抽取 | `diff_extract` | 差异块 | 差异编号、检测编号、差异类型 |
| 变更事件 | `change_event` | 事件记录 | 事件编号、差异编号、事件级别 |
| 字段映射 | `field_mapping` | 映射规则 | 规则编号、站点编号、源字段路径 |
| 抽取批次 | `extract_batch` | 批次记录 | 批次编号、计划编号、窗口起点 |
| 抓取预算 | `crawl_budget` | 预算台账 | 预算编号、站点编号、日请求上限 |
| 站点登记 | `site_registry` | 站点条目 | 站点编号、站点名称、站点类别 |
| 工作节点 | `poll_worker` | 节点条目 | 节点编号、节点地址、负载上限 |
| 任务派发 | `task_dispatch` | 派发记录 | 派发编号、计划编号、节点编号 |
| 噪声过滤 | `noise_filter` | 过滤记录 | 过滤编号、检测编号、过滤规则 |
| 事件去重 | `event_dedup` | 去重记录 | 去重编号、事件编号、重复指纹 |
| 订阅路由 | `subscribe_route` | 订阅条目 | 订阅编号、订阅方、事件级别过滤 |
| 推送台账 | `push_records` | 推送明细 | 推送编号、事件编号、订阅编号 |
| 对比报告 | `snapshot_report` | 报告条目 | 报告编号、站点编号、统计周期 |
| 历史时间线 | `history_timeline` | 时间线条目 | 时间线编号、站点编号、快照序号 |
| 质量抽样 | `quality_sample` | 抽样单 | 抽样编号、批次编号、抽样条数 |
| 回放对比 | `replay_compare` | 对比记录 | 对比编号、计划编号、原事件条数 |
| 抽取指标 | `extract_metrics` | 指标快照 | 快照编号、统计日期、轮询成功率 |
| 冷归档 | `cold_archive` | 归档快照 | 归档编号、快照编号、归档层级 |
| 告警收敛 | `alert_converge` | 收敛记录 | 收敛编号、告警来源、收敛窗口 |

## 约定

- 全部模块共享`frontend/src/views/WorkbenchView.vue|tsx`和一套资源路由。
- 每个模块仍保留独立`backend/app/services/<模块>.py`；纯前端保留
  `frontend/src/domain/<模块>.ts`，用于承载真实业务差异并维持36题位容量。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。

领域：数据工程
子方向：数据采集、爬虫与RPA
