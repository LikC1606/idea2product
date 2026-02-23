# Idea2Product 开发计划

## 项目目标
构建一个可用的 Web 应用，用户输入需求 → 系统生成产品

---

## 开发阶段总览

| Phase | 内容 |
|-------|------|
| Phase 1 | Agent 核心开发 (4 Stage) |
| Phase 2 | Web 后端开发 |
| Phase 3 | Web 前端开发 |
| Phase 4 | 集成测试 |

---

## Phase 1: Agent 核心开发

### 1.1 Stage 1 - Interaction Agent ✅ (已有基础)

**接口设计:**
```
输入: user_requirement (str)
   ↓
输出: Requirements (Pydantic Model)
   - title: str
   - description: str
   - features: List[Feature]
   - constraints: List[str]
   - target_users: str
   - data_requirements: str
   - user_clarifications: Dict[str, str]
```

**核心方法:**
- `analyze_requirement(requirement)` → 判断是否需要澄清
- `generate_clarification_questions(requirement)` → 生成澄清问题
- `run_interactive(requirement)` → 交互模式
- `execute(context)` → 非交互模式

---

### 1.2 Stage 2 - Planning Agents

#### 1.2.1 TaskDivisionAgent
```
输入: Requirements
输出: List[Task]

Task:
  - id: str (T1, T2...)
  - name: str
  - description: str
  - type: TaskType (FRONTEND/BACKEND/TESTING/DEPLOYMENT/DATABASE)
  - dependencies: List[str]  # 依赖的Task ID
  - priority: int  # 1-5
  - estimated_complexity: TaskComplexity (LOW/MEDIUM/HIGH)
```

**核心方法:**
- `execute(requirements)` → 调用 LLM 拆分任务

#### 1.2.2 AlgorithmAnalysisAgent
```
输入: List[Task]
输出: Dict[str, Algorithm]

Algorithm:
  - task_id: str
  - algorithm_type: str
  - implementation_approach: str
  - libraries: List[str]
  - data_structures: List[str]
  - notes: Optional[str]
```

**核心方法:**
- `execute(tasks)` → 分析每个任务的算法实现

#### 1.2.3 SchemePlanningAgent
```
输入: Requirements, List[Task]
输出: List[FileSpec]

FileSpec:
  - path: str
  - purpose: str
  - dependencies: List[str]
  - related_tasks: List[str]

最终组合输出: EngineeringPlan
  - tasks: List[Task]
  - algorithms: Dict[str, Algorithm]
  - file_structure: List[FileSpec]
  - dependencies: List[str]
  - architecture_notes: str
```

**核心方法:**
- `execute(requirements, tasks)` → 生成文件规格和工程方案

---

### 1.3 Stage 3 - Code Generation Agents

#### 1.3.1 CodeGenerationAgent (核心)
```
输入: ExecutionContext (含 EngineeringPlan)
输出: CodeRepository

CodeSkeleton:
  - interfaces: List[InterfaceDefinition]
  - dependency_graph: DependencyGraph
  - symbol_table: List[SymbolTableEntry]

CodeFile:
  - path: str
  - content: str
  - language: str
  - purpose: str
  - dependencies: List[str]

DirectoryStructure:
  - root: str
  - directories: List[str]
  - entry_point: str

CodeRepository:
  - skeleton: CodeSkeleton
  - files: List[CodeFile]
  - structure: DirectoryStructure
  - dependencies: List[str]
  - readme_content: str
```

**核心方法:**
- `generate_skeleton(engineering_plan)` → 生成 .pyi 接口 + 依赖图
- `generate_file(file_spec)` → 单文件代码生成
- `resolve_dependencies()` → 依赖解析
- `clean_markdown()` → 清理 markdown 代码块

#### 1.3.2 CodeMemoryAgent (MVP 可选)
```
输入: CodeRepository
输出: 更新 Symbol Table 到 SQLite
```

#### 1.3.3 CodeMiningAgent (MVP 可选)
```
输入: requirements, file_spec
输出: 外部代码片段
```

---

### 1.4 Stage 4 - Validation Agents

#### 1.4.1 FullCycleTestingAgent
```
输入: CodeRepository
输出: TestResult

BDDTestCase:
  - test_id: str
  - feature: str
  - scenario: str
  - given: str
  - when: str
  - then: str
  - test_code: str
  - status: str

TestError:
  - error_type: ErrorType (SYNTAX/RUNTIME/LOGIC/DEPENDENCY/TIMEOUT)
  - file_path: Optional[str]
  - line_number: Optional[int]
  - error_message: str
  - stack_trace: Optional[str]
  - suggestion: Optional[str]

TestResult:
  - logic_passed: bool
  - bdd_test_cases: List[BDDTestCase]
  - errors: List[TestError]
  - visual_verification: Optional[VisualVerificationResult]
  - execution_time: float
```

**核心方法:**
- `generate_bdd_tests(requirements)` → 生成 Given-When-Then 测试
- `run_tests(repository)` → 执行 pytest

#### 1.4.2 FineTuningAgent
```
输入: CodeRepository, TestResult
输出: (CodeRepository, bool)  # 修复后的代码 + 是否成功

核心方法:
- `execute(repository, test_result)` → 基于错误修复代码
- `fix_syntax_error()` → 修复语法错误
- `fix_import_error()` → 修复导入错误
- `generate_init_files()` → 生成 __init__.py
```

#### 1.4.3 VisualVerificationAgent
```
输入: ExecutionContext
输出: VisualVerificationResult
  - alignment_score: float
  - layout_feedback: str
  - missing_elements: List[str]
  - issues: List[str]
  - passed: bool
```

---

## Phase 2: Web 后端开发

### API 接口设计

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/projects | 创建新项目 |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/<id> | 项目详情 |
| GET | /api/projects/<id>/status | 项目状态 |
| GET | /api/projects/<id>/files | 文件列表 |
| GET | /api/projects/<id>/file/<path> | 文件内容 |
| WebSocket | /ws/project/<id> | 实时进度（**未实现**，当前通过轮询 GET /api/projects/<id>/status 获取 status/progress/current_stage） |

**当前实现：** REST API 已实现；任务状态通过轮询 `GET /api/projects/<id>/status` 获取，返回 `status`（pending/processing/completed/failed）、`progress`（0–100）、`current_stage`（如 Stage 1: Requirements）。

### 核心模块

```
src/web/
├── app.py              # Flask 应用
├── api/
│   ├── projects.py    # 项目 API
│   └── websocket.py   # WebSocket 进度
└── services/
    └── task_service.py # 任务服务
```

---

## Phase 3: Web 前端开发

### 页面设计

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | / | 需求输入框 |
| 项目列表 | /projects | 所有项目展示 |
| 项目详情 | /projects/<id> | 代码查看器、状态 |

### 技术栈
- 前端框架: HTML + JavaScript (简单版)
- 或 React/Vue (完整版)

---

## Phase 4: 后台任务

### 实现方式
- 使用 `threading.Thread` 处理长时任务
- 或使用 Celery (可选)

---

## 实施顺序图

```
Stage 1 (Interaction)
    ↓
Stage 2 (Planning)    [依赖 Stage 1 输出]
    ↓
Stage 3 (CodeGen)    [依赖 Stage 2 输出]
    ↓
Stage 4 (Validation)  [依赖 Stage 3 输出]
    ↓
Web API + 前端       [依赖完整 Pipeline]
```

---

## Phase 2 / Phase 3 完成情况

- **Phase 2 Web 后端：** REST API 已实现（创建项目、列表、详情、状态、文件列表、文件内容、需求分析/澄清/定稿）。WebSocket `/ws/project/<id>` 未实现，进度通过轮询 GET 状态接口获取。
- **Phase 3 Web 前端：** 由 `src.web.app` 提供静态首页与 API；若需完整前端（项目列表、代码查看器），需单独实现或集成现有静态页。

---

## 验收标准

每个 Stage 完成标准:
- [x] Agent 代码可运行
- [x] 输入输出接口正确
- [x] 单元测试通过（Stage 1–4 均有 Mock/结构测试）
- [x] 集成到 Orchestrator 可端到端运行
