# 18-wallpaper（墙纸卷数）

Wallpaper — 幅宽分幅 + 花高匹配损耗后的卷数向上取整

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4700 |
| API | http://localhost:9700 |

## 主链

周长层高+花匹配 → 卷数 → 展开示意

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。

## 历史快照导出

`GET /api/export/runs` 把当前全部 `calc_runs` 序列化为一份冻结快照：

- 响应正文即为快照 JSON，同时后端落盘一份到 `DATA_DIR/exports/calc_runs.json`
  （docker 卷内为 `/data/exports/calc_runs.json`）；响应里的 `path` 键给出实际落盘路径。
- 序列化字段拼装集中在 `backend/app/services/export_service.py`，路由只做转发。

解析键名：

| 键 | 含义 |
| --- | --- |
| `kind` | 固定为 `calc_runs_snapshot` |
| `version` | 快照格式版本（当前 `1`） |
| `count` | 行数，等于 `len(items)` |
| `path` | 后端落盘路径（仅响应正文有） |
| `items[].run_id` | calc_run 主键 |
| `items[].wall_id` / `items[].roll_id` | 关联墙 / 卷 |
| `items[].wall_name` / `items[].roll_name` | 关联名称 |
| `items[].rolls` | 卷数（冻结核验的目标字段） |
| `items[].drops` / `items[].drop_len_m` / `items[].pattern_m` / `items[].strips_per_roll` | 测算中间量 |
| `items[].note` / `items[].created_at` | 备注 / 创建时间（UTC ISO） |

## 冻结核验

```bash
python3 scripts/verify_export_freeze.py   # 需 API 已在运行（默认 http://localhost:9700）
```

流程：落一条测算记下 `rolls` → 调导出写到旁路文件
（默认 `scripts/out/calc_runs_snapshot.json`，可用 `EXPORT_SIDECAR` 覆盖）
并断言文件里能读到该 `rolls` → 再落一条不同墙/卷的测算但**不再导出** →
直读旁路文件，行数与首条 `rolls` 必须仍停在导出当下。

退出码：`0` 通过；`1` 前置/基础设施问题（API 不可达等）；
`2` 导出侧（快照缺失、不可解析、行数或 `rolls` 漂移）；
`3` 主库侧（测算没落库、`/api/runs` 与返回不一致）。
环境变量 `API_BASE` 可改 API 地址。
