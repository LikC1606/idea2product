"""单独测试 Stage 2"""
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.agents.stage2_planning.planning_agents import TaskDivisionAgent, AlgorithmAnalysisAgent, SchemePlanningAgent
from src.services.llm_service import LLMService
from src.core.data_models import Requirements

# 初始化
llm = LLMService()

# Stage 1: 获取需求
print("=" * 50)
print("STAGE 1: 需求收集")
print("=" * 50)

interaction = InteractionAgent(llm)
requirements = interaction.execute("A simple note-taking app: one page where I can enter text and save it")
print(f"Title: {requirements.title}")
print(f"Features: {[f.name for f in requirements.features]}")

# Stage 2: 规划
print("\n" + "=" * 50)
print("STAGE 2: 技术规划")
print("=" * 50)

# 2.1 任务拆分
task_agent = TaskDivisionAgent(llm)
tasks = task_agent.execute(requirements)
print(f"Tasks: {len(tasks)}")
for t in tasks:
    print(f"  - {t.id}: {t.name}")

# 2.2 算法分析
alg_agent = AlgorithmAnalysisAgent(llm)
algorithms = alg_agent.execute(tasks)
print(f"\nAlgorithms: {len(algorithms)}")

# 2.3 方案规划
scheme_agent = SchemePlanningAgent(llm)
files, interface_specs = scheme_agent.execute(requirements, tasks)

print(f"\nFiles: {len(files)}")
for f in files:
    print(f"  - {f.path}: {f.purpose}")

print(f"\nInterface Specs: {len(interface_specs)}")
for spec in interface_specs:
    print(f"  - {spec.file_path}")
    print(f"    module: {spec.module_name}")
    print(f"    imports: {spec.imports}")
    print(f"    exports: {[e.name for e in spec.exports]}")
    print()
