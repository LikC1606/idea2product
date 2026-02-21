"""单独测试 Stage 2"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from src.core.data_models import Requirements, Feature

# 初始化
settings = get_settings()

# 创建 LLM 服务
from src.services.llm_service import LLMService
llm = LLMService(settings.openai_api_key, base_url=settings.openai_base_url)

# 直接创建需求
print("=" * 60)
print("STAGE 1: 需求收集 (模拟)")
print("=" * 60)

requirements = Requirements(
    title="A simple note-taking app",
    description="One page where I can enter text and save it",
    features=[
        Feature(id="F1", name="Create note", description="Enter text in a text area"),
        Feature(id="F2", name="Save note", description="Save the entered text")
    ]
)
print(f"Title: {requirements.title}")
print(f"Features: {[f.name for f in requirements.features]}")

# Stage 2: 规划
print("\n" + "=" * 60)
print("STAGE 2: 技术规划")
print("=" * 60)

# 2.1 任务拆分
print("\n--- 2.1 任务拆分 ---")
from src.agents.stage2_planning.planning_agents import TaskDivisionAgent
task_agent = TaskDivisionAgent(llm)
tasks = task_agent.execute(requirements)
print(f"Tasks ({len(tasks)}):")
for t in tasks:
    print(f"  {t.id}: {t.name} ({t.type})")
    print(f"    {t.description}")

# 2.2 算法分析
print("\n--- 2.2 算法分析 ---")
from src.agents.stage2_planning.planning_agents import AlgorithmAnalysisAgent
alg_agent = AlgorithmAnalysisAgent(llm)
algorithms = alg_agent.execute(tasks)
print(f"Algorithms: {len(algorithms)}")

# 2.3 方案规划
print("\n--- 2.3 方案规划 ---")
from src.agents.stage2_planning.planning_agents import SchemePlanningAgent
scheme_agent = SchemePlanningAgent(llm)
files, interface_specs = scheme_agent.execute(requirements, tasks)

print(f"\nFiles: {len(files)}")
for f in files:
    related = f.related_tasks if hasattr(f, 'related_tasks') else []
    print(f"  - {f.path} (layer: {f.layer}, tasks: {related})")
    print(f"    purpose: {f.purpose}")

print(f"\nInterface Specs: {len(interface_specs)}")
for spec in interface_specs:
    print(f"  - {spec.file_path}")
    print(f"    module: {spec.module_name}")
    print(f"    imports: {spec.imports}")
    print(f"    exports: {[e.name for e in spec.exports]}")
    print()
