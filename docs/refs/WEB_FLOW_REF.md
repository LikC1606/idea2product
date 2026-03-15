# Web 层参考

## REST API（src/web/api/projects.py）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 环境与资源健康检查；返回 `status`（healthy/degraded）、`checks`（llm_key_set、projects_dir_writable、python_version 等）。可选 query `check_llm=1` 时若 `HEALTH_CHECK_LLM=true` 会探测 LLM 可达性；否则 `llm_reachable` 为 "skip"。 |
| GET | /api/options/models | 可选模型列表（id, provider, capabilities, roles），供前端用户选择 |
| POST | /api/projects | 创建项目 `{\"start_chat\": true}` 或 `{\"requirement\": \"...\", \"product_type\": \"web\", \"model_id\": \"gpt-4o\"}`（product_type、model_id 可选） |
| GET | /api/projects | 项目列表（含 timeline 字段：planning_completed_at、generation_completed_at、validation_last_run_at） |
| GET | /api/projects/metrics | 稳定性指标（`stage_failure_rate`、`transient_retry_success_rate`、`resume_success_rate`、`avg_recovery_seconds` 等） |
| GET | /api/projects/<id> | 项目详情（附带 timeline 字段） |
| GET | /api/projects/<id>/status | 生成状态（idle/pending/processing/completed/failed） |
| POST | /api/projects/<id>/chat | 发送消息，获取 AI 回复；若回复为问句，则同回包返回 `clarification.questions[0]`（含 `question`、`need_options`、`options[]` 等）供前端渲染 chips |
| POST | /api/projects/<id>/chat/stream | 流式聊天（SSE）；最后一条 `done` 事件会包含 `clarification`（若回复为问句，结构同上） |
| POST | /api/projects/<id>/generate | 显式触发生成；Body 可选 `product_type`、`model_id`；返回真实 enqueue 结果（`started` / `queued_rerun` / `deduped_active` / `deduped_completed` / `rejected_backpressure`） |
| POST | /api/projects/<id>/cancel | 请求取消当前生成任务（协作式取消） |
| GET | /api/projects/<id>/chat | 聊天历史 |
| GET | /api/projects/<id>/files | 生成文件列表 |
| GET | /api/projects/<id>/file/<path> | 文件内容（若为二进制/不可预览文件，返回 415 + error） |
| GET | /api/projects/<id>/preview-url | 实时预览 URL |
| GET | /api/projects/<id>/clarification-questions | （Legacy/Debug）基于**最新一条 assistant 问句**用 LLM 生成结构化澄清选项（questions + options）；使用 fast model（默认 `gpt-4o-mini`）+ 小 token；同一问句短期缓存；LLM 失败时返回 500 + error |
| GET | /api/projects/<id>/plan | 获取 Stage 2 生成的 EngineeringPlan JSON |
| PATCH | /api/projects/<id>/plan | 局部更新 EngineeringPlan（当前支持任务 name/description/priority/complexity 等安全字段） |
| GET | /api/projects/<id>/validation-runs | 获取项目的验证历史列表（ValidationRun 摘要） |
| GET | /api/projects/<id>/validation-runs/<run_id> | 获取单次验证 run 的详细信息 |
| GET | /api/projects/<id>/overview | 项目概览（项目状态 + 时间线 + 规划/验证摘要），供仪表盘使用 |
| DELETE | /api/projects/<id> | 删除项目；当状态为 processing/cancelling 时返回 **409 Conflict**（先取消或等待完成） |

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

## 2026-03-12 更新（可靠性修复）

- `POST /api/projects/<id>/chat` 与 `POST /api/projects/<id>/chat/stream` 现在支持可选字段 `client_message_id`，用于客户端重试/降级时做幂等去重，避免重复写入用户消息。
- `POST /api/projects/<id>/chat/stream` 的请求体 JSON 解析改为严格模式；非法 JSON 统一返回 `400 {"error":"Invalid JSON in request body"}`，与非流式 `chat` 行为一致。
- `GET /api/projects/<id>/events` 在 project 不存在时直接返回 404，不再长时间返回 `unknown` 状态流。
- `GET /api/projects/<id>/preview-url` 返回扩展状态字段：`state`、`starting`、`installing`、`preview_error`；已完成项目首次预览改为异步启动，避免请求长时间阻塞。
- `TaskService.enqueue_generation` 引入输入指纹去重：同项目、同输入（最近消息 + model_id + product_type + plan_version）不再重复排队或重复全量重跑。
- `run_from_stage_2` 引入阶段检查点 `artifacts/stage_state.json`：Stage 2/3 成功产物可在后续同输入重试中复用，实现从最近成功阶段恢复。

## 2026-03-12 下一阶段鲁棒性强化（Web）

- `POST /api/projects/<id>/generate` 改为返回真实排队结果语义，前端可区分“已启动”“重复去重”“背压拒绝”。
- `POST /api/projects/<id>/cancel` 新增任务取消入口；TaskService 在阶段边界检查取消与超时，避免无界运行。
- `GET /api/projects/<id>/events` 增加 `retry`、heartbeat、最大连接时长超时事件，降低静默挂死风险。
- 预览状态新增 `warming`（端口可达前的预热态），仅健康探活通过才置 `running`。

## 2026-03-15 | SSE 事件类型约定

- `GET /api/projects/<id>/events` 流式响应使用命名事件：`event: status`（状态 JSON）、`event: heartbeat`（保活）、`event: timeout`（连接超时）。前端必须使用 `addEventListener('status', ...)` / `addEventListener('timeout', ...)` 接收；`onmessage` 仅对未指定或 `event: message` 生效，无法收到 `status` 更新。
