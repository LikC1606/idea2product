# 数据模型参考

来源：`src/core/data_models.py`

## 阶段与模型映射

| 阶段 | 输入模型 | 输出模型 |
|------|----------|----------|
| Stage 1 | user_requirement (str) | Requirements |
| Stage 2 | Requirements | EngineeringPlan |
| Stage 3 | EngineeringPlan, Requirements | CodeRepository |
| Stage 4 | CodeRepository | ValidatedProject |

## 核心模型

### Stage 1
- **Requirements**: title, description, features (List[Feature]), constraints, target_users, data_requirements, user_clarifications, design_mode, layout_preferences（可包含布局 archetype 名称，如 `editorial_magazine`、`split_hero_left_text_right_preview`，用于提示 Stage 2/3 在首页或入口页采用对应布局）
- **Feature**: id, name, description, priority, user_story

### Stage 2
- **Task**: id, name, description, type (TaskType), dependencies, priority, estimated_complexity, files_to_add, files_to_modify
- **Algorithm**: task_id, algorithm_type, implementation_approach, libraries, data_structures
- **FileSpec**: path, purpose, dependencies, layer, related_tasks
- **ImageSpec**: id, prompt, suggested_path, role（可选；hero | placeholder | icon）
- **ExternalModelSpec**: capability_type, provider_name, docs_url, api_docs_summary, base_url_hint, auth_type, request_body_example, response_image_path, suggested_integration（Stage 2 联网搜索 + LLM 产出，供 Stage 3/4 可选使用；capability_type 示例：image_generation、tts、video_generation、ppt_generation、latex_generation、audio_tts、audio_music）
- **InterfaceSpec**: module_name, file_path, purpose, layer, exports, imports, database_access
- **EngineeringPlan**: tasks, algorithms, file_structure, interface_specs, dependencies, architecture_notes, api_specs, pyi_stubs, bdd_test_cases, image_specs（可选）, external_model_specs（可选）, ui_guidelines（可选）, product_type（可选）, latex_specs / video_specs / audio_specs（按产品类型可选）

其中 `engineering_plan.ui_guidelines` 约定：

- `global_layout_style: str | null`：整体页面布局风格，如 `"editorial_magazine"`、`"dashboard"`、`"form_first"` 等。
- `page_layouts: Dict[str, Dict]`：按路由划分的页面布局提示，例如：
  - `"/overview": {"layout_archetype": "editorial_magazine", "applicability_score": 0.85, "notes": "Content-heavy overview page"}`。
- `hero_layouts: Dict[str, Dict]`（可选）：按路由划分的首屏 Hero 布局 archetype，支持将首页使用的「左文案 / 右产品预览」模式上升为可复用语义：
  - key：路由或页面标识（如 `"/"`, `"/overview"`）
  - value 字段约定：
    - `layout_archetype: str`：例如 `"split_hero_left_text_right_preview"`（左列为主文案与 CTA，右列为界面预览/产品卡片）
    - `primary_column: "left" | "right"`：主要信息/行动所在列
    - `contrast_mode: "dark_bg_light_text" | "light_bg_dark_text"`：首屏 Hero 的对比模式
    - `notes: str`：补充 Hero 结构要素说明（如大标题、副标题、卖点列表、主/次按钮、预览卡片类型与层级关系等）

Stage 2 的 SchemePlanningAgent 会根据 Requirements 与路由语义，在适合用分屏 Hero 的页面（如 `/` 入口页）为 `ui_guidelines.hero_layouts[route]` 写入 `split_hero_left_text_right_preview` 等标记，Stage 3 CodeGenerationAgent 在生成对应模板时消费这些标记以稳定首屏布局。

### Stage 3
- **CodeSkeleton**: interfaces, dependency_graph, symbol_table
- **CodeFile**: path, content, language, purpose, dependencies
- **CodeRepository**: skeleton, files, structure, dependencies, readme_content

### Stage 4
- **TestResult**: logic_passed, bdd_test_cases, errors, visual_verification, execution_time
- **ValidationRun**: run_id, project_id, stage, status, started_at, finished_at, metrics（errors/warnings/logic_passed/visual_passed 等）, summary（可选，用于 Dashboard 简要说明）
- **ValidatedProject**: repository, test_results, is_deployable, deployment_instructions, fix_attempts（FineTuning 修复迭代次数）

## ExecutionContext（context.py）

- **generated_image_paths**：可选，Stage 3 AssetGeneration 写回，id → 路径字符串（如 static/images/hero.png），供 CodeGen 前端任务引用

## 产品类型与多计划（Stage 2）

- **ProductType**（枚举）：WEB, PDF, VIDEO, AUDIO, APP；表示产出物类型。
- **Requirements.product_type**：可选，默认 WEB；用于 Stage 2 分支与模型路由。
- **EngineeringPlan** 扩展：product_type（可选）、latex_specs（PDF）、video_specs（视频）、audio_specs（音频）；web/app 仍用 file_structure、pyi_stubs 等。
- **ExecutionContext**（context.py）：可选字段 product_type、model_id（用户选择模型时覆盖 registry 路由）。

## 枚举

- TaskType: FRONTEND, BACKEND, TESTING, DEPLOYMENT, DATABASE
- TaskComplexity: LOW, MEDIUM, HIGH
- ValidationStatus: NOT_STARTED, IN_PROGRESS, PASSED, FAILED, FIXED
- ErrorType: SYNTAX, RUNTIME, LOGIC, DEPENDENCY, TIMEOUT, IMPORT
- ProductType: WEB, PDF, VIDEO, AUDIO, APP

## See also

- AGENTS_REF — 各 Agent 的输入输出模型
- ARCHITECTURE — 阶段与数据流图

## 2026-03-12 更新（Stage 1 契约对齐）

- Stage 1 的结构化提取响应（`ExtractedRequirements`）已明确补齐：
  - `layout_preferences: Optional[List[str]]`
  - `product_type: Optional[str]`（限定为 `web|pdf|video|audio|app`）
- InteractionAgent 在构建 `Requirements` 时会显式解析 `product_type` 到 `ProductType`，并与既有 `layout_preferences` 一起进入后续 Stage 2/3 流程，减少字段静默丢失风险。
