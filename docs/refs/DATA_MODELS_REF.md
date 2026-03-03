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
- **Requirements**: title, description, features (List[Feature]), constraints, target_users, data_requirements, user_clarifications, design_mode
- **Feature**: id, name, description, priority, user_story

### Stage 2
- **Task**: id, name, description, type (TaskType), dependencies, priority, estimated_complexity, files_to_add, files_to_modify
- **Algorithm**: task_id, algorithm_type, implementation_approach, libraries, data_structures
- **FileSpec**: path, purpose, dependencies, layer, related_tasks
- **ImageSpec**: id, prompt, suggested_path, role（可选；hero | placeholder | icon）
- **ExternalModelSpec**: capability_type, provider_name, docs_url, api_docs_summary, base_url_hint, auth_type, request_body_example, response_image_path, suggested_integration（Stage 2 联网搜索 + LLM 产出，供 Stage 3/4 可选使用；capability_type 示例：image_generation、tts、video_generation、ppt_generation、latex_generation、audio_tts、audio_music）
- **InterfaceSpec**: module_name, file_path, purpose, layer, exports, imports, database_access
- **EngineeringPlan**: tasks, algorithms, file_structure, interface_specs, dependencies, architecture_notes, api_specs, pyi_stubs, bdd_test_cases, image_specs（可选）, external_model_specs（可选）

### Stage 3
- **CodeSkeleton**: interfaces, dependency_graph, symbol_table
- **CodeFile**: path, content, language, purpose, dependencies
- **CodeRepository**: skeleton, files, structure, dependencies, readme_content

### Stage 4
- **TestResult**: logic_passed, bdd_test_cases, errors, visual_verification, execution_time
- **ValidationRun**: run_id, project_id, stage, status, started_at, finished_at, metrics（errors/warnings/logic_passed/visual_passed 等）, summary（可选，用于 Dashboard 简要说明）
- **ValidatedProject**: repository, test_results, is_deployable, deployment_instructions

## ExecutionContext（context.py）

- **generated_image_paths**：可选，Stage 3 AssetGeneration 写回，id → 路径字符串（如 static/images/hero.png），供 CodeGen 前端任务引用

## 枚举

- TaskType: FRONTEND, BACKEND, TESTING, DEPLOYMENT, DATABASE
- TaskComplexity: LOW, MEDIUM, HIGH
- ValidationStatus: NOT_STARTED, IN_PROGRESS, PASSED, FAILED, FIXED
- ErrorType: SYNTAX, RUNTIME, LOGIC, DEPENDENCY, TIMEOUT, IMPORT

## See also

- AGENTS_REF — 各 Agent 的输入输出模型
- ARCHITECTURE — 阶段与数据流图
