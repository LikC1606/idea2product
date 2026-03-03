# Changelog

每次修改代码后，在此追加一条记录。格式：`## YYYY-MM-DD | [scope] 简要描述`

**scope 可选**：`agents` | `data-models` | `web` | `prompts` | `code-gen` | `services` | `utils` | `config` | `troubleshooting` | `other`

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
