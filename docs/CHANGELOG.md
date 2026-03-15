# Changelog

每次修改代码后，在此追加一条记录。格式：`## YYYY-MM-DD | [scope] 简要描述`

**scope 可选**：`agents` | `data-models` | `web` | `prompts` | `code-gen` | `services` | `utils` | `config` | `troubleshooting` | `other`

---

## 2026-03-15 | [other] 新增 bug 发现测试 tests/test_bug_hunting.py

- 数据模型边界：Requirements 空 features、Feature priority 1–5、Task 依赖字符串、CodeRepository 空 files/必填 structure。
- TaskService：enqueue 返回值 started/deduped_completed/rejected_backpressure、未知 project get_status 为 None。
- Skeleton builder：空 interface_specs/file_structure 返回空 dict 或最小 skeleton。
- Preview：无 generated/ 或无入口时 start_preview 返回 None 且 get_preview_status 为 error。
- Orchestrator：Stage 3 失败时 context.json 含 partial_failure 与 failed_stage=3。

## 2026-03-15 | [web][frontend] 深入 debug：删除时禁止进行中、cancelled 状态与 409 处理

- **DELETE /api/projects/<id>**：当项目状态为 `processing` 或 `cancelling` 时返回 **409 Conflict**，提示先取消或等待完成，避免删除目录后后台任务写盘异常。`TaskService.delete_project` 改为返回 `"deleted"` | `"not_found"` | `"busy"` 供 API 区分 200/404/409。
- **前端**：状态栏与轮询支持 `status === 'cancelled'`（文案与 stopPolling）；`deleteProject` 对 409 抛出明确错误信息。

## 2026-03-15 | [web][frontend] 前后端接口检查：健康检查、delete/cancel 封装

- **checkBackend**：改为请求 `GET /api/health`，返回 `{ ok, degraded?, checks? }`；503 或 `status=degraded` 时仍视为可达并设 `degraded: true`；健康不可用时 fallback 到 `GET /api/projects`。WorkspaceShell 使用 `result?.ok` 判断是否连接。
- **前端 API**：新增 `deleteProject(projectId)`（DELETE）、`cancelGeneration(projectId)`（POST /cancel），与后端一致，便于后续 UI 接入。

## 2026-03-15 | [web][frontend] 深入调试：SSE 事件类型、delete 清理、澄清缓存上限

- **SSE**：后端发送 `event: status` / `event: timeout`，前端原用 `onmessage`（仅接收默认 `message` 类型）。改为 `addEventListener('status', ...)` 与 `addEventListener('timeout', ...)`，确保状态更新能实时推送到 UI。
- **TaskService.delete_project**：删除项目时同时清理 `_project_locks`、`_pending_regenerate`、`_active_fingerprints`、`_last_completed_fingerprint`、`_cancelled_projects`、`_run_starts`、`_run_trace_ids`，避免长期运行后内存与锁字典无限增长。

## 2026-03-15 | [web][frontend] 更细致修复：流式 fallback 不重复 assistant、澄清缓存上限

- **前端 useChat**：流式请求失败后 fallback 到非流式时，若已有 assistant 消息（部分流式内容），改为更新该条内容为完整回复，避免出现两条 assistant 消息。
- **澄清缓存**：`_CLARIFY_CACHE` 增加上限 `_CLARIFY_CACHE_MAX_SIZE=500`，写入前若已满则移除最旧一项，避免长时间运行内存持续增长。

## 2026-03-15 | [agents][web] 修复 chat 回复强加问号与 get_file 编码错误处理

- **InteractionAgent**：`_normalize_chat_reply` 增加参数 `ensure_question=False`；`reply_in_chat`/`reply_in_chat_stream` 不再强制将回复结尾改为 `?`，保留 LLM 原始句尾（句号等）；需强制单问句的澄清流程可传 `ensure_question=True`。
- **TaskService.get_file**：对非 UTF-8 文本文件改用 `read_text(encoding="utf-8", errors="replace")`，避免抛出 BinaryFileError，与测试及“编码问题返回内容或 None”的约定一致。

## 2026-03-15 | [config] 默认模型切换至 OpenAI GPT-5 系列

- **主模型**：`OPENAI_MODEL` / `openai_model` 默认由 `gpt-4o` 改为 `gpt-5.4`；`OPENAI_VLM_MODEL` / `openai_vlm_model` 改为 `gpt-5.4`。
- **快速/轻量模型**：`fast_model_for_review`、`fast_model_for_code_gen` 默认由 `gpt-4o-mini` 改为 `gpt-5-mini`。
- **图像模型**：`image_generation_openai_model` 默认由 `dall-e-3` 改为 `gpt-image-1.5`（DALL-E 3 已标记为 Deprecated）。
- **模型注册表**：`config/models_registry.json` 更新为 GPT-5 系列（gpt-5.4、gpt-5.4-pro、gpt-5-mini、gpt-5-nano、gpt-5、gpt-4.1），供前端选择与 stage 路由。`.env.example` 中 `OPENAI_MODEL`/`OPENAI_VLM_MODEL` 已同步更新。

## 2026-03-15 | [config][web][agents] Phase 2：环境自检、规划校验、导入检查默认开启、语法修复轮数

- **环境自检**：新增 `src/utils/env_check.py`，校验 LLM API Key、projects_dir 可写、Python 版本；`GET /api/health` 使用该模块，支持 `?check_llm=1`（需 `HEALTH_CHECK_LLM=true`）探测 LLM 可达性；启动时可选执行 `run_startup_env_check`（`ENABLE_STARTUP_ENV_CHECK`，默认 True）。CLAUDE.md 增加 ENABLE_STARTUP_ENV_CHECK、HEALTH_CHECK_LLM；TROUBLESHOOTING 增加环境自检与 /api/health 说明。
- **规划完整性**：新增 `src/utils/plan_validator.py`，在 Stage 2 结束后做轻量校验（入口文件、pyi/interface 覆盖）；Orchestrator 在 `enable_plan_completeness_check=True` 时调用并打 warning。AGENTS_REF 注明该步骤。
- **Stage 3**：`ENABLE_STAGE3_IMPORT_SANITY_CHECK` 默认改为 True；`code_gen_syntax_fix_retries` 默认改为 2。
- **PROMPTS_REF**：增加「Stage 4 FineTuning 与 TestError 引用」约定，要求修复时传入 file_path/line_number 以定位修复位置。

## 2026-03-15 | [other] 新增项目介绍与当前问题总结文档；Phase 1 可靠性改进

- 新增 **docs/PROJECT_AND_ISSUES.md**：项目介绍 + 三类问题（运行失败、代码有 bug、达不到预期）+ 原因与排查要点 + 推荐排查顺序；CONTEXT_INDEX 已加入该文档与按任务索引。
- **Preview**：`_install_requirements` 失败时写回 `preview_error` 并将 state 置为 `error`，前端可通过 preview-url 获取错误信息。
- **前端**：对 `/generate` 返回的 `started`/`deduped_active`/`deduped_completed`/`rejected_backpressure` 做明确文案与操作引导；429 时返回 body 供前端展示「队列已满，请稍后再试」。
- **500 响应**：当异常为 `StageExecutionError` 时，响应中增加 `error_code`、`failed_stage`，便于前端展示「第 N 阶段失败」而不暴露详情。

## 2026-03-12 | [services] LLM 异常分型与重试预算

- `LLMService` 新增 `TransientLLMError` / `PermanentLLMError` 分型，避免永久错误被误判为瞬时错误重试。
- `generate/stream/stream_messages` 增加 `retry_budget_seconds`，预算耗尽后快速失败，抑制重试放大。

## 2026-03-12 | [web] 真实 enqueue 语义、取消入口与 SSE/预览状态收敛

- `POST /api/projects/<id>/generate` 返回真实状态：`started` / `queued_rerun` / `deduped_active` / `deduped_completed` / `rejected_backpressure`。
- 新增 `POST /api/projects/<id>/cancel`，支持协作式取消生成。
- `GET /api/projects/<id>/events` 增加 `retry`、heartbeat、最大连接时长超时事件，减少静默挂死。
- `preview` 状态新增 `warming`，健康探活通过后才进入 `running`。

## 2026-03-12 | [agents] Stage4 回退契约与 RunAndFix 隔离执行

- FineTuning 回退生成的 `app.py` 补齐 `create_app()`，与 Stage4 导入校验契约一致。
- `RunAndFixAgent._try_run_app` 改为子进程检查，避免 in-process 导入污染导致跨轮次不稳定。

## 2026-03-12 | [other] 鲁棒性回归补充

- 新增 `tests/test_llm_service_retries.py`，覆盖瞬时重试、预算耗尽、永久错误分型。
- 扩展 `test_task_service_reliability.py`、`test_orchestrator_recovery.py`、`test_projects_api.py`，覆盖永久错误不重试、签名失效重跑、取消接口与新 generate 语义。

## 2026-03-12 | [services] LLM 重试分类与模型能力匹配收敛

- `LLMService` 重试策略改为“仅瞬时错误可重试”：timeout/connection/429/5xx 走指数退避+jitter（支持 Retry-After），4xx 类非瞬时错误快速失败并统一抛 `LLMServiceError`。
- 修复 `LLMService` usage 日志空字段导致二次异常的问题，降低“调用成功但日志失败”误报。
- `ModelSelector` fallback 改为必须满足全部 `required_capabilities`，避免选到能力不完整模型导致后续阶段失败。

## 2026-03-12 | [web] 任务幂等去重、检查点恢复与可靠性指标

- `TaskService` 新增输入指纹（消息摘要 + model_id + product_type + plan_version），同输入重复触发不再重复排队或二次全量重跑。
- 增加可靠性指标聚合与 API：`GET /api/projects/metrics` 输出 `stage_failure_rate`、`transient_retry_success_rate`、`resume_success_rate`、`avg_recovery_seconds` 等。
- `Orchestrator.run_from_stage_2` 新增 `artifacts/stage_state.json` 阶段检查点，Stage 2/3 成功产物可在同输入重试中复用，实现从最近成功阶段恢复。

## 2026-03-12 | [agents] Stage 3 增量扫描与 Stage 4 隔离校验

- Stage 3 `CodeGenerationAgent` 引入按任务快照 diff 的增量扫描，仅对变更文件执行 symbol/snippet 增量更新，减少重复全量处理开销。
- Stage 4 `FullCycleTestingAgent` 依赖安装增加 run 内缓存（requirements hash + Python 版本），去除重复 `pip install`。
- Stage 4 导入与前端路由校验迁移至子进程隔离执行，避免污染解释器状态导致跨轮次不稳定。

## 2026-03-12 | [other] 稳定性回归测试与 CI 门禁补齐

- 新增 `tests/test_task_service_reliability.py`（指纹去重、瞬时错误重试成功率）与 `tests/test_orchestrator_recovery.py`（阶段检查点恢复）。
- `tests/test_projects_api.py` 新增 `/api/projects/metrics` 回归用例。
- CI 新增 `Reliability regression tests` 步骤，显式执行稳定性关键回归测试。

## 2026-03-10 | agents, code-gen, troubleshooting Stage 3 最小 Flask 骨架兜底与 Stage 4 运行环境隔离

- **Stage 4 FullCycleTesting**：在 `_try_run_with_subprocess` 中为子进程构造隔离的运行环境，将 `data/projects/<id>/generated` 目录置于 `PYTHONPATH` 首位，避免 `import config` 等导入命中仓库根部的 `config/` 包；错误仍通过 `TestError`/日志完整上报。
- **Stage 3 CodeGenerationAgent**：新增 `_ensure_minimum_files()`，在 Agent 任务完成后根据 `engineering_plan.file_structure` + `pyi_stubs` + `api_specs.frontend_routes` 兜底生成最小可运行 Flask 骨架（缺失的 `app/models/*.py`、`app/routes/*.py` 与关键 `templates/*.html` 会被补齐为简单但可运行的实现）。
- **文档**：更新 `AGENTS_REF` 中 CodeGenerationAgent/FullCycleTestingAgent 行为说明，`CODE_GEN_SPEC` 增加最小骨架兜底入口；`TROUBLESHOOTING` 中补充「Empty or minimal generated code」与 `config` 导入冲突的排查指引。

## 2026-03-06 | agents, web, prompts 澄清选项 JSON 结构统一（question + need_options + options）

- **Agent**：`InteractionAgent.ClarificationQuestion` 增加 `need_options` 字段，用于标记某个澄清问句是否需要结构化选项；`generate_options_for_question()` 改为期望 LLM 返回 `{question, need_options, options[]}` 形态的 JSON，并在 question 为空时回退到原始 assistant 问句。
- **Web API**：`_get_or_build_clarification_payload()` 在构造 `clarification.questions[0]` 时补充 `need_options` 字段，前端据此判断是否渲染 chips；结构保持向后兼容（默认为 true）。
- **Prompts**：`interaction_clarification_options_for_question.txt` 的 Output 规范调整为返回带 `question`、`need_options` 与 `options[]` 的 JSON 对象；`PROMPTS_REF`、`WEB_FLOW_REF` 与 `AGENTS_REF` 对应说明已更新。
- **前端**：`ChatPanel.vue` 的 `clarificationQuestions` 仅保留 `need_options !== false` 的问题，避免未来扩展为开放式澄清问句时仍强制渲染选项。

## 2026-03-06 | web, prompts Chat 同回包返回澄清选项（无示例问句）

- **Chat API**：`POST /api/projects/<id>/chat` 与 `POST /api/projects/<id>/chat/stream` 在 assistant 回复为问句时，同回包（stream 在 `done` 事件）返回 `clarification.questions[0].options`，前端无需再额外调用澄清选项接口。
- **对话约束**：`interaction_chat_system.txt` 改为严格单问句输出，禁止在消息中包含示例回答或选项列表（选项由结构化字段提供）。
- **兼容保留**：`GET /api/projects/<id>/clarification-questions` 保留为 Legacy/Debug 路径，LLM 失败时仍返回 500 + error。
- **Agent 行为**：InteractionAgent 在 `reply_in_chat()` / `reply_in_chat_stream()` 中增加后处理逻辑，只保留最后一个以 `?`/`？` 结尾的问句，并裁剪掉任何残留的 “For example/Examples/例如/比如” 段落，保证前端看到的永远是一句澄清问题而不是带示例的长段落。

## 2026-03-06 | data-models, agents, services, web 多产品类型与 Stage 2 分计划、模型按类型与用户选择

- **数据模型**：新增 ProductType 枚举（web, pdf, video, audio, app）；Requirements 与 EngineeringPlan 增加 product_type；EngineeringPlan 增加 latex_specs、video_specs、audio_specs；ExecutionContext 增加 product_type、model_id。
- **Stage 2**：execute_stage_2 按 product_type 分支；web/app 走现有 FlowSimulation → TaskDivision → SchemePlanning；pdf/video/audio 走 _execute_stage_2_non_web，调用 media_planning_agents（plan_pdf、plan_video、plan_audio）产出对应 specs；adapters.engineering_plan_from_stage2 支持 product_type。
- **模型路由**：config/models_registry.json 增加 product_type_routing；ModelRegistry.get_stage_route(stage, product_type=...)；ModelSelector.select(..., product_type=...)；_llm_for_stage 支持 context.model_id 覆盖与 context.product_type 路由。
- **Orchestrator**：run()、run_from_stage_2() 接受 product_type、model_id；Stage 3 对非 web 类型返回最小 CodeRepository 以完成流水线。
- **Web API**：GET /api/options/models 返回可选模型列表；POST /api/projects 与 POST /api/projects/<id>/generate 支持 body 可选 product_type、model_id；task_service 持久化并传入 orchestrator。
- **文档**：DATA_MODELS_REF、SERVICES_REF、WEB_FLOW_REF、ARCHITECTURE 已更新。

---

## 2026-03-06 | other README 优化：快速上手与结构精简

- **结构**：首屏改为标题 + 一句话描述 + Quick Start 三步 + 前置要求；合并重复的安装/配置说明为单一路径。
- **配置**：与 .env.example 对齐，增加 PRIMARY_LLM_PROVIDER 及 OpenAI/Anthropic/Google 对应 API Key 说明；全量变量表改为链接至 CLAUDE.md 与 .env.example。
- **Web UI**：补全前端构建步骤（生产：`cd frontend && npm run build` 后 `python -m src.web.app`；开发：`npm run dev`）。
- **精简**：删除重复 Installation 小节；Agent 详细映射表移除，保留阶段简表并链接 ARCHITECTURE；精简配置表与故障排查，新增「更多文档」节指向 CONTEXT_INDEX、ARCHITECTURE、AGENTS_REF、WEB_FLOW_REF、TROUBLESHOOTING。

---

## 2026-03-06 | web BuildStudio 交互与预览修复

- **布局滚动**：对齐 `--shell-header-height` / `--shell-status-height` 与实际组件高度，避免右侧面板底部被 StatusBar 遮挡；关闭 `WorkspaceShell` 外层滚动，改由各面板内部自行滚动，减少嵌套滚动导致的可视区计算问题。
- **Plan 面板**：增强 `revealOnScroll` 指令以支持嵌套滚动容器（自动选择 scroll root、放宽 threshold/rootMargin），并让 Plan 的空态/加载/错误态不依赖 reveal 动画；切到 Plan tab 时自动加载规划。
- **Generate 反馈**：点击 Generate 立即在状态栏与聊天区给出 queued 反馈，失败时展示明确错误摘要；`POST /generate` 回显 product_type/model_id。
- **代码视图**：后端文件列表过滤 `__pycache__`/`.pyc` 等二进制与资源文件；尝试预览二进制时返回 415，前端显示友好错误。
- **Preview 稳定性**：启动预览子进程时注入 `FLASK_DEBUG=0`、`FLASK_RUN_RELOAD=0` 等环境变量，降低 debug/reloader 引起的反复重启风险。
- **澄清问题**：新增 `GET /api/projects/<id>/clarification-questions`，前端在对话早期渲染可点击的澄清选项 chips（单选即发，多选可选后发送）。

## 2026-03-06 | web, agents, prompts 澄清选项由 Agent 按问句生成

- **澄清选项**：`GET /api/projects/<id>/clarification-questions` 改为基于最新 assistant 问句调用 LLM 动态生成选项（与提问对齐），LLM 失败时返回 500 + error 以便前端直接展示错误。
- **InteractionAgent**：新增 `generate_options_for_question()`，用于针对单个问句生成 3–6 个选项（UI 另提供“其它/自定义”输入）。
- **Prompts**：新增 `interaction_clarification_options_for_question.txt`，只为给定问句生成选项 JSON。

## 2026-03-06 | web, agents, prompts 澄清交互质量与稳定性增强

- **对话质量**：增强 `interaction_chat_system.txt`，约束为“每次只问 1 个高信号问题”，并提供示例答案以提升澄清效率。
- **选项成功率**：澄清选项接口强制使用 fast model（默认 `gpt-4o-mini`）并限制 token；对同一问句启用短期缓存与前端去重，减少重复 LLM 调用导致的超时/失败。
- **交互体验**：点击澄清选项后，用户消息仅发送“答案”而不复读原问题；错误态提供 Retry，便于手动重试。
- **可观测性**：后端记录 chat/clarify 使用的 model/base_url 与耗时，便于确认实际使用的模型与定位慢请求。

## 2026-03-05 | agents, core, web, config 全流程 Agent 结构与可读性重构

- **Agent 规范**：在 `AGENTS_REF` 顶部增加「Agent 设计规范」小节，约定目录结构、构造函数签名、主入口 `execute` 方法以及日志前缀格式，统一 Stage 1–4 Agent 的风格。
- **Orchestrator 日志与结构**：`src/core/orchestrator.py` 中为 Stage 1–4 的执行方法补充 `[StageN][AgentName]` 风格的日志前缀，并细化 Stage 2/3 的日志（FlowSimulation/TaskDivision/AlgorithmAnalysis/SchemePlanning、CodeMemoryAgent/CodeMiningAgent/CodeGenerationAgent），Stage 4 日志显式标注 FullCycleTesting / FrontendTesting / VisualVerification / FineTuning 循环及收敛条件。
- **Stage 4 Agent 文档**：`validation_agents.py` 中为 `FullCycleTestingAgent` 与 `FineTuningAgent` 增强 class-level docstring，清晰描述它们在闭环中的职责与输入输出；`execute_stage_4` 文档与日志前缀同步更新为「Validation & iterative FineTuning loop」。
- **文档对齐**：`docs/ARCHITECTURE.md` 新增 Orchestrator ↔ Agent 调用关系 mermaid 图；`AGENTS_REF` 新增「Orchestrator ↔ Agent 调用关系（代码导航）」小节，标注每个 Agent 与 Orchestrator 包装方法的映射关系；`run_from_stage_2` 的 progress 回调文案细化为包含主要 Agent 名称的阶段描述，便于前端展示当前阶段/Agent。

---

## 2026-03-05 | agents, config, data-models, web Stage 4 验证循环与 FineTuning 多轮迭代

- **配置**：`config/settings.py` 新增 `max_stage4_rounds` 与 `stage4_quality_threshold`，控制 Stage 4 FineTuning 最大迭代轮数与视觉对齐阈值（alignment_score）。
- **Stage 4 Orchestrator**：`execute_stage_4` 重构为「FullCycleTesting → FrontendTesting（逻辑通过时） → VisualVerification → FineTuning」闭环循环，直到测试与视觉对齐都达标、FineTuning 不再修改代码或达到 `max_stage4_rounds` / `max_fix_attempts`。
- **FineTuningAgent**：改用可配置的 `stage4_quality_threshold` 判断是否需要视觉修复（替代硬编码 0.7），并沿用 `fix_attempts` 统计修复轮数。
- **文档**：更新 ARCHITECTURE 中 Stage 4 流程图、AGENTS_REF Stage 4 调用顺序说明、DATA_MODELS_REF 对 `ValidatedProject.fix_attempts` 的解释，以及 CLAUDE.md 环境变量列表；保证与实际实现一致。

---

## 2026-03-05 | agents, web 项目评估改进（高优先级）

- **Orchestrator**：删除重复的 `_save_artifact` 方法定义，仅保留一处
- **Web API**：`post_chat_stream` 中移除未使用的 `generate()` 死代码，仅保留 `generate_and_persist()` 以正确持久化流式回复
- **文档**：AGENTS_REF Stage 4 表格增加 CodeFixAgent、FrontendTestingAgent（输入/输出/关键方法），并补充「Stage 4 调用顺序与职责」说明（CodeFix 负责 run-fix 循环，FineTuning 负责按 TestResult/视觉的精细化修复）

---

## 2026-03-03 | agents, web, config, services, troubleshooting 全流程鲁棒性与稳定性优化

- **Orchestrator**：`run_from_stage_2` 与 `run()` 对齐，按 Stage 2/3/4 分别 try/except；阶段失败时写入 `context.json`（`partial_failure`、`failed_stage`）并抛出 `StageExecutionError`，保证部分产物落盘
- **API**：`project_id` 校验（`_validate_project_id`）拒绝 `..`、路径分隔符及非 `proj_[a-zA-Z0-9_-]+` 格式，非法返回 400；500 统一 JSON，`EXPOSE_ERROR_DETAILS` 时返回详情，服务端始终 `logger.exception`
- **配置**：`validate_startup_config_log_warnings(settings)` 校验 `projects_dir` 可写、主用 LLM API Key 存在，仅打 log 不阻塞启动；Web 启动时调用
- **TaskService**：`_persist_task` 失败时在 `_update`/`_complete` 中 log.warning、在 `_fail` 中 logger.exception 且不 re-raise；可选 `task_generation_retry_on_transient`，瞬时错误（LLMServiceError、超时、5xx）重试一次
- **前端**：`useStatus` 暴露 `statusError`；StatusBar 在 `status === 'failed'` 时展示错误摘要与「重试生成」按钮，点击调用 `triggerGeneration` 并重新轮询
- **文档**：TROUBLESHOOTING 新增「阶段部分失败与恢复」小节（context.json、产物、日志、恢复方式）；CHANGELOG

---

## 2026-03-03 | agents, services 合并 bench5 HF 提交（7d1baaa）

- **拉取**：`git pull origin bench5` 引入 `feat: enhance HF model search + add PaperToProject agent`
- **HF 增强**：HfModelService 增加 Inference 检查、相关性打分、多样性过滤；AlgorithmAnalysisAgent 使用 LLM 检测 ML 任务（_detect_ml_task）替代纯关键词；配置 hf_check_inference（默认 true）、enable_hf_model_search 默认开启
- **PaperToProjectAgent**：新增 `src/agents/stage1_requirements/paper_to_project_agent.py`，分析论文生成应用创意；CLI 新增 `from-paper` 命令（paper 路径、可选 --context、--generate）
- **冲突解决**：planning_agents.py 保留 LLM 检测 + run_hf 条件；hf_model_service.py 合并 min_downloads、_TASK_MAPPING、use_cache/LRU 缓存与增强的 search_and_fetch_docs
- **测试**：test_orchestrator_failures 改为期望 StageExecutionError
- **文档**：AGENTS_REF 增加 PaperToProjectAgent、AlgorithmAnalysisAgent HF 增强说明；CLAUDE.md 增加 from-paper 命令；CHANGELOG

---

## 2026-03-03 | agents, config, web 接口与鲁棒性优化

- **Stage 1 输入**：`run()` 入口校验 `user_requirement` 非空（strip 后），空则 `ValueError`；CLI/Web 在调用前 strip 并拒绝空字符串（400 或友好提示）
- **StageExecutionError**：Orchestrator 各 stage 的 except 中包装为 `StageExecutionError(message, stage=N, partial_context=context)` 并 `raise ... from e`，便于调用方按 stage 与 partial_context 定位
- **Adapter**：`engineering_plan_from_stage2` 入口增加 `requirements` 非空及 `tasks`/`algorithms` 类型校验（TypeError/ValueError）
- **Web 500**：500 响应统一为通用文案 "Internal server error"，`logger.exception(e)` 记录；配置 `expose_error_details=True` 时可在响应中返回 `str(e)` 便于调试
- **文档**：AGENTS_REF 阶段契约注明 Stage 1 要求 user_requirement 非空及 StageExecutionError；TROUBLESHOOTING 增加阶段失败与 500 说明；CHANGELOG

---

## 2026-03-03 | config, services API 设置与交互环节 Key 引导

- **三大 API 配置**：Settings 支持 `primary_llm_provider`（openai | anthropic | google）；新增 `anthropic_api_key`、`anthropic_base_url`、`anthropic_model`；`google_api_key`、`google_base_url`、`google_model`；`openai_api_key` 改为可选，校验时仅要求主用 provider 的 key 已配置
- **get_primary_llm_config(settings)**：返回 (api_key, base_url, model, vlm_model)；LLMService.from_settings 据此创建客户端
- **validate_settings(settings, require_llm_key=True)**：`require_llm_key=False` 时跳过主用 key 校验，供交互引导流程使用
- **load_settings_lenient()** / **clear_settings_cache()**：交互模式下先 lenient 加载，缺 key 时引导后再 get_settings()
- **CLI 交互引导**：`create -i` 时若主用 key 未配置，提示在 .env 中填写或选择“当前会话粘贴”；粘贴后写 os.environ 并清除缓存，再继续 pipeline
- **文档**：.env.example 增加 PRIMARY_LLM_PROVIDER 与三大 key 示例；CLAUDE.md、SERVICES_REF 补充主用 API 与 key 说明；CHANGELOG

---

## 2026-03-03 | agents, services, data-models, config Stage 2 模型发现与接入设计

- **ExternalModelSpec**：新增数据模型（capability_type, provider_name, docs_url, api_docs_summary, base_url_hint, auth_type, request_body_example, response_image_path, suggested_integration）；EngineeringPlan 增加 external_model_specs（可选）
- **WebSearchService**：新建 `src/services/web_search_service.py`，WebSearchProvider 接口、SerperSearchProvider 实现；工厂 get_web_search_provider(settings)；配置 enable_stage2_web_search、web_search_provider、web_search_api_key、web_search_num_results、web_search_timeout
- **ModelIntegrationPlanningAgent**：Stage 2 新 Agent，根据 requirements/tasks 推断外部能力（image_generation、tts 等）→ 联网搜索 API 文档 → LLM 产出 List[ExternalModelSpec]，写入 plan.external_model_specs；仅当 enable_stage2_web_search 且 API Key 配置时调用
- **Orchestrator**：execute_stage_2 在 BDD 合成后条件调用 ModelIntegrationPlanningAgent，将 external_model_specs 传入 engineering_plan_from_stage2
- **AssetGeneration**：当 plan 存在 capability_type=image_generation 的 external_model_spec 且含 base_url_hint 时，优先使用该 spec 配置 GenericHTTPImageProvider
- **文档**：AGENTS_REF（ModelIntegrationPlanningAgent、Stage 2 契约）、DATA_MODELS_REF（ExternalModelSpec、external_model_specs）、SERVICES_REF（WebSearchService、AssetGeneration plan 覆盖）、CLAUDE.md（ENABLE_STAGE2_WEB_SEARCH 等）、CHANGELOG

---

## 2026-03-03 | services, config, data-models 多模型接入与图生设计

- **ImageGenerationService**：新增 `src/services/image_generation_service.py`，抽象 `ImageGenerationProvider`（generate(prompt, size, n) -> List[bytes]）；实现 OpenAIImageProvider（DALL-E）、GenericHTTPImageProvider（任意 HTTP 图生 API）；工厂 `get_image_provider(settings)`，enable_image_generation=False 时返回 None
- **配置**：enable_image_generation、image_generation_provider（openai | generic_http）、image_generation_openai_model、image_generation_base_url、image_generation_api_key、image_generation_extra_headers、image_generation_response_image_path、image_generation_timeout
- **数据**：EngineeringPlan 增加可选 image_specs（List[ImageSpec]）；新增 ImageSpec（id, prompt, suggested_path, role）；ExecutionContext 增加 generated_image_paths（id → 路径字符串）
- **AssetGeneration**：`src/services/asset_generation.py`，run_asset_generation(context, settings) 根据 image_specs 或默认规则生成 hero/placeholder 图，写入 generated/static/images/，写回 context.generated_image_paths；Orchestrator Stage 3 在 CodeGen 前调用（仅当 enable_image_generation 时）
- **CodeGen**：前端任务 prompt 中注入 generated_image_paths，提示使用 /static/images/xxx.png
- **文档**：SERVICES_REF（ImageGeneration、AssetGeneration）、DATA_MODELS_REF（ImageSpec、image_specs、generated_image_paths）、CLAUDE.md 环境变量、CHANGELOG

---

## 2026-03-03 | agents, services, config Stage 2 多模态模型发现与接入设计扩展

- **Stage 2 能力类型**：扩展 `_EXTERNAL_CAPABILITY_KEYWORDS` 与 ExternalModelSpec.capability_type 语义，支持 `video_generation`、`ppt_generation`、`latex_generation`、`audio_tts`、`audio_music` 等多模态能力，用于发现视频/PPT/LaTeX/音频相关外部服务
- **ModelIntegrationPlanningAgent**：增加可选 LLM 能力推断（`enable_stage2_llm_capability_infer`），在关键词基础上用 LLM 辅助识别需要的外部能力，并对每种能力构造更丰富的搜索 query（偏向 2026 API 文档）
- **多模态服务抽象**：新增 `video_generation_service.py`、`ppt_generation_service.py`、`latex_generation_service.py`、`audio_generation_service.py`，分别定义 Video/Presentation/Latex/AudioGenerationProvider 及对应 GenericHTTP*Provider 与工厂函数（get_video_provider/get_ppt_provider/get_latex_provider/get_audio_provider）
- **配置**：config/settings.py 增加 `enable_video_generation` / `enable_ppt_generation` / `enable_latex_generation` / `enable_audio_generation` 及各自的 provider/base_url/api_key/timeout/extra_headers 配置；新增 `enable_stage2_llm_capability_infer`
- **文档**：DATA_MODELS_REF 补充 ExternalModelSpec 多模态 capability_type 示例；AGENTS_REF 扩展 ModelIntegrationPlanningAgent 行为说明（多模态能力 + LLM 推断）；SERVICES_REF 新增多模态生成服务章节；CLAUDE.md 环境变量增加多模态相关开关；CHANGELOG 记录

---

## 2026-03-03 | web, agents, data-models 全流程 UX 优化（规划/验证/时间线）

- **Stage 2 规划可视化/编辑**：TaskService 暴露 `get_plan` / `update_plan`（基于 artifacts/02_engineering_plan.json），新增 `GET/PATCH /api/projects/{id}/plan` 接口，前者返回完整 EngineeringPlan JSON，后者安全地允许更新任务的 name/description/priority/estimated_complexity 等字段，并通过 EngineeringPlan 校验
- **验证历史记录**：新增数据模型 ValidationRun（run_id, project_id, stage, status, started_at, finished_at, metrics, summary）；Orchestrator 在 Stage 4 完成后调用 `_record_validation_run` 将本次验证摘要附加到 artifacts/validation_runs.json，metrics 含 errors/warnings/logic_passed/visual_passed
- **验证 Dashboard API**：新增 `GET /api/projects/{id}/validation-runs` 与 `GET /api/projects/{id}/validation-runs/<run_id>`，分别返回项目的验证历史列表与单次验证详情，供后续前端仪表盘使用
- **项目时间线元数据**：TaskService 基于 artifacts 文件时间与 validation_runs.json 推导 `planning_completed_at`、`generation_completed_at`、`validation_last_run_at`，并在项目列表/详情 API 中一并返回，便于前端构建时间线视图
- **项目概览接口**：新增 `GET /api/projects/{id}/overview`，聚合项目当前状态、时间线、轻量的 plan_summary（任务数 + 架构备注截断）以及 latest_validation（最近一次 ValidationRun），作为仪表盘卡片的数据源
- **文档**：WEB_FLOW_REF 更新项目相关 REST API 表；DATA_MODELS_REF 增加 ValidationRun 描述；CHANGELOG 记录本次 UX 优化改动

---

## 2026-03-03 | agents, config, data-models Agent 接口连接与性能优化（更稳妥路径）

- **文档**：AGENTS_REF 增加 Stage Input/Output 契约表（各阶段进入/写回 context、阶段内显式传参、Stage 4 磁盘契约）
- **Stage 3 并行预取**：Orchestrator 中 CodeMemoryAgent.pre_execute 与 CodeMiningAgent.execute 可并行执行（ThreadPoolExecutor，max_workers=2），配置 `enable_parallel_stage3_prefetch`（默认 True）
- **Context 写回**：ExecutionContext 增加可选字段 `memory_context`、`mining_by_task`；Stage 3 预取后写入；每次 FullCycleTesting（含 CodeFix 后重测）后写回 `context.test_results`
- **CodeGen**：保持 `execute(context, mining_by_task=..., memory_context=...)` 签名；内部优先从 context 读取（getattr 兜底），参数兼容
- **FineTuning**：保持 `execute(context, test_result)` 签名，不改为仅 context
- 配置：config/settings.py 增加 enable_parallel_stage3_prefetch；CLAUDE.md 增加 ENABLE_PARALLEL_STAGE3_PREFETCH

---

- fixed 语义：各 _fix_* 返回 (CodeRepository, bool)，execute() 仅在实际修改时置 fixed=True
- 入口点：_fix_missing_entry_point 生成 app.py（与 FullCycleTesting 的 app.py/run.py 一致），不再生成 app/main.py
- 修复顺序：errors 按 SYNTAX → IMPORT → RUNTIME|LOGIC 分组处理
- _fix_test_error：上下文按 fine_tuning_max_context_chars 截断，error.file_path 规范化匹配 repository 路径
- _fix_visual_issues：同上截断，返回 (repository, changed)
- 配置：fine_tuning_max_context_chars（默认 12000）、use_fast_model_for_fine_tuning_syntax（默认 True，_fix_syntax_error 使用 fast_model_for_code_gen）
- create_validated_project 增加参数 fix_attempts；Orchestrator 在 FineTuning 返回 fixed 时传入 fix_rounds=1
- AGENTS_REF：FineTuningAgent 行为说明

---

## 2026-03-03 | agents, config, troubleshooting Full-cycle Testing Agent 设计优化

- 修复 _check_unused_files：删除重复 return，修正恒假条件（未使用 app/ 下非 app/static 文件现正确加入 warnings）
- 统一端口：_try_import_and_create_app 使用 validation_port（与 _try_run_with_subprocess 一致），子进程传入 PORT 环境变量
- 未使用文件仅作 warnings，可配置：warn_unused_files（默认 True）、bdd_test_timeout_seconds（默认 60）
- 语法错误时跳过启应用与 BDD 执行，设 env_install_success/env_start_success=False，仍写盘以便 CodeFix/RunAndFix 修复；未使用文件检查仍执行
- TROUBLESHOOTING：补充 "Could not verify run: '_check_can_run'" 历史 artifact 说明
- AGENTS_REF：FullCycleTestingAgent 行为说明（执行顺序、BDD 来源、未使用文件策略、配置）

---

## 2026-03-03 | agents, services Code Mining Agent 优化

- Service 复用：CodeMiningService 在 Agent 层创建一次，传入 _build_mining_context_for_task
- 并行预取：ThreadPoolExecutor 并行 mining，code_mining_parallel_workers（默认 3）
- 提前跳过：skip_mining_for_simple_tasks 时在预取前跳过 frontend/config-only 任务
- 查询去重：code_mining_deduplicate_queries（默认 True）按 query 去重，结果复用到多 task
- CodeMiningService 缓存分层：query 级 raw 缓存 + (content_hash, interface_spec) 级 adapt 缓存
- 限流退避：403 时 _get_with_retry 指数退避重试 1–2 次
- 配置：code_mining_parallel_workers、code_mining_max_context_chars、code_mining_deduplicate_queries

## 2026-03-03 | agents Code Memory Agent 优化

- 配置项：code_memory_prefetch_max_queries、code_memory_context_max_chars（config/settings.py）
- pre_execute 兜底：skeleton 播种、预取、服务初始化分别独立 try 块，失败不中断
- 并行预取：ThreadPoolExecutor 并行 search_snippets，替代串行
- CodeMemoryService：add_snippet docstring 补充 FTS5 同步逻辑说明

## 2026-03-03 | agents Code Generation Agent 优化

- 简单任务 Fast Model：frontend+low 或 static/templates/config-only 使用 gpt-4o-mini
- Prompt 截断：max_system_prompt_chars 限制 system prompt 长度
- 简单任务跳过 Mining：skip_mining_for_simple_tasks 时 frontend/config 任务不注入 mining_context
- Agent 失败兜底：_fallback_for_task 在 detect_pattern_with_score 达标时生成最小 stub（code_gen_templates）
- 语法修复：use_fast_model_for_syntax_fix、code_gen_syntax_fix_retries 可配置
- Prompt 模块化：code_gen_system_base.txt、code_gen_critical_rules.txt、code_gen_quality.txt

## 2026-03-03 | agents Scheme Planning Agent 优化

- 结构化兜底：LLM 失败时用 build_scheme_fallback 生成 task_files、api_specs、pyi_stubs（crud/dashboard/auth/readonly）
- 条件 API Review：skip_api_review_when_simple、use_fast_model_for_api_review
- flow 可选：skip_flow_in_scheme_planning
- pattern_hint 注入 scheme_planning prompt

## 2026-03-03 | agents Algorithm Analysis Agent 优化

- 类型感知兜底：_default_algorithm_for_task 按 backend/frontend/database 返回 Flask+SQLAlchemy / Jinja2
- data_structures、algorithm_type：AlgorithmEntry 与 Algorithm 支持，供 CodeGen algo_extras 使用
- 富 tasks_summary：T1 [backend]: name - description...
- HF 并行检索：ThreadPoolExecutor 并行 search_and_fetch_docs
- 库推断：按 task type 补全 libraries
- 配置：skip_hf_for_simple_tasks、skip_flow_in_algorithm、enable_hf_cache
- HfModelService：可选 use_cache（LRU 32）

## 2026-03-03 | agents Task Division Agent 优化

- 合并 flow 提取：unified 模式下 flow_simulation 原始文本直接注入，移除单独 `_extract_structured_flow` LLM 调用
- 结构化兜底：LLM 失败时基于 crud/dashboard/auth/readonly 模板生成最小任务列表
- DAG 校验：`_validate_dag` 修正无效依赖、检测循环、拓扑排序
- 模板扩展：新增 auth、readonly 模式及 `detect_pattern_with_score`
- 条件 Review：skip_task_review_when_count_low、force_task_review_when_count_high、force_task_review_dep_depth、auth 关键词触发
- 配置：skip_flow_extraction、use_fast_model_for_task_review、fast_model_for_review
- task_division_unified.txt 增强 JSON Schema 约束

## 2026-03-02 | agents Interaction Agent 优化

- 提取所有提示词至 config/prompts/（interaction_*.txt, requirement_analysis.txt）
- 接入 PromptLoader，与 planning_agents 模式一致
- merge_requirements 增加 design_mode 支持：用户提 UI 风格时正确更新
- execute() 增加 design_mode 提取；ExtractedRequirements 新增 design_mode 字段
- 删除 requirement_analysis_prompt.py，模板迁移至 config/prompts/
- 新增 test_merge_requirements_preserves_design_mode、test_merge_requirements_updates_design_mode_from_user_request
- 更新 PROMPTS_REF、AGENTS_REF

## 2026-03-02 | other Skill 集成与项目优化

- CONTEXT_INDEX、project-context 增加 Skill 触发表与建议
- 新建 idea2product-dev skill（SKILL.md + references/）
- 新建 config/prompts/frontend_design_guidelines.txt，CodeGenerationAgent 前端任务注入
- CODE_GEN_SPEC 增加 theme-factory 映射表
- TROUBLESHOOTING 增加 webapp-testing 引用
- doc-sync 增加 doc-coauthoring 说明
- AGENTS.md 注册 idea2product-dev skill

## 2026-03-02 | other 文档优化

- 新增 docs/TROUBLESHOOTING.md、docs/refs/SERVICES_REF.md
- 新增 scripts/check_docs.py — 校验 AGENTS_REF 与 src/agents 一致性
- 扩展 CONTEXT_INDEX：完整清单、按任务找文档、SERVICES/TROUBLESHOOTING 引用
- 更新 doc-sync、project-context 规则，覆盖 services、utils、config、troubleshooting
- 各 ref 文档末尾新增 See also 交叉引用
- CHANGELOG 新增 scope：services、utils、config、troubleshooting

## 2026-03-02 | other 初始化上下文文档体系

- 新增 docs/CONTEXT_INDEX.md、docs/refs/*、docs/specs/CODE_GEN_SPEC.md
- 新增 .cursor/rules/*.mdc（project-context、doc-sync、core-pipeline、agents、web-layer、code-generation）
- 精简 CLAUDE.md，增加 CONTEXT_INDEX 链接

## 2026-03-03 | code-gen, agents, config, troubleshooting Stage 3 代码正确性优化（Skeleton + Prompt + 检查）

- **Skeleton 质量校验**：在 `skeleton_builder.build_skeleton_from_pyi_stubs` 之上新增 `validate_skeleton`，对依赖图节点/边、entry_point 等做轻量检查，并在日志中输出 warning，供 Stage 3 提前发现明显结构问题。
- **Prompt 强化正确性规则**：更新 `config/prompts/code_gen_critical_rules.txt` 与 `code_gen_quality.txt`，强调接口/类型约束、禁止臆造模块、优先使用安全占位实现，以及「正确性 > 清晰性 > 性能」的优先级原则。
- **Stage 3 检查开关**：在 `config/settings.py` 中新增 `enable_stage3_syntax_check` 与 `enable_stage3_import_sanity_check`，并在 `CodeGenerationAgent` 中按配置控制语法检查与内部导入健全性检查（扫描 `app.*` 模块引用是否对应生成模块）。
- **Agent 文档与排错说明**：更新 `AGENTS_REF` 中 CodeGenerationAgent 小节以反映新的正确性检查行为；在 `CLAUDE.md` 环境变量列表中增加 Stage 3 检查相关开关；在 `docs/TROUBLESHOOTING.md` 中新增「Stage 3 常见错误与预防」表，覆盖 SyntaxError 爆发、内部模块导入错误与 Skeleton 异常等场景。

## 2026-03-03 | other 设计优化全流程文档

- 新增 `docs/OPTIMIZATION_FLOW.md`，给出面向 4 阶段流水线的统一设计优化循环（问题发现→现状建模→指标设计→方案与优先级→实验→实施→验证与回滚）
- 在 `docs/DEVELOPMENT_PLAN.md` 中增加指向 OPTIMIZATION_FLOW 的说明，约定后续优化专题可复用该流程与模板

---

## 2026-03-05 | code-gen, prompts Skeleton Screen 加载规范与 Stage 2 规划增强

- 在 `docs/specs/CODE_GEN_SPEC.md` 中新增「Loading 状态与 Skeleton 设计」章节，明确长耗时场景下优先使用 Skeleton Screen（浅灰骨架 + shimmer，支持 `prefers-reduced-motion`）承载加载状态，并给出列表页、详情页、Dashboard、代码浏览器等典型骨架布局建议。
- 更新 `config/prompts/scheme_planning.txt`：在 ui_design_spec 约束中要求对存在明显等待的页面优先规划 skeleton 式 loading_state，并将示例 JSON 中 `/` 路由的 loading_state 改为带有 skeleton_layout 描述的 skeleton 方案，同时在 IMPORTANT 段强调「有明显等待的页面应优先使用结构化 skeleton 布局而非 generic spinner」。

---

## 2026-03-05 | code-gen, prompts, web Aurora Parallax 背景规范与 Stage 2 规划支持

- 在 `config/prompts/frontend_design_guidelines.txt` 中新增「Parallax background for hero/workspace sections」小节，约定在工作台、Dashboard 或 hero 区域使用视差 aurora/背景时，背景滚动速度约为前景的 50%（0.3–0.6 区间），并必须尊重 `prefers-reduced-motion`，以独立背景容器形式实现且不影响前景可读性。
- 在 `docs/specs/CODE_GEN_SPEC.md` 的 Loading/Skeleton 章节末尾补充说明：当 Stage 2 在 `ui_design_spec` 中给出 aurora_parallax + parallax_speed 提示时，Stage 3 应将视差背景实现为独立背景层，使用滚动驱动 transform 实现约 50% 速度，并同样遵守运动偏好设置。
- 更新 `config/prompts/scheme_planning.txt`：在 ui_design_spec 规则中加入对 modern/dashboard 应用可选的 aurora/parallax 背景 hint，并在示例 JSON 中为 `/` 路由增加 `background: {\"type\": \"aurora_parallax\", \"parallax_speed\": 0.5}` 字段，作为 Stage 2 规划时参考的前端背景模式。

---

## 2026-03-05 | code-gen, prompts, other Reveal on Scroll 微交互规范与 Stage 2 规划支持

- 在 `config/prompts/frontend_design_guidelines.txt` 中新增「Reveal on Scroll micro-interactions」小节，说明在卡片列表、section 化内容等场景下应使用小幅上浮 + 淡入、仅首次触发的 subtle 滚动进场动画，并明确必须遵守 `prefers-reduced-motion`（在 reduced 模式下降级为无动画或静态过渡）。
- 在 `config/prompts/scheme_planning.txt` 中扩展 ui_design_spec 规则与示例 JSON：允许 Stage 2 在具有明显分区 / 卡片列表 / section 化内容的页面中，用自然语言 hint 推荐使用 subtle 的 reveal-on-scroll 动效（示例中为 `/` 路由的 `task-list` section 补充描述），并要求提示尊重运动偏好设置。
- 在 `docs/specs/CODE_GEN_SPEC.md` 的 Loading/Skeleton 章节中挂钩 Reveal on Scroll 指南：当 Stage 2 在 `ui_design_spec` 中明确提到 “reveal on scroll” 之类的动效时，Stage 3 在实现时应优先采用 IntersectionObserver 等机制，实现小幅上浮 + 淡入、每个元素仅首次进入视口触发的 subtle 动画，并强制遵守 `prefers-reduced-motion`。

---

## 2026-03-05 | code-gen, prompts, other Hover Micro-interactions 规范与 Stage 2 规划支持

- 在 `config/prompts/frontend_design_guidelines.txt` 中新增「Micro-interactions for interactive elements」小节，推荐为按钮、Tab、Chip、可点击卡片等交互元素设计轻微的 hover 微交互（小幅 scale + 阴影加深），给出 scale 因子与时长约束，并要求在 `prefers-reduced-motion` 模式下降级为无缩放动画，仅保留颜色/边框反馈。
- 在 `config/prompts/scheme_planning.txt` 中扩展 ui_design_spec 规则与示例 JSON：鼓励 Stage 2 在 `ui_guidelines.layout_hints` 或 `ui_design_spec.product_grade_rules` 中用自然语言说明主要可点击元素使用统一的 hover micro-interactions，并在 `/` 路由示例中补充「主按钮、Tab 与可点击卡片在 hover 时使用统一的微交互（轻微 scale + 阴影加深），在 prefers-reduced-motion 模式下关闭 scale 动画」等提示。
- 在 `docs/specs/CODE_GEN_SPEC.md` 中新增「Hover Micro-interactions」章节，约定当 Stage 2 在 `ui_design_spec` 中提到 hover 微交互时，Stage 3 应通过共享 CSS 工具类（而非散落内联样式）统一实现 scale+shadow 效果，并严格遵守 `prefers-reduced-motion` 约束，确保前端代码在交互和可访问性之间取得平衡。

## 2026-03-05 | code-gen, prompts, troubleshooting 将平滑转场上升为 Vue Web 生成规范

- 在 `docs/specs/CODE_GEN_SPEC.md` 中新增「Page & Stage Transitions（页面与阶段平滑转场）」章节，约定 Vue Web 应用在路由级页面、主视图 tab（如 Plan/Code/Preview）以及状态栏 Stage 文案更新时，应优先使用 `<Transition>` + CSS（`page-transition`、`tab-fade`、`stage-fade` 等）实现短时淡入+轻微位移的平滑转场，并在 `prefers-reduced-motion` 下关闭 transition/transform；同时将这些结构规划为未来 Vue 脚手架/骨架中的可复用模版片段。
- 在 `docs/refs/PROMPTS_REF.md` 中补充「Stage 2/Stage 3 中与平滑转场相关的 prompts 规划」小节，明确 SchemePlanning/FlowSimulation 的 prompt 应在 `architecture_notes` 或 `ui_design_spec` 中用自然语言标注页面/Stage 转场风格，而 CodeGeneration 相关 prompts（尤其是 `frontend_design_guidelines.txt` 与 `code_gen_system_base.txt`）应在 Vue 前端场景下要求使用上述转场模式并遵守运动偏好设置。
- 在 `docs/TROUBLESHOOTING.md` 中新增「前端转场（Page & Stage Transitions）相关问题」小节，给出路由切换闪白、主视图瞬间跳变、Stage 文案生硬更新以及 reduced-motion 下仍存在明显位移动画等常见现象的排查清单（检查根组件/工作台 Shell/状态栏是否使用规范的 `<Transition>` 结构与 CSS，并确保存在对应的 `@media (prefers-reduced-motion: reduce)` 降级规则）。

## 2026-03-05 | data-models 为 Stage 2/3 增加杂志式布局偏好

- Requirements 增加 layout_preferences，用于记录用户/Stage 1 对布局 archetype（如 editorial_magazine）的偏好。
- EngineeringPlan 增加 ui_guidelines，用于 Stage 2 写入全局/分页面布局风格（含 editorial_magazine），供 Stage 3/4 消费。

## 2026-03-05 | data-models, agents, prompts, code-gen Hero Split Layout Archetype（split_hero_left_text_right_preview）

- **数据模型**：在 `src/core/data_models.py` 中细化 `Requirements.layout_preferences` 与 `EngineeringPlan.ui_guidelines` 的描述，明确支持通过 `ui_guidelines.hero_layouts[route]` 为路由标记分屏 Hero 布局（`layout_archetype: "split_hero_left_text_right_preview"`、`primary_column`、`contrast_mode`、`notes` 等），并在 `DATA_MODELS_REF` 中补充 hero_layouts 的字段语义。
- **Stage 2 SchemePlanningAgent**：更新 `SchemePlanningAgent.execute` 的 prompt 逻辑（`scheme_planning.txt` + planning_agents.py），当需求中存在 Landing/Homepage/入口 Hero 语义或 layout_preferences 显式包含 `split_hero_left_text_right_preview` 时，引导 LLM 在 `engineering_plan.ui_guidelines.hero_layouts` 中为首页（通常 `/` 或 `/overview`）写入分屏 Hero 布局标记。
- **Stage 3 CodeGenerationAgent**：在 `code_generation_agents.py` 中从 `plan.api_specs.ui_guidelines.hero_layouts` 读取 hero 布局，并在 system prompt 的「UI Guidelines」下追加「Hero Layouts (per route)」说明，要求在标记为 `split_hero_left_text_right_preview` 的路由模板中实现左文案 / 右产品预览的分屏 Hero（左列主文案+CTA，右列预览卡片，比例约 3:2/5:4，遵守 contrast_mode）。
- **文档与映射**：更新 `AGENTS_REF` 中 SchemePlanningAgent 与 CodeGenerationAgent 的行为说明，`CODE_GEN_SPEC` 中新增 Split Hero 布局章节，`PROMPTS_REF` 标注 scheme_planning.txt 已支持 hero_layouts；整体让「左文案 / 右预览」首页结构从单个项目实现上升为可复用的 UI layout archetype。

## 2026-03-05 | code-gen, prompts Hero Gradient + Noise Background（aurora_parallax_with_noise）

- **Prompts**：在 `config/prompts/scheme_planning.txt` 中扩展 ui_guidelines/ui_design_spec 示例，为首页 `/` 的 `background` 增加 `type: "aurora_parallax_with_noise"`、`parallax_speed` 与 `noise_opacity` 字段，并在规则说明中约定噪点纹理应细腻、低不透明度且不影响文字可读性；在 `frontend_design_guidelines.txt` 中新增「Gradient + Noise backgrounds」小节，详细约束渐变+噪点背景的实现方式（渐变为基底，噪点通过伪元素/覆盖层叠加，透明度约 0.04–0.08，避免可见平铺与对比度下降）。
- **Agents**：更新 `SchemePlanningAgent`（`planning_agents.py`），在 Hero 布局 hint 中补充当首页 Hero 需要 aurora + noise 时可选择 `aurora_parallax_with_noise` 并写出 `noise_opacity`；更新 `CodeGenerationAgent`（`code_generation_agents.py`），在构建 UI Design Spec context 时读取 `page_layouts[route].background`，当 `type == "aurora_parallax_with_noise"` 时向 system prompt 注入「渐变基底 + 细腻噪点覆盖层」的实现提示与约束。
- **文档**：在 `CODE_GEN_SPEC.md` 中新增「Gradient + Noise Hero 背景（aurora_parallax_with_noise）」小节，说明 Stage 2/3 如何通过 `ui_design_spec.page_layouts[route].background` 约定/消费渐变+噪点 Hero 背景；在 `PROMPTS_REF.md` 标注 `scheme_planning.txt` 与 `frontend_design_guidelines.txt` 现在也负责该背景 archetype 的规划与实现规范。

---

## 2026-03-05 | agents, web 全流程健康检查修复（Stage 3 & 前端构建）

- **Stage 3 CodeGenerationAgent**：修复 `_process_task_with_tools` 中对 `skeleton_warnings` 的 NameError，将 skeleton 校验产生的 warning 以参数形式传入并注入 modular prompts/system prompt，避免 Stage 3 在首个任务上直接抛出 `StageExecutionError`。
- **CodeGenerationAgent 兼容 generated_image_paths**：在 `_process_task_with_tools` 中对 `context.generated_image_paths` 的访问增加容错封装，保证在未启用图片生成（或缺少该字段）时不会因 NameError 中断整段任务流程，而是降级为无图片提示继续生成代码。
- **前端构建占位资源**：在 Vue 前端的 `directionVisuals` 中将缺失的 hero/directions 占位图片统一指向现有的 `vue.svg`，保证 `npm run build` 在没有专门插画资源的情况下也能成功通过 Rollup 资源解析。

## 2026-03-12 | [agents] Stage 3/4 路径安全与 Stage 2 回退鲁棒性修复

- 为 Stage 3 工具读写与 Stage 4 落盘增加路径越界防护，阻断绝对路径/`..` 穿越写入。
- Stage 2 fallback 在低置信度时改为最小可执行任务集，避免空任务级联导致 Stage 3 失败。

## 2026-03-12 | [web] 聊天幂等、预览异步状态与 SSE/API 一致性修复

- chat/chat-stream 新增 `client_message_id` 幂等去重，避免流式降级重试导致重复用户消息。
- preview-url 增加 `state/starting/installing/preview_error`，并改为异步触发预览启动，降低接口阻塞风险。
- 移除重复 `/generate` 路由；统一 chat-stream 非法 JSON 错误语义；`/events` 对不存在项目返回 404。

## 2026-03-12 | [config] Settings 初始化并发安全修复

- 移除 `Settings.__init__` 对全局环境变量的临时删改，避免并发场景的进程级副作用。

## 2026-03-12 | [other] CI 门禁与 API 测试覆盖增强

- CI 开启覆盖率阈值并收紧 mypy 失败门禁，新增 docs 一致性检查步骤。
- 扩展 `tests/test_projects_api.py`，覆盖 chat-stream JSON 错误、幂等消息、generate 回包、events 404、plan/validation-runs/overview/clarification 端点等场景。
