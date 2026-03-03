# 提示模板参考

来源：`config/prompts/`

## 文件与 Agent 映射

| 文件 | 用途 |
|------|------|
| interaction_extract.txt | InteractionAgent execute() — 从用户描述提取需求 |
| interaction_conversation.txt | InteractionAgent conversation_to_requirements() — 对话转需求 |
| interaction_merge.txt | InteractionAgent merge_requirements() — 增量合并需求（含 design_mode） |
| interaction_chat_system.txt | InteractionAgent reply_in_chat / reply_in_chat_stream — 聊天 system prompt |
| interaction_final_requirements.txt | InteractionAgent _generate_final_requirements() — 澄清后生成最终需求 |
| interaction_clarification_questions.txt | InteractionAgent generate_clarification_questions() — 生成澄清问题 |
| requirement_analysis.txt | InteractionAgent analyze_requirement() — 需求分析 |
| flow_simulation.txt | FlowSimulationAgent |
| extract_structured_flow.txt | 结构化流程提取（unified 模式下已合并：原始 flow 直接注入 task_division_unified） |
| extract_entities_and_pages.txt | 实体与页面提取 |
| task_division.txt | TaskDivisionAgent（旧） |
| task_division_unified.txt | TaskDivisionAgent（统一版，flow_section 接收原始用户操作流程文本） |
| review_tasks.txt | 任务审阅 |
| algorithm_analysis.txt | AlgorithmAnalysisAgent（富 tasks_summary、data_structures、algorithm_type） |
| scheme_planning.txt | SchemePlanningAgent（含 pattern_hint） |
| review_api_specs.txt | API 规范审阅 |
| bdd_synthesis.txt | BDD 测试用例合成 |
| frontend_design_guidelines.txt | CodeGenerationAgent 前端任务设计规范（注入 system prompt） |
| code_gen_system_base.txt | CodeGenerationAgent system prompt 基础（framework, pyi, skeleton, task） |
| code_gen_critical_rules.txt | CodeGenerationAgent critical 规则（API 字段、Session 认证、auth checklist） |
| code_gen_quality.txt | CodeGenerationAgent 质量与工具使用要求 |

## 修改约定

- 占位符使用 `$variable` 格式（string.Template），由 `PromptLoader.format()` 替换
- 输出为 JSON 时，在提示中明确要求 valid JSON，避免多余 markdown
- 修改后需更新本文档对应行，并追加 docs/CHANGELOG.md

## See also

- AGENTS_REF — 各提示对应的 Agent
