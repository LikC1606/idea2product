# 代码生成规范

## Interface-First 流程

1. **pyi_stubs** — SchemePlanningAgent 输出 `.pyi` 占位；若为空，`skeleton_builder.generate_minimal_pyi_from_interface_specs` 补全
2. **CodeSkeleton** — `skeleton_builder.build_skeleton_from_pyi` 从 pyi 构建 interfaces + dependency_graph
3. **依赖顺序** — 按 dependency_graph 拓扑排序生成实现
4. **实现填充** — 每文件遵循接口约束，生成业务逻辑

## 关键文件

- `src/utils/skeleton_builder.py` — 构建 CodeSkeleton、解析 pyi
- `config/prompts/code_gen_*.txt` — CodeGenerationAgent 模块化提示（system_base, critical_rules, quality）
- `config/prompts/frontend_design_guidelines.txt` — 前端任务设计规范
- `templates/flask_base/` — 生成应用的模板基础
- `src/agents/stage3_generation/code_gen_templates.py` — Agent 失败兜底 stub 生成

## 禁止事项

- 不要绕过 skeleton_builder 直接修改 pyi 生成逻辑
- 生成实现时必须遵守 pyi 中定义的接口签名
- 跨文件调用时使用 symbol_table 提供的签名，不要臆造

## 输出

- 生成代码保存在 `data/projects/{id}/generated/`
- 包含 app.py、app/、config.py、templates/、requirements.txt

## theme 与 theme-factory 对应（可选扩展）

design_mode（modern/minimal/dashboard）可映射到 theme-factory 的 10 主题，供 ui_guidelines 产出更具体配色与字体：
- modern → Ocean Depths / Tech Innovation / Modern Minimalist
- minimal → Arctic Frost / Desert Rose
- dashboard → Golden Hour / Botanical Garden

详见 `npx openskills read theme-factory`。

## Code Generation 配置

- `use_fast_model_for_simple_code_tasks` — frontend+low 任务使用 fast model
- `fast_model_for_code_gen` — 默认 gpt-4o-mini
- `skip_mining_for_simple_tasks` — frontend/config-only 任务不注入 mining_context
- `max_system_prompt_chars` — system prompt 截断上限（默认 16000）
- `use_fast_model_for_syntax_fix` — 语法修复轮使用 fast model
- `code_gen_syntax_fix_retries` — 语法修复重试次数

## See also

- AGENTS_REF — SchemePlanningAgent、CodeGenerationAgent
- DATA_MODELS_REF — CodeSkeleton、CodeRepository、EngineeringPlan
