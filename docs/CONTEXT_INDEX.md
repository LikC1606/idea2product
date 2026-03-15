# 上下文索引

## 自引用指令

当遇到以下情况时，请使用 @ 引用对应文档以补充上下文：

| 场景 | 文档 |
|------|------|
| 需要 Agent 输入输出或阶段分工 | @docs/refs/AGENTS_REF.md |
| 需要数据模型字段或阶段映射 | @docs/refs/DATA_MODELS_REF.md |
| 需要代码生成规范或 Interface-first 细节 | @docs/specs/CODE_GEN_SPEC.md |
| 需要 Web API、Chat、Preview 流程 | @docs/refs/WEB_FLOW_REF.md |
| 需要修改或理解提示模板 | @docs/refs/PROMPTS_REF.md |
| 需要服务层 / 模型选择（LLM、CodeMemory、ModelRegistry 等） | @docs/refs/SERVICES_REF.md |
| 报错 / 调试 | @docs/TROUBLESHOOTING.md |

**若发现文件被压缩或信息不完整，优先按上表 @ 引用。**

## 按任务找文档（Task → Docs）

| 任务类型 | 优先阅读 | Skill 补充 |
|----------|----------|------------|
| 了解项目并排查运行/生成问题 | PROJECT_AND_ISSUES → TROUBLESHOOTING | — |
| 调试生成失败 / 运行报错 | TROUBLESHOOTING → CODE_GEN_SPEC → AGENTS_REF | — |
| 修改 Agent 行为或新增 Agent | AGENTS_REF → PROMPTS_REF → doc-sync | — |
| 修改数据流或模型 | DATA_MODELS_REF → ARCHITECTURE | — |
| 修改 Web/API/Chat | WEB_FLOW_REF | — |
| 修改 LLM 调用、模型选择 | SERVICES_REF | — |
| 跑基准 / 复现实验 | BENCHMARK、REPRODUCIBILITY | — |
| 了解整体规划 | DEVELOPMENT_PLAN、ARCHITECTURE | — |
| 生成应用前端美化、设计规范 | CODE_GEN_SPEC | `npx openskills read frontend-design` |
| 生成应用主题/风格 | scheme_planning、ui_guidelines | `npx openskills read theme-factory` |
| 增强 UI 测试、Playwright | TROUBLESHOOTING、validation | `npx openskills read webapp-testing` |
| 编写/修订项目文档 | doc-coauthoring | `npx openskills read doc-coauthoring` |

## 完整文档清单

| 文档 | 用途 |
|------|------|
| CLAUDE.md | 快速上手、命令、关键模式 |
| docs/ARCHITECTURE.md | 4 阶段 pipeline、数据流 |
| docs/refs/AGENTS_REF.md | Agent 清单、输入输出、关键方法 |
| docs/refs/DATA_MODELS_REF.md | Pydantic 模型、阶段映射 |
| docs/refs/WEB_FLOW_REF.md | REST API、chat/preview/task 服务 |
| docs/refs/PROMPTS_REF.md | 提示模板与 Agent 映射 |
| docs/refs/SERVICES_REF.md | LLMService、CodeMemory、ModelRegistry 等 |
| docs/specs/CODE_GEN_SPEC.md | Interface-first、生成约束 |
| docs/PROJECT_AND_ISSUES.md | 项目介绍与当前已知问题总结 |
| docs/TROUBLESHOOTING.md | 故障排查 |
| docs/BENCHMARK.md | 基准测试设计与运行 |
| docs/REPRODUCIBILITY.md | 复现环境与依赖 |
| docs/DEVELOPMENT_PLAN.md | 开发阶段、接口设计、完成情况 |

## 文档-领域映射

| 文档 | 覆盖领域 |
|------|----------|
| AGENTS_REF | Stage 1–4 所有 Agent、输入输出、关键方法 |
| DATA_MODELS_REF | Pydantic 模型、Requirements、Task、EngineeringPlan、CodeRepository、ValidatedProject |
| CODE_GEN_SPEC | Interface-first、pyi、skeleton、dependency graph、生成约束 |
| WEB_FLOW_REF | REST API、chat_service、preview_service、task_service |
| PROMPTS_REF | config/prompts 各文件对应 Agent、修改约定 |
| SERVICES_REF | LLMService、ModelRegistry、CodeMemory、CodeMining、HfModel |

## 推荐阅读顺序（新接手项目时）

**主流程：**
1. CLAUDE.md — 快速上手、命令、关键模式
2. docs/ARCHITECTURE.md — 4 阶段 pipeline、数据流
3. docs/refs/AGENTS_REF.md — Agent 清单
4. docs/refs/DATA_MODELS_REF.md — 数据模型
5. docs/refs/WEB_FLOW_REF.md — Web 层（若涉及 chat/preview）

**调试 / 复现 / 开发：**
- 报错排查 → docs/TROUBLESHOOTING.md
- 基准与复现 → docs/BENCHMARK.md、docs/REPRODUCIBILITY.md
- 开发规划 → docs/DEVELOPMENT_PLAN.md

## 修改记录

每次修改代码后，需同步更新对应 ref 文档并追加 docs/CHANGELOG.md。参见 doc-sync 规则。
