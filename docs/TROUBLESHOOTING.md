# 故障排查

问题 → 可能原因 → 解决步骤。遇报错时优先查阅本表。

## 运行失败时先看什么（3 步）

1. **确定失败位置**：打开 `data/projects/<project_id>/artifacts/context.json`，看 **partial_failure** 与 **failed_stage**（2/3/4）。若存在，则流水线在该阶段失败。
2. **看阶段产物与日志**：根据 failed_stage 查看同目录下 `01_requirements.json`、`02_engineering_plan.json`、`03_code_repository.json` 是否齐全；再查看 `data/projects/<project_id>/logs/` 中对应阶段的日志（如 Stage 2 规划、Stage 3 生成、Stage 4 测试）。
3. **API/预览**：若是 500，检查响应 JSON 是否含 **error_code**（如 `STAGE_3_FAILED`）、**failed_stage**，可据此提示「第 N 阶段失败」；若是预览空白或报错，调用 `GET /api/projects/<id>/preview-url` 查看 **state**、**preview_error**（依赖安装失败时会在此体现）。

**环境自检**：启动前可运行 `GET /api/health` 检查配置与目录；若返回 503 或 `checks.llm_key_set` 为 false，请检查 `.env` 中的 API Key。可选 `GET /api/health?check_llm=1` 探测 LLM 可达性（需设置 `HEALTH_CHECK_LLM=true`，会发起一次 API 调用）。

## API 错误

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| **401 Unauthorized** | API Key 无效或缺失 | 检查 `.env` 中的 `OPENAI_API_KEY`，确认已从 `.env.example` 复制并填入有效 key |
| **Rate limit exceeded** | 请求超限 | 换用限流更高的提供商，或增加重试间隔 |
| **Connection refused** | 端点不可达 | 确认 `OPENAI_BASE_URL` 正确且服务已启动；本地代理检查端口 |

## 生成问题

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| **Empty generated code** | 需求描述过于笼统 | 使用更具体的需求（如 "Build a todo app with add, delete, and complete"） |
| **Tests failing after generation** | 生成代码有缺陷 | 系统会尝试自动修复；查看 `data/projects/<id>/logs/` 日志，关注 Stage 4 FineTuning 多轮修复记录 |
| **Import errors in generated app** | 依赖未安装，或 FullCycleTesting 子进程错误地从主仓库导入模块（如 `config`） | 在生成应用目录执行 `pip install -r requirements.txt`；若错误堆栈指向仓库根目录（如 `.../idea2product/config/__init__.py`），说明 Stage 4 运行环境未优先使用 `data/projects/<id>/generated`，请确认已更新到使用隔离 PYTHONPATH（以 generated 目录为首位）的 FullCycleTesting 实现。 |
| **同一需求反复触发导致资源争用** | 生成请求缺少幂等去重（重复点击/网络重放） | 升级到包含 TaskService 输入指纹去重的版本；排查 `task_status.json` 与服务日志是否出现 “skip duplicate fingerprint” 关键字。 |
| **/generate 返回成功但没有实际执行** | 返回语义与实际 enqueue 状态未对齐，或触发了 dedupe/backpressure | 查看 `/generate` 响应中的 `status` 字段（`started`、`queued_rerun`、`deduped_*`、`rejected_backpressure`），按状态做重试或等待。 |

## 常见坑

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| `.env` 相关报错 | 未配置环境变量 | 确保 `.env` 存在且包含有效的 `OPENAI_API_KEY` |
| **Windows encoding errors** | 编码问题 | CLI 会自动处理 UTF-8；若仍报错，检查终端编码设置 |
| **data/ 目录过大** | 历史项目堆积 | 使用 `python -m src.cli list` 查看项目，手动删除不需要的 `data/projects/<id>` |
| **"Could not verify run: 'FullCycleTestingAgent' object has no attribute '_check_can_run'"** | 历史 artifact 中残留的旧校验信息 | 该错误来自已删除的代码路径，当前版本不再调用 `_check_can_run`。若在 `data/projects/.../artifacts/` 的 JSON 中看到此字符串，可忽略或清理对应 artifact |

## 复现失败检查项

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| **`ModuleNotFoundError: No module named 'src'`** | 包未以可编辑模式安装 | 在项目根目录执行 `pip install -e .` |
| **401 Unauthorized（复现时）** | 环境变量未生效 | 确认已复制 `.env.example` 为 `.env` 并设置有效 key |
| **Empty or minimal generated code** | 需求不够具体，或 Stage 3 LLM 任务在中途失败仅写入模板骨架 | 使用更明确的描述，避免过于宽泛的「Build an app」；若在 `artifacts/03_code_repository.json` 中看到只有框架文件（`app.py`、`config.py`、`templates/index.html` 等），可升级到启用了 `_ensure_minimum_files` 的版本，它会根据 `file_structure` + `pyi_stubs` 自动补齐最小可运行的模型/路由/模板骨架。 |
| **`pytest tests/` 失败** | 依赖或路径问题 | 在项目根目录执行 `pip install -r requirements.txt`；单元测试使用 mock，无需 API key |

## Stage 4（Validation & FineTuning）循环相关

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| Stage 4 日志中 FineTuning 只跑了一轮就停止，且仍有错误 | `max_stage4_rounds` 或 `max_fix_attempts` 过小，或 FineTuningAgent 在本轮未修改任何文件 | 检查 `config/settings.py` 或 `.env` 中 `MAX_STAGE4_ROUNDS`、`MAX_FIX_ATTEMPTS`；确认日志中是否出现 “FineTuningAgent did not apply any changes”，必要时放宽轮数或检查 TestError 是否足够明确。 |
| VisualVerification 一直提示 alignment_score 较低且 FineTuning 多轮仍未通过 | `stage4_quality_threshold` 过高，或前端 HTML/CSS 结构难以自动修复 | 适当降低 `STAGE4_QUALITY_THRESHOLD`（例如从 0.9 调整到 0.7），或手动查看 `data/projects/<id>/generated/` 中的前端文件，结合 VisualVerification 的 `missing_elements` 与 `issues` 做针对性修改。 |
| Stage 4 耗时明显增加 | max_stage4_rounds 配置过大，导致多轮 “测试 + 可视化 + FineTuning” 循环 | 在保证质量的前提下，将 `MAX_STAGE4_ROUNDS` 调整为 2～3；如只需基础运行性验证，可暂时降低或关闭 VisualVerification（`ENABLE_VISUAL_VERIFICATION=false`）。 |

**配置推荐**：`MAX_STAGE4_ROUNDS` 建议 2～3（过小易修不完，过大耗时长）；`MAX_FIX_ATTEMPTS` 建议 2；`ENABLE_STAGE3_IMPORT_SANITY_CHECK` 建议设为 `true`，可在生成阶段提前发现 `app.*` 等导入与文件不一致问题（若个别项目误报可临时关闭）。

## 阶段部分失败与恢复

当 Pipeline 某一阶段（Stage 2/3/4）失败时，Orchestrator 会写入部分产物并标记失败阶段，便于排查与恢复。

| 内容 | 说明 |
|------|------|
| **artifacts/context.json** | 失败后会写入或更新，其中 **partial_failure** 为 `true` 表示发生了阶段级失败，**failed_stage** 为失败阶段编号（2、3 或 4）。 |
| **阶段产物** | Stage 2 失败时已有 `01_requirements.json`；Stage 3 失败时另有 `02_engineering_plan.json`；Stage 4 失败时另有 `03_code_repository.json`。可根据 `failed_stage` 查看对应阶段产物是否已落盘。 |
| **日志** | Orchestrator 在每阶段 except 中会打 `logger.error(..., exc_info=True)`（如 "run_from_stage_2 Stage N failed for &lt;project_id&gt;"）；TaskService 在任务失败时会打 "Generation failed for &lt;project_id&gt;"，重试时会打 "Retrying generation for &lt;project_id&gt; after transient error"。 |
| **恢复方式** | 修正需求或配置（如 API Key、网络）后，在 Web 端点击「重试生成」或再次触发生成；新版本会优先读取 `artifacts/stage_state.json`，若 Stage 2/3 在相同输入签名下已成功则从最近成功阶段恢复。 |

## 阶段失败与 API 错误响应

| 现象 | 说明 | 解决步骤 |
|------|------|----------|
| **StageExecutionError** | 某阶段执行失败时 Orchestrator 抛出的异常 | 查看 `stage` 属性（1～4）和 `partial_context`（或 `data/projects/<id>/artifacts/context.json`）定位失败阶段；根据 `__cause__` 或日志排查具体原因 |
| **500 响应仅返回 "Internal server error"** | 生产态下 Web API 不向客户端返回详细错误内容 | 服务端会通过 `logger.exception` 记录完整异常；查服务端日志获取堆栈。当异常为阶段失败（StageExecutionError）时，响应 JSON 会包含 **error_code**（如 `STAGE_3_FAILED`）、**failed_stage**（2/3/4），便于前端展示「第 N 阶段失败」而不暴露详情。若需完整错误正文，可设置 `EXPOSE_ERROR_DETAILS=true`（仅用于调试）。 |
| **任务长时间不结束** | 任务未被取消或触发超时前仍在阶段执行 | 调用 `POST /api/projects/<id>/cancel` 发起取消；检查 status 的 `failure_info` 是否为 `GenerationTimeoutError` / `GenerationCancelledError`。 |

## Stage 3（CodeGeneration）常见错误与预防

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| 生成应用在 Stage 4 立刻报大量 **SyntaxError** | LLM 在单个任务中引入了多处 Python 语法错误 | Stage 3 已内置语法检查与自动修复循环；可检查 `data/projects/<id>/logs/` 中与 `CodeGenerationAgent` 相关的日志，确认是否已有多轮修复尝试。必要时可以暂时关闭 `ENABLE_STAGE3_SYNTAX_CHECK=false` 以缩短调试回合，但不推荐长期关闭。 |
| 运行时报 **ModuleNotFoundError: No module named 'app.xxx'** | 代码引用了不存在的内部模块，或路由/模型文件名与导入不一致 | 建议开启 Stage 3 导入健全性检查（`ENABLE_STAGE3_IMPORT_SANITY_CHECK=true`，见 CLAUDE.md）在生成阶段提前发现此类问题；同时检查生成项目中 `app/routes/*`、`app/models/*` 与导入语句是否一一对应。 |
| 特定任务一直 fallback 到最小 stub（功能缺失） | 接口信息不完整（pyi / interface_specs 不足）或 Skeleton 存在明显缺陷 | 检查 `EngineeringPlan` 中的 `pyi_stubs` 与 `interface_specs` 是否覆盖了该任务相关文件；查看日志中 Skeleton 校验的 warning（依赖图缺节点、entry_point 异常等），必要时先修复 Stage 2 规划输出再重跑。 |

## 前端转场（Page & Stage Transitions）相关问题

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| 路由切换时出现短暂白屏或内容瞬间闪切 | Vue 根组件未使用 `<Transition>` 包裹 `RouterView`，或缺失 `page-transition-*` CSS 类；前端模板未按规范生成转场结构 | 检查生成项目的根组件（通常为 `App.vue`），确认是否存在 `<Transition name="page-transition" mode="out-in"><RouterView /></Transition>` 结构；若不存在，可在后续模板/骨架优化中补齐，并参考 `docs/specs/CODE_GEN_SPEC.md` 中的「Page & Stage Transitions」章节；对于已生成的项目，可在不影响业务逻辑的前提下手工添加该结构与对应 CSS。 |
| 切换 Plan/Code/Preview 等主视图时内容瞬间跳变、缺少一致的动画 | 工作台/编辑器 Shell 组件未为右侧主 pane 使用 `tab-fade` 转场，或缺失相关 CSS | 检查类似 `WorkspaceShell` 的布局组件，确认是否使用 `<Transition name="tab-fade" mode="out-in">` 包裹 `plan` / `code` / `preview` pane；缺失时可参考本仓前端实现或 `CODE_GEN_SPEC` 中的推荐 archetype，在后续骨架/模板层统一补齐。 |
| 底部状态栏的 Stage 文案更新过于生硬或频繁闪烁 | 未使用 `stage-fade` 转场包裹阶段文案，或后端轮询过于频繁导致文案频繁跳动 | 检查状态栏组件（如 `StatusBar`）是否使用 `<Transition name="stage-fade" mode="out-in">` 包裹 `currentStage` 文案，并使用 `:key="currentStage"` 触发平滑过渡；如 Stage 变化过于频繁，可在 `useStatus` 或后台轮询层适度节流，仅对关键阶段切换触发文案更新。 |
| 用户开启「减少动态效果」（prefers-reduced-motion）后仍看到明显位移动画 | 未在 CSS 中为 `page-transition-*` / `tab-fade-*` / `stage-fade-*` 等类添加 `@media (prefers-reduced-motion: reduce)` 降级规则 | 检查前端样式表中是否存在 `@media (prefers-reduced-motion: reduce)`，并确认在该块内对上述类关闭 `transition` 与 `transform`；若缺少，请参考 `CODE_GEN_SPEC` 中的示例实现，在模板/骨架层统一补齐，以确保生成应用符合无障碍要求。 |

## 相关文档

- 代码生成规范：@docs/specs/CODE_GEN_SPEC.md
- Agent 输入输出：@docs/refs/AGENTS_REF.md

## 增强 UI 测试

需更细粒度 UI 测试时，可参考 webapp-testing 技能（Playwright + with_server.py）：
```bash
npx openskills read webapp-testing
```

## 2026-03-12 新增排障项（Web 可靠性）

| 现象 | 可能原因 | 解决步骤 |
|------|----------|----------|
| 聊天消息偶发重复（尤其在流式失败后） | 客户端重试/降级时重复提交同一用户消息 | 现在 `chat` / `chat/stream` 支持 `client_message_id` 幂等去重。检查前端是否为同一条消息复用同一 `client_message_id`。 |
| Preview 页长时间显示空白，但无明显报错 | 预览正在后台安装依赖或启动进程 | 调用 `/api/projects/<id>/preview-url` 查看 `state`（`starting/installing/running/error`）与 `preview_error` 字段；`installing` 状态下等待后台完成。 |
| Preview 的 state 为 error 且 preview_error 提示依赖安装失败 | 生成应用的 `pip install -r requirements.txt` 失败（超时、网络或依赖冲突） | 预览服务在依赖安装失败时会写入 `preview_error` 并将 state 置为 `error`。查看 `preview_error` 内容；在 `data/projects/<id>/generated/` 下手动执行 `pip install -r requirements.txt` 排查；修复生成项目的 requirements.txt 或环境后重试预览。 |
| 订阅 `/events` 一直无有效状态 | project_id 不存在或状态文件不可用 | 现已对不存在项目返回 404；先检查 project_id 是否有效，再检查 `artifacts/task_status.json` 是否存在。 |
