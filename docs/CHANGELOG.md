# Changelog

每次修改代码后，在此追加一条记录。格式：`## YYYY-MM-DD | [scope] 简要描述`

**scope 可选**：`agents` | `data-models` | `web` | `prompts` | `code-gen` | `services` | `utils` | `config` | `troubleshooting` | `other`

---

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
