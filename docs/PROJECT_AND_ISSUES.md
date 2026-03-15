# 项目介绍与当前已知问题

本文档分两部分：**项目介绍**（是什么、怎么用、架构要点）与**当前遇到的问题**（运行失败、生成代码有 bug、达不到预期）及排查指引。读者可先了解项目，再对照「当前问题」做自查与排查。

---

## 第一部分：项目介绍

### 项目是什么

Idea2Product 将自然语言需求通过 **4 阶段 pipeline**（需求分析 → 规划 → 代码生成 → 验证）转化为可运行的 Web 应用。详见 [README.md](../README.md) 的 "What It Does" 与 [docs/ARCHITECTURE.md](ARCHITECTURE.md) 的 Pipeline Overview。

### 如何运行

- **CLI**：`python -m src.cli create "..."`、`create -i "..."`、`list`、`status <project_id>`
- **Web**：先 `cd frontend && npm run build && cd ..`，再 `python -m src.web.app`；开发时可用 `cd frontend && npm run dev`
- **前置**：`pip install -r requirements.txt`、`pip install -e .`，在 `.env` 中配置主用 LLM API Key（见 [CLAUDE.md](../CLAUDE.md)）

### 架构要点

- **4 阶段**：Requirements（Stage 1）→ Planning（Stage 2）→ Code Generation（Stage 3）→ Validation（Stage 4）
- 每阶段主要产物与关键 Agent 见 [docs/ARCHITECTURE.md](ARCHITECTURE.md) 的表格与流程图
- **生成产物**：`data/projects/<id>/generated/`；**中间产物**：`data/projects/<id>/artifacts/`（如 `01_requirements.json`、`02_engineering_plan.json`、`03_code_repository.json`、`context.json`、`task_status.json`）

延伸阅读：ARCHITECTURE、[CONTEXT_INDEX.md](CONTEXT_INDEX.md)、CLAUDE、[TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

---

## 第二部分：当前遇到的问题

### 一、运行总是失败

**现象与原因**

- **环境与流程**：API Key 缺失/无效、网络不可达、某阶段执行失败（`artifacts/context.json` 中 `partial_failure` / `failed_stage`）、`/generate` 返回成功但未真正执行（实为 deduped/backpressure）、预览长时间空白、500 无详情等
- **生成应用本身**：Stage 4 或本地运行时 PYTHONPATH 污染（误导入主仓库）、生成应用依赖未安装导致预览/运行失败

**排查要点**

- 查 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 中「API 错误」「生成问题」「Stage 4（Validation & FineTuning）循环相关」「阶段部分失败与恢复」
- 确认 `.env` 与主用 LLM 的 API Key；`/generate` 返回的 `status` 为 `deduped_*` 或 `rejected_backpressure` 时参见前端提示或 WEB_FLOW_REF
- 预览空白时调用 `GET /api/projects/<id>/preview-url` 查看 `state`（`installing`/`error`）与 `preview_error`；依赖安装失败时此处会返回错误信息
- 500 时若响应含 `error_code`、`failed_stage`，表示某阶段失败，可据此定位并查服务端日志

### 二、生成的代码有 bug / 无法运行

**现象**

- SyntaxError、ModuleNotFoundError（如 `app.xxx`）、Stage 4 测试失败、任务退化为最小 stub

**原因与现有机制**

- Stage 3 有语法检查与自动修复循环；可选导入健全性检查（`ENABLE_STAGE3_IMPORT_SANITY_CHECK`）
- Stage 4 子进程隔离、FineTuning 轮数（`MAX_STAGE4_ROUNDS`、`MAX_FIX_ATTEMPTS`）；Stage 2 规划不完整时易触发 fallback 或 stub

**排查要点**

- 查 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 中「生成问题」「Stage 3（CodeGeneration）常见错误与预防」「Stage 4（Validation & FineTuning）循环相关」
- 日志位置：`data/projects/<id>/logs/`；配置项：`MAX_STAGE4_ROUNDS`、`ENABLE_STAGE3_IMPORT_SANITY_CHECK`、`code_gen_syntax_fix_retries` 等（见 CLAUDE.md、TROUBLESHOOTING）
- 参考 [docs/specs/CODE_GEN_SPEC.md](specs/CODE_GEN_SPEC.md)、[docs/refs/AGENTS_REF.md](refs/AGENTS_REF.md)

### 三、生成的代码达不到预期

**现象与原因**

- 需求过于笼统、生成内容过少（Empty/minimal）：需求引导不足或 Stage 2 规划不完整
- 前端/视觉不符：Stage 2 的 ui_guidelines/hero_layouts 等与 Stage 3 实现不一致
- Stage 2 规划不完整、模型能力或配置不当

**可做调整**

- 写清需求，避免过于宽泛的「Build an app」；查看 `artifacts/01_requirements.json`、`02_engineering_plan.json` 是否充分
- 视觉要求可调 `STAGE4_QUALITY_THRESHOLD` 或暂时关闭 `ENABLE_VISUAL_VERIFICATION`；复杂应用可选用更强模型（model_id）
- 参考 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)、[CODE_GEN_SPEC](specs/CODE_GEN_SPEC.md)

### 四、推荐排查顺序

1. **区分失败发生位置**：是「流水线/本机环境」还是「生成应用运行」。
2. **流水线/环境**：  
   - 查看 `artifacts/context.json`（`partial_failure`、`failed_stage`）→ 确定失败阶段  
   - 查看 `artifacts/task_status.json` 与 `data/projects/<id>/logs/` 对应阶段日志  
   - 若为 500，检查响应中 `error_code`、`failed_stage`；必要时设置 `EXPOSE_ERROR_DETAILS=true` 查看详情（仅调试）
3. **生成应用有 bug/跑不起来**：  
   - 查看 `02_engineering_plan.json`、`03_code_repository.json` 是否完整  
   - 查看 logs 中 CodeGenerationAgent、FullCycleTesting、FineTuning 相关记录  
   - 调整 `MAX_STAGE4_ROUNDS`、`ENABLE_STAGE3_IMPORT_SANITY_CHECK` 等（见 TROUBLESHOOTING）
4. **达不到预期**：  
   - 检查 01/02 artifacts 与需求描述是否匹配  
   - 调整 `STAGE4_QUALITY_THRESHOLD` 或模型选择；必要时手动修改生成产物（注意勿直接改 `data/projects/**` 作为长期方案，见项目规则）

---

## 相关文档

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 故障排查详表
- [CONTEXT_INDEX.md](CONTEXT_INDEX.md) — 文档索引
- [docs/specs/CODE_GEN_SPEC.md](specs/CODE_GEN_SPEC.md) — 代码生成规范
- [docs/refs/AGENTS_REF.md](refs/AGENTS_REF.md) — Agent 输入输出
- [ARCHITECTURE.md](ARCHITECTURE.md) — 4 阶段架构
