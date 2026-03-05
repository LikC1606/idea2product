# Web 层参考

## REST API（src/web/api/projects.py）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/projects | 创建项目 `{\"start_chat\": true}` 或 `{\"requirement\": \"...\"}` |
| GET | /api/projects | 项目列表（含 timeline 字段：planning_completed_at、generation_completed_at、validation_last_run_at） |
| GET | /api/projects/<id> | 项目详情（附带 timeline 字段） |
| GET | /api/projects/<id>/status | 生成状态（idle/pending/processing/completed/failed） |
| POST | /api/projects/<id>/chat | 发送消息，获取 AI 回复 |
| POST | /api/projects/<id>/generate | 显式触发生成 |
| GET | /api/projects/<id>/chat | 聊天历史 |
| GET | /api/projects/<id>/files | 生成文件列表 |
| GET | /api/projects/<id>/file/<path> | 文件内容 |
| GET | /api/projects/<id>/preview-url | 实时预览 URL |
| GET | /api/projects/<id>/plan | 获取 Stage 2 生成的 EngineeringPlan JSON |
| PATCH | /api/projects/<id>/plan | 局部更新 EngineeringPlan（当前支持任务 name/description/priority/complexity 等安全字段） |
| GET | /api/projects/<id>/validation-runs | 获取项目的验证历史列表（ValidationRun 摘要） |
| GET | /api/projects/<id>/validation-runs/<run_id> | 获取单次验证 run 的详细信息 |
| GET | /api/projects/<id>/overview | 项目概览（项目状态 + 时间线 + 规划/验证摘要），供仪表盘使用 |
| DELETE | /api/projects/<id> | 删除项目 |

- **project_id 校验**：所有带 `<id>` 的路由会校验 `project_id` 格式（仅允许 `proj_[a-zA-Z0-9_-]+`，拒绝 `..` 与路径分隔符），非法时返回 `400 {"error": "Invalid project id"}`。
- **500 响应**：未捕获异常经 errorhandler 返回 JSON `{"error": "..."}`；默认不向客户端暴露详情，设置 `EXPOSE_ERROR_DETAILS=true` 时可返回 `str(e)`；服务端始终 `logger.exception`。

## Chat-first 流程

1. `POST /api/projects {"start_chat": true}` → 创建项目，返回 project_id
2. `POST /api/projects/<id>/chat {"message": "..."}` → 追加消息，获取 AI 回复
3. 用户可调用 `POST /api/projects/<id>/generate` 显式触发生成，或由前端自动触发
4. 首次生成：`conversation_to_requirements()` → `orchestrator.run_from_stage_2()`
5. 增量：`merge_requirements(existing, new_msg)` → `orchestrator.run_from_stage_2()`
6. 生成完成后 `preview_service.start_preview()` 在动态端口启动应用

## 服务

- **chat_service** (`src/web/services/chat_service.py`) — 持久化 `artifacts/chat.json`
- **preview_service** (`src/web/services/preview_service.py`) — 管理预览子进程、动态端口
- **task_service** (`src/web/services/task_service.py`) — 后台生成，按项目串行化

## See also

- AGENTS_REF — InteractionAgent 的 conversation_to_requirements、merge_requirements
