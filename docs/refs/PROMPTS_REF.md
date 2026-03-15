# 提示模板参考

来源：`config/prompts/`

## 文件与 Agent 映射

| 文件 | 用途 |
|------|------|
| interaction_extract.txt | InteractionAgent execute() — 从用户描述提取需求 |
| interaction_conversation.txt | InteractionAgent conversation_to_requirements() — 对话转需求 |
| interaction_merge.txt | InteractionAgent merge_requirements() — 增量合并需求（含 design_mode） |
| interaction_chat_system.txt | InteractionAgent reply_in_chat / reply_in_chat_stream — 聊天 system prompt（严格单问句、禁止示例回答与选项列举；选项由 Web API 结构化返回） |
| interaction_final_requirements.txt | InteractionAgent _generate_final_requirements() — 澄清后生成最终需求 |
| interaction_clarification_questions.txt | InteractionAgent generate_clarification_questions() — 生成澄清问题 |
| requirement_analysis.txt | InteractionAgent analyze_requirement() — 需求分析 |
| interaction_clarification_options_for_question.txt | InteractionAgent generate_options_for_question() — 针对单个澄清问句生成结构化选项 JSON（`{question, need_options, options[]}`），供 Web UI chips 使用 |
| flow_simulation.txt | FlowSimulationAgent |
| extract_structured_flow.txt | 结构化流程提取（unified 模式下已合并：原始 flow 直接注入 task_division_unified） |
| extract_entities_and_pages.txt | 实体与页面提取 |
| task_division.txt | TaskDivisionAgent（旧） |
| task_division_unified.txt | TaskDivisionAgent（统一版，flow_section 接收原始用户操作流程文本） |
| review_tasks.txt | 任务审阅 |
| algorithm_analysis.txt | AlgorithmAnalysisAgent（富 tasks_summary、data_structures、algorithm_type） |
| scheme_planning.txt | SchemePlanningAgent（含 pattern_hint、ui_guidelines 及 ui_design_spec 规则；支持为首页等路由在 `ui_guidelines.hero_layouts` 中写入 `split_hero_left_text_right_preview` 分屏 Hero 布局标记，并在 `ui_design_spec.page_layouts[route].background` 中为 hero/workspace 区域选择 `aurora_parallax` 或 `aurora_parallax_with_noise` 等背景类型） |
| review_api_specs.txt | API 规范审阅 |
| bdd_synthesis.txt | BDD 测试用例合成 |
| frontend_design_guidelines.txt | CodeGenerationAgent 前端任务设计规范（注入 system prompt；包含 Masonry/Bento Grid、Reveal on Scroll、Hover micro-interactions、Parallax background、Gradient + Noise 背景，以及在 Vue Web 应用中使用 `<Transition>` + CSS 定义的平滑页面/主视图转场等前端实现规则） |
| code_gen_system_base.txt | CodeGenerationAgent system prompt 基础（framework, pyi, skeleton, task） |
| code_gen_critical_rules.txt | CodeGenerationAgent critical 规则（API 字段、Session 认证、auth checklist） |
| code_gen_quality.txt | CodeGenerationAgent 质量与工具使用要求 |

## 修改约定

- 占位符使用 `$variable` 格式（string.Template），由 `PromptLoader.format()` 替换
- 输出为 JSON 时，在提示中明确要求 valid JSON，避免多余 markdown
- 修改后需更新本文档对应行，并追加 docs/CHANGELOG.md

### Stage 2/Stage 3 中与平滑转场相关的 prompts 规划

- **Stage 2 — SchemePlanning / FlowSimulation**：
  - 在 `scheme_planning.txt` 中，前端结构/交互规划应考虑页面与主视图的转场策略：
    - 对于 Vue Web 应用，鼓励在 `engineering_plan.architecture_notes` 或 `ui_design_spec` 中以自然语言标注：路由级页面切换、关键 tab/Stage 切换应使用「短时淡入 + 轻微位移、遵守 prefers-reduced-motion」的平滑转场。
    - 不强制修改数据模型结构（例如不必新增专门的 `ui_transitions` 字段），而是通过文本约定为 Stage 3 提供动效约束。
- **Stage 3 — CodeGeneration**：
  - `frontend_design_guidelines.txt` 与 `code_gen_system_base.txt` 应在 Vue 前端任务场景下明确要求：
    - 使用 `<Transition name="page-transition" mode="out-in">` 包裹 `RouterView`，使用 `page-transition-*` CSS 类实现页面淡入+轻微下滑。
    - 对主要 tab/视图（如 Plan/Code/Preview）使用 `tab-fade` 转场，对状态栏 Stage 文案使用 `stage-fade` 转场，并在 `@media (prefers-reduced-motion: reduce)` 下关闭 transform/transition。
  - 这些要求与 `docs/specs/CODE_GEN_SPEC.md` 中的「Page & Stage Transitions」章节保持一致，仅在 prompt 层做规范性描述，不直接约束具体实现文件路径。

### Stage 4 FineTuning 与 TestError 引用

- **TestError** 包含 `file_path`、`line_number`、`error_message`、`stack_trace`、`suggestion`。FullCycleTesting 在构造 TestError 时应尽量填入文件路径与行号，便于 FineTuning 定位。
- **修复时引用该位置**：FineTuningAgent 的 `_fix_syntax_error` / `_fix_import_error` / `_fix_test_error` 等在使用 LLM 修复时，应在 prompt 中显式传入 `error.file_path`、`error.line_number` 以及 `error.error_message`（必要时 `error.stack_trace` 片段），要求模型「仅修改上述文件与行附近代码」或「优先在该位置修复」，避免修偏。

## See also

- AGENTS_REF — 各提示对应的 Agent
