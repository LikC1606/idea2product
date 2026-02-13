# Idea2Product MVP 实现计划（已更新）

> **更新说明**: 本计划基于 2026年2月13日 更新的 plan.txt，包含了最新的 agent 设计变更。

## 📋 主要变更概览

### 🔴 API 变更
- **原方案**: Claude API (Anthropic)
- **新方案**: **OpenAI API (GPT-4o)**
- **新增功能**: 支持 GPT-4o 视觉模型用于前端视觉验收

### 🔴 Stage 3 - 代码生成阶段重大升级

**原方案**: 简单的逐文件生成，无历史上下文依赖

**新方案**: **Interface-First（接口优先）策略**

#### 1. 代码生成智能体 (Code Generation Agent)
- **全局骨架生成**:
  - 先生成项目的全局接口定义（`.pyi` / Type Definitions）
  - 生成文件依赖关系图
  - 确立跨模块调用的"硬约束"
- **局部实现填充**:
  - 基于接口约束逐文件生成具体业务逻辑
  - 检索符号表而非完整代码
  - 规避长语境幻觉，保障类型安全

#### 2. 代码记忆智能体 (Code Memory Agent)
- **原功能**: 记录已生成代码的功能定义、调用逻辑与复用规范
- **新功能升级**:
  - ✨ **构建项目的动态知识图谱**
  - ✨ **实时维护抽象语法树（AST）与全局符号表**
  - 提供精准的接口签名（Signature）而非完整代码实现

#### 3. 代码挖掘智能体 (Code Mining Agent)
- **原功能**: 检索 GitHub 通用代码片段
- **新功能**:
  - ✨ **基于当前项目的接口规范进行适配性重构**
  - 确保外部代码能"无缝缝合"进当前架构

### 🔴 Stage 4 - 测试阶段重大升级

**Agent 改名**: `Black-box Testing Agent` → **`Full-cycle Testing Agent`**

#### 全链路测试智能体 (Full-cycle Testing Agent)

**原功能**: 黑盒测试与运行验证

**新功能**: 引入"**逻辑-视觉**"双流验证机制

1. **测试驱动（Test-Driven）**:
   - ✨ **在代码生成前**自动合成 BDD（行为驱动开发）格式的测试用例
   - Given-When-Then 脚本格式
   - 代码生成后即时执行单元测试与集成测试
   - 验证业务逻辑是否符合预期

2. **视觉验收（Visual Verification）**:
   - ✨ 针对前端界面，调用**多模态大模型（VLM, GPT-4o）**
   - 对渲染后的页面截图进行语义理解
   - 计算"**视觉-语义对齐度**"
   - 自动发现布局错乱或元素缺失问题

#### 微调优化智能体 (Fine-tuning Agent)

**增强功能**:
- 基于测试用例的失败断言（Assertion Failure）
- 基于视觉验收的差异报告
- 定位具体的代码错误片段
- 执行针对性的代码修复（Debug）
- 回归测试（Regression Test）直至所有测试用例通过

---

## 🏗️ 系统架构（更新版）

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (CLI)                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│              (Manages stages and agent coordination)             │
└─────────────────┬───────────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────────────┬──────────────┐
        ▼         ▼         ▼                 ▼              ▼
    STAGE 1   STAGE 2   STAGE 3          STAGE 4
                      (Interface-First)   (Logic + Visual)
```

### Stage 3: 代码生成流程（Interface-First）

```
EngineeringPlan
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│ Step 1: 全局骨架生成                                     │
│                                                          │
│ Code Generation Agent:                                  │
│  - 生成全局接口定义 (.pyi)                               │
│  - 生成文件依赖关系图                                    │
│  - 生成全局符号表                                        │
│                                                          │
│ Output: CodeSkeleton {                                  │
│   interfaces: List[InterfaceDefinition]                 │
│   dependency_graph: DependencyGraph                     │
│   symbol_table: List[SymbolTableEntry]                  │
│ }                                                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Step 2: 局部实现填充                                     │
│                                                          │
│ For each file in dependency order:                      │
│   ┌─────────────────────────────────────┐               │
│   │ Code Generation Agent:              │               │
│   │  1. Query Code Memory Agent         │──────┐        │
│   │     (get symbol table entries)      │      │        │
│   │  2. Query Code Mining Agent         │      │        │
│   │     (get adapted snippets)          │      │        │
│   │  3. Generate implementation         │      │        │
│   │  4. Store in Code Memory            │──────┘        │
│   └─────────────────────────────────────┘               │
│                                                          │
│ Output: CodeRepository {                                │
│   skeleton: CodeSkeleton                                │
│   files: List[CodeFile]                                 │
│ }                                                        │
└──────────────────────────────────────────────────────────┘
```

### Stage 4: 全链路测试流程（Logic + Visual）

```
CodeRepository
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│ Full-cycle Testing Agent                                 │
│                                                          │
│ Logic Testing:                                           │
│  1. Execute BDD test cases (auto-generated)              │
│  2. Run unit tests                                       │
│  3. Run integration tests                                │
│  Output: logic_passed (bool) + errors                    │
│                                                          │
│ Visual Verification (if frontend exists):                │
│  1. Start application                                    │
│  2. Capture screenshots (Selenium)                       │
│  3. Analyze with VLM (GPT-4o):                           │
│     - Compare screenshot vs requirement                  │
│     - Calculate visual-semantic alignment score          │
│     - Detect missing/misplaced elements                  │
│  Output: VisualVerificationResult                        │
│                                                          │
│ Aggregate: TestResult {                                  │
│   logic_passed: bool                                     │
│   bdd_test_cases: List[BDDTestCase]                      │
│   visual_verification: VisualVerificationResult          │
│ }                                                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
              ┌──────────┐
              │  Passed? │
              └─────┬────┘
                    │
           ┌────────┴────────┐
           │                 │
          YES               NO
           │                 │
           │                 ▼
           │     ┌───────────────────────┐
           │     │ Fine-tuning Agent     │
           │     │  - Fix logic errors   │
           │     │  - Fix visual issues  │
           │     │  - Regression test    │
           │     └───────┬───────────────┘
           │             │
           └─────────────┘
                     │
                     ▼
            ValidatedProject
```

---

## 📦 新增数据模型

### Stage 3 - Interface-First Models

```python
class InterfaceDefinition(BaseModel):
    """接口定义 (.pyi 风格)"""
    module_name: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    type_hints: str

class SymbolTableEntry(BaseModel):
    """符号表条目"""
    symbol_name: str
    symbol_type: str  # function, class, variable
    module: str
    signature: Optional[str]
    line_number: int

class DependencyGraph(BaseModel):
    """文件依赖关系图"""
    nodes: List[str]  # 文件路径
    edges: List[Dict[str, str]]  # from -> to
    entry_point: str

class CodeSkeleton(BaseModel):
    """全局骨架（Interface-First）"""
    interfaces: List[InterfaceDefinition]
    dependency_graph: DependencyGraph
    symbol_table: List[SymbolTableEntry]
```

### Stage 4 - BDD & Visual Verification Models

```python
class BDDTestCase(BaseModel):
    """BDD 测试用例"""
    test_id: str
    feature: str
    scenario: str
    given: str  # 前置条件
    when: str   # 操作
    then: str   # 预期结果
    test_code: str
    status: str  # pending/passed/failed

class VisualVerificationResult(BaseModel):
    """视觉验收结果"""
    screenshot_path: str
    requirement_text: str
    alignment_score: float  # 0.0-1.0
    layout_feedback: str
    missing_elements: List[str]
    issues: List[str]
    passed: bool

class TestResult(BaseModel):
    """全链路测试结果"""
    # Logic testing
    logic_passed: bool
    bdd_test_cases: List[BDDTestCase]
    errors: List[TestError]

    # Visual verification
    visual_verification: Optional[VisualVerificationResult]

    @property
    def passed(self) -> bool:
        """逻辑测试 AND 视觉验收都通过"""
        return self.logic_passed and (
            self.visual_verification.passed
            if self.visual_verification else True
        )
```

---

## 🔧 技术栈更新

### API 与模型
- ✅ **OpenAI API** (替代 Claude API)
- ✅ **GPT-4o** - 主要代码生成模型
- ✅ **GPT-4o Vision** - 前端视觉验收

### 新增依赖

```txt
# API
openai>=1.54.0

# Code analysis (AST & Symbol Table)
astroid>=3.3.0

# Visual verification
Pillow>=10.0.0
selenium>=4.27.0

# BDD testing
pytest-bdd>=7.0.0
```

---

## 📝 实现优先级（更新版）

### Phase 1: Foundation ✅ **已完成**
- ✅ OpenAI LLMService（已更新）
- ✅ 配置系统（已更新）
- ✅ 数据模型（已添加新模型）
- ✅ Agent 基类
- ✅ Orchestrator 骨架

### Phase 2: Stage 1 - Requirements ⏳ **下一步**
- 实现 Interaction Agent
- 创建 prompt 模板

### Phase 3: Stage 2 - Planning ⏳
- Task Division Agent
- Algorithm Analysis Agent
- Scheme Planning Agent

### Phase 4: Stage 3 - Code Generation (Interface-First) ⏳
**关键更新**:
1. **Step 1 实现**: 全局骨架生成
   - 接口定义生成
   - 依赖图分析
   - 符号表构建
2. **Step 2 实现**: 局部实现填充
   - 基于符号表的代码生成
3. **Code Memory Agent 升级**: AST 和符号表维护
4. **Code Mining Agent 升级**: 适配性重构

### Phase 5: Stage 4 - Full-cycle Testing ⏳
**关键更新**:
1. **BDD 测试用例生成**
   - 基于需求自动合成 Given-When-Then
   - pytest-bdd 集成
2. **视觉验收实现**
   - Selenium 截图
   - GPT-4o Vision 分析
   - 对齐度评分
3. **Fine-tuning Agent 增强**
   - 处理逻辑错误
   - 处理视觉问题

### Phase 6: Integration & Testing ⏳
- 端到端集成
- 完整工作流测试

---

## 🎯 MVP 简化策略（更新版）

| 组件 | 完整愿景 | MVP 简化 | 备注 |
|------|---------|---------|------|
| **Interface-First** | 完整的接口约束系统 | 基础的 .pyi 生成 + 简单符号表 | 证明概念可行性 |
| **Code Memory (AST)** | 完整的动态知识图谱 | 基于 astroid 的简单 AST 解析 | 提供基本符号信息 |
| **Code Mining 适配** | 智能重构外部代码 | 模板匹配 + 简单替换 | 降低复杂度 |
| **BDD 测试生成** | 完整的测试推理 | 固定模板生成 3-5 个关键测试 | 覆盖核心场景 |
| **视觉验收** | 复杂的像素级比对 | GPT-4o 语义分析 + 简单评分 | 利用 VLM 能力 |
| **Fine-tuning** | 多轮迭代修复 | 最多 2 次修复尝试 | 避免无限循环 |

---

## 📊 Benchmark 体系（参考 plan.txt）

基于研究提案，未来的评估体系将包括：

### 1. 代码质量维度
- 语法正确性
- 编码规范符合性
- 代码安全性

### 2. 环境适配与运行维度
- Docker 容器化成功率
- 依赖安装成功率
- 服务启动成功率

### 3. 需求实现与前端效果维度
- ✨ **Pass@k (BDD)**: 基于 BDD 测试用例的通过率
- ✨ **Visual-Semantic Alignment**: VLM 计算的视觉语义对齐度

---

## 🚀 快速开始

### 环境配置

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_KEY
```

3. 测试 LLM 连接:
```bash
python -m src.cli list
```

---

## 📚 参考文档

- [研究提案](plan.txt) - 完整的研究背景和方法论
- [原始实现计划](.claude/plans/wise-strolling-hamster.md) - 更详细的技术设计

---

## ✅ 已完成的变更

- ✅ OpenAI API 集成（替代 Claude）
- ✅ 添加视觉验收支持（GPT-4o Vision）
- ✅ 更新数据模型支持 Interface-First
- ✅ 添加 BDD 和视觉验收数据模型
- ✅ 重命名 Black-box Testing → Full-cycle Testing
- ✅ 更新配置系统和依赖项

## ⏳ 待实现

- ⏳ Interface-First 代码生成逻辑
- ⏳ AST 和符号表维护
- ⏳ BDD 测试用例生成
- ⏳ VLM 视觉验收实现
- ⏳ 所有 10 个 Agent 的具体实现

---

**版本**: 0.1.0 (Updated 2026-02-13)
**状态**: Phase 1 完成，Phase 2 准备中
