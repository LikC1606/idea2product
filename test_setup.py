#!/usr/bin/env python
"""测试脚本 - 检查项目是否正确配置"""

import sys
from pathlib import Path

def test_python_version():
    """检查 Python 版本"""
    print(f"✓ Python 版本: {sys.version.split()[0]}")
    if sys.version_info < (3, 9):
        print("✗ 需要 Python 3.9+")
        return False
    return True

def test_imports():
    """测试基本导入"""
    try:
        import pydantic
        print(f"✓ pydantic {pydantic.__version__} 已安装")
    except ImportError:
        print("✗ pydantic 未安装 - 运行: pip install -r requirements.txt")
        return False

    try:
        import openai
        print(f"✓ openai {openai.__version__} 已安装")
    except ImportError:
        print("✗ openai 未安装 - 运行: pip install -r requirements.txt")
        return False

    try:
        import click
        import rich
        print("✓ CLI 依赖已安装")
    except ImportError:
        print("✗ CLI 依赖未安装")
        return False

    return True

def test_project_structure():
    """检查项目结构"""
    required_files = [
        "config/settings.py",
        "src/core/orchestrator.py",
        "src/core/agent_base.py",
        "src/core/data_models.py",
        "src/services/llm_service.py",
        "src/cli.py",
    ]

    project_root = Path(__file__).parent
    all_exist = True

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_env_config():
    """检查环境配置"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✓ .env 文件存在")

        # 检查是否包含 API key
        env_content = env_file.read_text()
        if "OPENAI_API_KEY=sk-" in env_content:
            print("✓ OPENAI_API_KEY 已配置")
            return True
        else:
            print("⚠ OPENAI_API_KEY 未配置或为示例值")
            return False
    else:
        print("✗ .env 文件不存在 - 运行: cp .env.example .env")
        return False

def test_module_loading():
    """测试模块加载"""
    try:
        from config.settings import Settings, get_settings
        print("✓ 可以导入 Settings")
    except Exception as e:
        print(f"✗ 无法导入 Settings: {e}")
        return False

    try:
        from src.core.data_models import Requirements, Task, CodeRepository
        print("✓ 可以导入数据模型")
    except Exception as e:
        print(f"✗ 无法导入数据模型: {e}")
        return False

    try:
        from src.services.llm_service import LLMService
        print("✓ 可以导入 LLMService")
    except Exception as e:
        print(f"✗ 无法导入 LLMService: {e}")
        return False

    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Idea2Product 安装检查")
    print("=" * 60)

    tests = [
        ("Python 版本检查", test_python_version),
        ("依赖包检查", test_imports),
        ("项目结构检查", test_project_structure),
        ("环境配置检查", test_env_config),
        ("模块加载检查", test_module_loading),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[{name}]")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ 所有检查通过 ({passed}/{total})")
        print("\n下一步:")
        print("  python -m src.cli list  # 测试 CLI")
    else:
        print(f"⚠ {total - passed} 个检查失败 ({passed}/{total} 通过)")
        print("\n需要修复:")
        if not results[1]:  # 依赖包
            print("  1. 安装依赖: pip install -r requirements.txt")
        if not results[3]:  # 环境配置
            print("  2. 配置环境: cp .env.example .env")
            print("     然后编辑 .env 添加 OPENAI_API_KEY")

if __name__ == "__main__":
    main()
