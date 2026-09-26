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

## 历史快照导出

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/estimate` | POST/GET | 传 `wall_id`、`roll_id`，`save=true` 时落一条 `calc_runs` |
| `/api/runs` | GET | 最近测算（倒序，`?limit=`） |
| `/api/export` | GET | **全量历史快照**，当前 `calc_runs` 序列化为 JSON；导出即冻结，之后新增测算不会改变已落盘的响应 |

`GET /api/export` 响应为 JSON，脚本按如下键名解析：

```json
{
  "exported_at": "2026-09-26T08:00:00+00:00",
  "count": 1,
  "items": [
    {
      "id": 1,
      "wall_id": 1,
      "roll_id": 1,
      "wall_name": "主卧一圈",
      "roll_name": "素色53",
      "note": "",
      "created_at": "2026-09-26T08:00:00+00:00",
      "rolls": 11,
      "drops": 31,
      "strips_per_roll": 3,
      "drop_len_m": 2.7,
      "pattern_m": 0.0,
      "result": { "drops": 31, "drop_len_m": 2.7, "pattern_m": 0.0, "strips_per_roll": 3, "rolls": 11, "wall_id": 1, "roll_id": 1 }
    }
  ]
}
```

解析键名：顶层 `count` / `items`；每条记录的 `id`、`wall_id`、`roll_id`、`wall_name`、`roll_name`、`note`、`created_at`，以及卷数结果 `rolls`、`drops`、`strips_per_roll`、`drop_len_m`、`pattern_m`（同时原样保留在 `result` 对象内）。`items` 按 `id` 升序。

导出落盘供脚本消费：

```bash
curl -s http://localhost:9700/api/export -o history-export.json
python3 -c "import json;d=json.load(open('history-export.json'));print(d['count'], d['items'][0]['rolls'])"
```

## 冻结核验脚本

```bash
./scripts/verify_export_freeze.sh          # 自动起一个隔离 DATA_DIR 的后端，跑完即焚
# 或对已在运行的后端（仅标准库）：
python3 scripts/verify_export_freeze.py --base-url http://localhost:9700 --snapshot /tmp/history-export.json
```

脚本流程：落一条测算并记下 `rolls` → 调一次 `/api/export` 写到旁路文件并断言其中能读到该 `rolls` → 再落一条不同墙/卷的测算（**不再调用导出**）→ 直接重读旁路文件，行数与首条 `rolls` 必须停在导出当下。退出码：`0` 通过；`2` 导出侧不一致（快照内容错或被写动）；`3` 主库侧不一致（在线 `/api/runs` 未反映新测算）；`4` 环境/连接失败。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
