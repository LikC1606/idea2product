# 故障排查

问题 → 可能原因 → 解决步骤。遇报错时优先查阅本表。

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
| **Tests failing after generation** | 生成代码有缺陷 | 系统会尝试自动修复；查看 `data/projects/<id>/logs/` 日志 |
| **Import errors in generated app** | 依赖未安装 | 在生成应用目录执行 `pip install -r requirements.txt` |

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
| **Empty or minimal generated code** | 需求不够具体 | 使用更明确的描述，避免过于宽泛的「Build an app」 |
| **`pytest tests/` 失败** | 依赖或路径问题 | 在项目根目录执行 `pip install -r requirements.txt`；单元测试使用 mock，无需 API key |

## 阶段失败与 API 错误响应

| 现象 | 说明 | 解决步骤 |
|------|------|----------|
| **StageExecutionError** | 某阶段执行失败时 Orchestrator 抛出的异常 | 查看 `stage` 属性（1～4）和 `partial_context`（或 `data/projects/<id>/artifacts/context.json`）定位失败阶段；根据 `__cause__` 或日志排查具体原因 |
| **500 响应仅返回 "Internal server error"** | 生产态下 Web API 不向客户端返回详细错误内容 | 服务端会通过 `logger.exception` 记录完整异常；查服务端日志获取堆栈。若需在响应中看到详情，可设置 `EXPOSE_ERROR_DETAILS=true`（仅用于调试） |

## 相关文档

- 代码生成规范：@docs/specs/CODE_GEN_SPEC.md
- Agent 输入输出：@docs/refs/AGENTS_REF.md

## 增强 UI 测试

需更细粒度 UI 测试时，可参考 webapp-testing 技能（Playwright + with_server.py）：
```bash
npx openskills read webapp-testing
```
