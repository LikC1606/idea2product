# Agent 参考

## Agent 设计规范（全局约定）

- **目录结构**：每个阶段的 Agent 均位于 `src/agents/stageX_*/` 目录下，文件命名建议为 `<stage>_<domain>_agents.py`（如 `validation_agents.py`、`code_generation_agents.py`）。
- **类命名**：类名统一以 `*Agent` 结尾，并在 docstring 中标注所处阶段（Stage 1–4）及主要职责。
- **构造函数**：所有 Agent 构造函数统一为 `__init__(self, llm_service: LLMService, settings: Settings | None = None, ...)` 的变体，至少接收一个 `LLMService` 实例；不继承基类。
- **主入口方法**：所有 Agent 的主执行方法为 `execute(...) -> <OutputModel | None>`，docstring 中必须包含 `Args` 与 `Returns` 说明；多入口方法（如 `run_interactive`）只用于 CLI / Web 特殊场景。
- **调用方式**：所有 Agent 仅通过 `Orchestrator` 调用，避免其他服务层直接调用 Agent；Orchestrator 负责注入 `ExecutionContext` 与 Settings。
- **日志前缀**：Agent 内部日志使用模块级 logger（`get_logger(__name__)`），关键日志建议包含 `[Agent:Name]` 字样；Orchestrator 日志使用 `[StageN][AgentName]` 风格标识当前运行的 Agent。

## Stage 1 - Requirements

| Agent | 文件 | 输入 | 输出 | 关键方法 |
|-------|------|------|------|----------|
| InteractionAgent | `src/agents/stage1_requirements/interaction_agent.py` | ExecutionContext, List[Dict] | Requirements | `execute()`, `run_interactive()`, `generate_clarification_questions()`, `generate_options_for_question()`（返回包含 `question`、`need_options` 与 `options[]` 的 ClarificationQuestion，用于 Web 澄清 chips），`reply_in_chat()`（对话助手，强制输出单句澄清问句且不包含示例）、`reply_in_chat_stream()`（同样返回已归一化的单句问句）、`conversation_to_requirements()`, `merge_requirements()` |
| PaperToProjectAgent | `src/agents/stage1_requirements/paper_to_project_agent.py` | 论文路径/文本, 可选 context | 应用创意/需求摘要 | 分析论文并生成可落地的应用创意；CLI `from-paper` 使用 |

- `InteractionAgent.generate_options_for_question()`：为 Web 澄清 chips 面板针对单个 assistant 问句生成 3–6 个选项；支持传入 `max_tokens`/`temperature` 控制成本与一致性；UI 侧另提供“其它/自定义”输入。

## Stage 2 - Planning

| Agent | 文件 | 输入 | 输出 | 关键方法 |
|-------|------|------|------|----------|
| FlowSimulationAgent | `src/agents/stage2_planning/planning_agents.py` | Requirements | str (flow_simulation) | `execute()` |
| TaskDivisionAgent | 同上 | Requirements, flow_simulation | List[Task] | `execute()`, `_fallback_tasks()`, `_validate_dag()`, `_should_run_review()` |
| AlgorithmAnalysisAgent | 同上 | List[Task], flow_simulation | Dict[str, Algorithm] | `execute()`, `_default_algorithm_for_task()` |
| SchemePlanningAgent | 同上 | Requirements, tasks, algorithms | (files, interface_specs, api_specs, pyi_stubs) | `execute()`, `_fallback_scheme()`, `_should_run_api_review()` |
| ModelIntegrationPlanningAgent | 同上 | Requirements, tasks, flow_simulation, settings | List[ExternalModelSpec] | `execute()` |

## Stage 3 - Code Generation

| Agent | 文件 | 输入 | 输出 | 关键方法 |
|-------|------|------|------|----------|
| CodeGenerationAgent | `src/agents/stage3_generation/code_generation_agents.py` | ExecutionContext | CodeRepository | `execute()`, `_should_use_fast_model()`, `_fallback_for_task()`, `_process_task_with_tools()` |
| CodeMemoryAgent | 同上 | ExecutionContext, CodeRepository | None (side-effect) | `pre_execute()`, `execute()` |
| CodeMiningAgent | 同上 | ExecutionContext | Dict[str, str] | `execute()` |

## Stage 3 编排（Orchestrator）

- **并行预取**：`enable_parallel_stage3_prefetch=True`（默认）时，CodeMemoryAgent.pre_execute 与 CodeMiningAgent.execute 在 ThreadPoolExecutor 中并行执行，再调用 CodeGenerationAgent。
- **Context 写回**：预取完成后写回 `context.memory_context`、`context.mining_by_task`；CodeGenerationAgent 保持 `execute(context, mining_by_task=..., memory_context=...)` 签名，内部优先从 context 读取（getattr 兜底）。

## CodeMiningAgent 行为说明

- **并行预取**：使用 ThreadPoolExecutor 并行获取各任务 mining context，`code_mining_parallel_workers`（默认 3）控制线程数
- **Service 复用**：CodeMiningService 在 Agent 层创建一次，共享给所有任务
- **提前跳过**：`skip_mining_for_simple_tasks=True` 时，frontend/config-only 任务在预取前直接跳过，不发起 API 调用
- **查询去重**：`code_mining_deduplicate_queries=True`（默认）时，相同 query 仅 mining 一次，结果复用到多个 task
- **配置**：`code_mining_max_context_chars`（默认 800）、`code_mining_parallel_workers`、`code_mining_deduplicate_queries`

## CodeMemoryAgent 行为说明

- **pre_execute**：生成前为 CodeGenerationAgent 预取相似代码片段。先播种 symbol_table（build_skeleton_from_pyi_stubs + add_symbols_from_skeleton），若 enable_cross_project_memory 则对 tasks[:5] 构建 queries 去重后并行 search_snippets（ThreadPoolExecutor）
- **配置**：`code_memory_prefetch_max_queries`（默认 3）、`code_memory_context_max_chars`（默认 2500）控制预取数量与 memory_context 截断
- **兜底**：skeleton 播种、预取、服务初始化分别独立 try/except，任一失败不中断整体流程，返回已有 memory_context 或空字符串
- **execute**：生成后遍历 repository.files，对 .py 调用 add_snippets_from_file（AST 解析、函数/类级存储到 code_snippets + FTS5 code_search）

## CodeGenerationAgent 行为说明

- **简单任务 Fast Model**：`use_fast_model_for_simple_code_tasks=True` 时，frontend+low 或仅 static/templates/config 任务使用 fast_model_for_code_gen（gpt-4o-mini）
- **Prompt 截断**：`max_system_prompt_chars` 限制 system prompt 长度，超出时截断
- **简单任务跳过 Mining**：`skip_mining_for_simple_tasks=True` 且 frontend/config-only 时，mining_context 置空
- **Agent 失败兜底**：`agent.invoke` 异常时，若 `detect_pattern_with_score` 达到阈值（crud/dashboard/auth/readonly），用 `generate_fallback_stub` 生成最小 stub
- **语法修复**：`use_fast_model_for_syntax_fix=True` 时 fix 轮使用 fast model；`code_gen_syntax_fix_retries` 可配置重试次数
- **Prompt 模块化**：system prompt 从 config/prompts/code_gen_system_base.txt、code_gen_critical_rules.txt、code_gen_quality.txt 加载
- **正确性检查**：Stage 3 内部集成轻量级 Python 语法检查与自动修复循环（可通过 `enable_stage3_syntax_check` 开关控制），并提供可选的内部导入健全性检查（`enable_stage3_import_sanity_check`，用于提前发现 `app.*` 模块引用与生成文件不匹配的问题）；Skeleton 构建后会进行基础校验并在日志中输出 warning，用于尽早暴露依赖图异常。

## Stage 4 - Validation

| Agent | 文件 | 输入 | 输出 | 关键方法 |
|-------|------|------|------|----------|
| FullCycleTestingAgent | `src/agents/stage4_validation/validation_agents.py` | ExecutionContext | TestResult | `execute()` |
| CodeFixAgent | 同上 | Path (generated 目录) | None（磁盘就地修改） | `execute(project_path)` |
| FrontendTestingAgent | 同上 | Path (generated), Optional[port] | List[TestError] | `execute(project_path, port)` |
| VisualVerificationAgent | 同上 | ExecutionContext | Dict (alignment_score, issues) | `execute()` |
| FineTuningAgent | 同上 | ExecutionContext, TestResult | (CodeRepository, bool) | `execute()` |

**Stage 4 调用顺序与职责**：Orchestrator 以 FullCycleTestingAgent 为入口，对代码库进行完整测试与 BDD 检查，然后在每轮中按「FullCycleTesting → FrontendTesting（逻辑通过时） → VisualVerification → FineTuning」的顺序形成闭环。在每一轮：

- FullCycleTestingAgent 负责落盘、语法检查、run 子进程、自检路由/鉴权、BDD 测试并产出 TestResult。
- FrontendTestingAgent 在 logic_passed 时运行，对前端代码中发现的 API 进行真实调用测试，追加 TestError。
- VisualVerificationAgent 根据设置决定是否运行，对 UI 截图或 HTML 结构做分析，写入 `test_result.visual_feedback` 与 `visual_verification`（alignment_score 等）。
- FineTuningAgent 在存在逻辑/导入/运行错误或视觉对齐度低于阈值（stage4_quality_threshold）时被调用，对 CodeRepository 做精细化修复；若实际修改了代码，则 Orchestrator 递增 fix_attempts 并重新进入下一轮 FullCycleTesting。

循环在以下情况停止：测试与视觉对齐都通过、FineTuningAgent 未再产生修改、达到 `max_stage4_rounds` 或 `max_fix_attempts`。

## Stage Input/Output 契约

各阶段进入时 context 必须满足的字段、阶段内显式传参、阶段结束时的写回约定。便于排查与扩展。

| 阶段 | 进入时 context 必须 | 阶段内显式传参 | 阶段结束时写回 context |
|------|---------------------|----------------|------------------------|
| Stage 1 | `user_requirement`（非空，run() 入口校验） | — | `context.requirements` |
| Stage 2 | `context.requirements` | flow_simulation, tasks, algorithms（Orchestrator 局部传递） | `context.engineering_plan`, `context.tasks`, `context.algorithms`；可选 `plan.external_model_specs`（ModelIntegrationPlanningAgent 产出） |
| Stage 3 | `context.requirements`, `context.engineering_plan` | memory_context, mining_by_task（由 Orchestrator 传入 CodeGen）；可选写回 `context.memory_context`, `context.mining_by_task` | `context.code_repository` |
| Stage 4 | `context.requirements`, `context.engineering_plan`, `context.code_repository` | test_result 传入 FineTuning；CodeFix/FrontendTesting 输入为磁盘 generated 目录 | 每次测试后可选写回 `context.test_results`；最终产出 ValidatedProject |

- **Stage 4 磁盘契约**：FullCycleTestingAgent 写盘后，CodeFixAgent、FrontendTestingAgent 的输入为「磁盘上的 generated 目录」；RunAndFix 回退路径使用 repository 内存 + 写盘。
- **可选步骤跳过**：skip_flow_extraction、skip_mining_for_simple_tasks、warn_unused_files 等配置控制阶段内可选步骤是否执行。
- **阶段失败异常**：Orchestrator 在各 stage 的 try/except 中将失败包装为 `StageExecutionError(message, stage=N, partial_context=context)` 并设置 `__cause__`；调用方可通过 `stage` 与 `partial_context`（或 artifact）定位失败阶段。参见 TROUBLESHOOTING。

## Orchestrator ↔ Agent 调用关系（代码导航）

- **Stage 1**：`Orchestrator.execute_stage_1` → `InteractionAgent.execute` / `run_interactive`（`src/agents/stage1_requirements/interaction_agent.py`）
- **Stage 2**：`Orchestrator.execute_stage_2` 依次调用：
  - `FlowSimulationAgent.execute`（用户操作流模拟）
  - `TaskDivisionAgent.execute`（任务拆分）
  - `AlgorithmAnalysisAgent.execute`（算法与实现策略）
  - `SchemePlanningAgent.execute`（文件结构与接口规格）
  - （可选）`ModelIntegrationPlanningAgent.execute`（外部模型/API 规划）
- **Stage 3**：`Orchestrator.execute_stage_3`：
  - Phase 1/2：`CodeMemoryAgent.pre_execute` + `CodeMiningAgent.execute`（可并行）预取 memory/m mining 上下文
  - Phase 3：`CodeGenerationAgent.execute`（主体代码生成）
  - Phase 4：`CodeMemoryAgent.execute`（最终 snippet 写入记忆库）
- **Stage 4**：`Orchestrator.execute_stage_4`：
  - 每轮循环调用 `FullCycleTestingAgent.execute` → （可选）`FrontendTestingAgent.execute` → （可选）`VisualVerificationAgent.execute` → `FineTuningAgent.execute`
  - Orchestrator 负责根据 `max_stage4_rounds` / `max_fix_attempts` / `stage4_quality_threshold` 等配置判断是否继续下一轮。

## FullCycleTestingAgent 行为说明

- **执行顺序**：BDD 来源（plan.bdd_test_cases 或 _rule_based_bdd_fallback）→ 落盘 _save_files → _generate_init_files → _run_syntax_check → 若无语法错误则：_try_run_with_subprocess（validation_port）→ _check_frontend_routes / _check_auth_flow → _check_unused_files（warnings）→ 若 enable_bdd_testing 则 _write_bdd_pytest_file + _run_tests；若有语法错误则跳过启应用与 BDD 执行，设 env_start_success=False，仍可做未使用文件检查。
- **BDD 来源**：Single source 为 Orchestrator._synthesize_bdd_tests 写入 plan.bdd_test_cases；仅当 plan 无 BDD 时使用 _rule_based_bdd_fallback。
- **未使用文件**：仅作为 warnings 上报（不加入 errors），仅检查 app/ 下非 app/static 的后端文件；可通过 warn_unused_files=False 关闭。
- **配置**：validation_port、enable_bdd_testing、warn_unused_files、bdd_test_timeout_seconds

## FineTuningAgent 行为说明

- **触发条件**：need_logic_fix = (test_result.errors 或 warnings 存在且 logic_passed=False)；need_visual_fix = (visual_feedback 存在且 alignment_score < 0.7)。仅当 need_logic_fix 或 need_visual_fix 时 Orchestrator 调用 execute。
- **修复类型与顺序**：errors 按 ErrorType 分组，按 SYNTAX → IMPORT → RUNTIME|LOGIC 顺序依次调用 _fix_syntax_error、_fix_import_error、_fix_test_error；warnings 中 “No app.py found”/“No main.py found”/“No entry point” 触发 _fix_missing_entry_point；need_visual_fix 时调用 _fix_visual_issues。
- **fixed 语义**：各 _fix_* 返回 (CodeRepository, changed)；execute() 仅在实际发生修改时将 fixed 置 True，避免无改动时触发重测。
- **入口点**：_fix_missing_entry_point 在缺少 app.py/run.py 时生成 app.py，与 FullCycleTesting 的 _try_run_with_subprocess 一致。
- **_fix_test_error / _fix_visual_issues**：送 LLM 的上下文按 fine_tuning_max_context_chars 截断；error.file_path 与 repository 路径规范化匹配（含单文件回退时的 path 解析）。
- **配置**：fine_tuning_max_context_chars（默认 12000）、use_fast_model_for_fine_tuning_syntax（默认 True，_fix_syntax_error 使用 fast_model_for_code_gen）。
- **fix_attempts**：Orchestrator 在 FineTuning 返回 fixed=True 时设 fix_rounds=1 并传入 create_validated_project，ValidatedProject.fix_attempts 供 Benchmark 使用。

## 通用约定

- Agents 为独立类，构造函数接收 `LLMService`，**不继承** AgentBase
- 所有 Agent 通过 `Orchestrator` 调用，ExecutionContext 贯穿各阶段
- 使用 `LLMService.from_settings(settings)` 创建 LLM 实例

## TaskDivisionAgent 行为说明

- **Unified 模式**（默认）：单次 LLM 调用生成 entities + pages + tasks；flow_simulation 原始文本直接注入 prompt，不再单独调用 extract_structured_flow
- **兜底**：LLM 失败或返回空时，若 detect_pattern_with_score 达到阈值（crud/dashboard/auth/readonly），用模板生成最小可用任务列表
- **DAG 校验**：`_validate_dag` 修正无效 dependency、检测循环、返回拓扑序
- **条件 Review**：任务数 ≤ skip_task_review_when_count_low 时跳过，但含 auth 关键词、依赖深度 > 2、任务数 > force_task_review_when_count_high 时强制 review
- **快速模型**：`use_fast_model_for_task_review=True` 时 ReviewAgent 使用 gpt-4o-mini

## AlgorithmAnalysisAgent 行为说明

- **富摘要**：tasks_summary 含 `T1 [backend]: name - description...`，便于 LLM 输出准确 approach
- **类型感知兜底**：LLM 失败时 `_default_algorithm_for_task` 按 TaskType 返回：backend/database→Flask+SQLAlchemy；frontend→Jinja2
- **库推断**：非 HF 任务按 type 推断 libraries（backend→flask,sqlalchemy；frontend→jinja2）
- **HF 增强**：用 LLM 检测 ML 任务（_detect_ml_task）替代纯关键词；search_and_fetch_docs 支持 check_inference、keywords 相关性打分、多样性过滤
- **输出**：AlgorithmEntry 支持 data_structures、algorithm_type；Algorithm 写入并供 CodeGen 使用
- **配置**：skip_hf_for_simple_tasks、skip_flow_in_algorithm、hf_check_inference、enable_hf_cache（HfModelService）

## SchemePlanningAgent 行为说明

- **结构化兜底**：LLM 失败时若 `detect_pattern_with_score` 达到阈值，用 `build_scheme_fallback` 生成 task_files、api_specs、pyi_stubs
- **条件 API Review**：`skip_api_review_when_simple` 时，endpoint 数 ≤ N 且无 auth 时跳过 review
- **快速模型**：`use_fast_model_for_api_review=True` 时 ReviewAgent 使用 gpt-4o-mini
- **flow 可选**：`skip_flow_in_scheme_planning=True` 时不注入 flow_section
- **pattern_hint**：检测到 crud/dashboard 时注入任务结构提示
- **布局偏好整合**：从 Requirements.design_mode 与 Requirements.layout_preferences（如 `editorial_magazine`、`split_hero_left_text_right_preview`）中提取设计/布局偏好，通过 scheme_planning prompt 的 design_mode_hint / layout hint 向 LLM 提示应在 ui_guidelines 中选择合适的 layout（如 bento_grid、masonry_grid、editorial_magazine），并在 `ui_guidelines.page_layouts` 中为 overview/report 等页面写入 layout_archetype 与 applicability_score。
- **Hero 布局标记**：当需求/路由描述中包含「landing / homepage / 入口页 / 产品介绍 / 选择生成方向 / hero」等关键词，或 Requirements.layout_preferences 中显式包含 `split_hero_left_text_right_preview` 时，SchemePlanningAgent 会在 `engineering_plan.ui_guidelines.hero_layouts` 中为相应路由（通常是 `/` 或 `/overview`）写入：
  - `hero_layouts[route] = {"layout_archetype": "split_hero_left_text_right_preview", "primary_column": "left", "contrast_mode": "dark_bg_light_text", "notes": "左列为标题、副标题、卖点+主/次按钮，右列为产品界面预览卡片"}`
  - 该结构作为 Stage 3 实现分屏 Hero 区块的高层约束，避免每次从零设计首页 Hero。

## ModelIntegrationPlanningAgent 行为说明

- **触发**：仅当 `enable_stage2_web_search=True` 且 `get_web_search_provider(settings)` 非空时由 Orchestrator 在 Stage 2（BDD 合成之后）调用
- **能力推断**：
  - 关键词：根据 requirements 与 tasks 的关键词推断所需外部能力，能力类型来自 `_EXTERNAL_CAPABILITY_KEYWORDS`（如 image_generation、tts、video_generation、ppt_generation、latex_generation、audio_tts、audio_music）
  - 可选 LLM：当 `enable_stage2_llm_capability_infer=True` 时，使用 LLM 进一步分析 requirements/tasks，补充/精炼能力列表
- **联网搜索**：对每种能力调用 WebSearchProvider.search 检索 API 文档（如 `"text to video API documentation 2026"`、`"generate pptx API"`、`"text to speech API"`），合并多条 query 结果
- **结构化产出**：LLM 将搜索结果整理为 List[ExternalModelSpec]（capability_type、provider_name、docs_url、base_url_hint、auth_type、request_body_example、response_image_path、suggested_integration 等），写入 plan.external_model_specs
- **Stage 3 可选使用**：AssetGeneration 在存在 capability_type=image_generation 的 external_model_spec 且含 base_url_hint 时，可优先采用该 spec 配置 GenericHTTPImageProvider；视频/PPT/LaTeX/音频能力可由后续 Video/PPT/Latex/AudioGenerationService 消费

## See also

- DATA_MODELS_REF — 输入输出类型（Requirements、Task、EngineeringPlan、CodeRepository）
- PROMPTS_REF — 各 Agent 对应的提示模板
