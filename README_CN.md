<!-- README_SYNC: source=8e9c0125f75c21c72dcd7be5d76646e42a6f44ce; updated=2026-11-23 -->
<p align="center">简体中文 · <a href="./README.md" lang="en">English</a></p>

# Idea2Product

Idea2Product 把一段自然语言需求转化为可在本地检查和运行的 Flask Web 应用，并逐阶段留存需求文档、工程规划、生成代码与验证日志，方便追溯每处代码的来源和待修复项。

<a href="https://github.com/LikC1606/idea2product"><img alt="GitHub stars" src="https://img.shields.io/github/stars/LikC1606/idea2product"></a>
<a href="https://github.com/LikC1606/idea2product/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/LikC1606/idea2product/actions/workflows/ci.yml/badge.svg"></a>
<a href="./pyproject.toml"><img alt="Project version 0.1.0" src="https://img.shields.io/badge/version-0.1.0-blue"></a>
<img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776ab">
<a href="./frontend/package.json"><img alt="Frontend: Vue 3" src="https://img.shields.io/badge/frontend-Vue_3-42b883"></a>

欢迎[给仓库点 Star](https://github.com/LikC1606/idea2product)，方便回看流程和评测资料。

单次生成可以用 Python CLI；想边聊需求边看代码和预览，可以打开 Build Studio。生成的是应用原型，部署前请先检查代码、依赖和验证结果。

## 快速开始

准备 Python 3.12 和 Git。以下命令适用于 Unix shell；依赖见 [requirements.txt](./requirements.txt)。安装时用这份文件，旧的[固定版本列表](./requirements-pinned.txt)早于代码现在使用的 `langchain.agents.create_agent` 接口。

```bash
git clone https://github.com/LikC1606/idea2product.git
cd idea2product
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.cli --help
cp .env.example .env
```

参考[配置示例](./.env.example)编辑 `.env`，把 `PRIMARY_LLM_PROVIDER` 设为 `openai`、`anthropic` 或 `google`，并填对应的 API Key。后两种提供商通过各自 Base URL 指向兼容端点。不要把密钥提交到 Git。生成会调用所配置的模型服务，并可能产生使用费用。

```bash
python -m src.cli create "Build a todo app that can add, complete, and delete tasks"
```

生成成功后，CLI 会打印项目位置和运行入口。先检查 `generated/` 里的生成文件、运行说明和验证结果。需要先澄清需求时，可用 `-i` 进入互动模式。下面的 `PROJECT_ID` 换成 CLI 显示的项目 ID。

```bash
python -m src.cli create --help
python -m src.cli list
python -m src.cli status PROJECT_ID
python -m src.cli from-paper --help
```

## 在浏览器里用 Build Studio

Vite 前端需要 Node.js 20.19 或更高的 20.x 版本，或 22.12 及以上版本。激活 Python 环境后，在项目根目录运行：

```bash
npm ci --prefix frontend
npm run build --prefix frontend
HOST=127.0.0.1 PORT=8080 python -m src.web.app
```

打开 `http://127.0.0.1:8080`。Flask 同时提供已构建的 Vue 界面和 API；在 Build Studio 里可以同时查看对话、生成文件和预览。[Web 流程说明](./docs/refs/WEB_FLOW_REF.md)介绍开发代理、REST 接口和预览进程。

## 各阶段会留下什么

| 阶段 | 产物 |
| --- | --- |
| 需求 | 功能和约束明确的需求记录 |
| 规划 | 用户流程、任务、API、文件结构和接口存根 |
| 生成 | 按规划接口和依赖顺序生成的源文件 |
| 验证 | 测试与启动结果、修复尝试，以及可选的 BDD 和视觉检查 |

```text
data/projects/<project_id>/
  artifacts/
    01_requirements.json
    02_engineering_plan.json
    03_code_repository.json
    context.json
  generated/
  logs/
```

[架构说明](./docs/ARCHITECTURE.md)解释各 Agent 怎样分工交接；[数据模型参考](./docs/refs/DATA_MODELS_REF.md)列出了记录的字段和关系。

## 开发与评测

- [文档索引](./docs/CONTEXT_INDEX.md)汇总了 Agent、模型接入和配置资料。依赖、模型连接或预览有问题，先看[故障排查](./docs/TROUBLESHOOTING.md)。
- [基准评测说明](./docs/BENCHMARK.md)和[研究评测协议](./docs/paper/EVALUATION.md)介绍任务和指标。在线评测会调用模型服务；比较结果时请记录模型、依赖版本和功能开关。
- [CI 工作流](./.github/workflows/ci.yml)列有测试和检查命令。以下命令可检查文档列出的 Agent 是否仍存在于源码中：

```bash
python scripts/check_docs.py
```

当前仓库未附许可文件，README 不声明 MIT 或其他复用许可。

欢迎[提交 Issue](https://github.com/LikC1606/idea2product/issues)并附上出错阶段和相关日志，也可以[点 Star](https://github.com/LikC1606/idea2product)收藏。
