# Web 层参考

## REST API（src/web/api/projects.py）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/projects | 创建项目 `{"start_chat": true}` 或 `{"requirement": "..."}` |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/<id> | 项目详情 |
| GET | /api/projects/<id>/status | 生成状态（idle/pending/processing/completed/failed） |
| POST | /api/projects/<id>/chat | 发送消息，获取 AI 回复 |
| POST | /api/projects/<id>/generate | 显式触发生成 |
| GET | /api/projects/<id>/chat | 聊天历史 |
| GET | /api/projects/<id>/files | 生成文件列表 |
| GET | /api/projects/<id>/file/<path> | 文件内容 |
| GET | /api/projects/<id>/preview-url | 实时预览 URL |
| DELETE | /api/projects/<id> | 删除项目 |

## Chat-first 流程

1. `POST /api/projects {"start_chat": true}` → 创建项目，返回 project_id
2. `POST /api/projects/<id>/chat {"message": "..."}` → 追加消息，获取 AI 回复
3. 用户可调用 `POST /api/projects/<id>/generate` 显式触发生成，或由前端自动触发
4. 首次生成：`conversation_to_requirements()` → `orchestrator.run_from_stage_2()`
5. 增量：`merge_requirements(existing, new_msg)` → `orchestrator.run_from_stage_2()`
6. 生成完成后 `preview_service.start_preview()` 在动态端口启动应用

## 服务

- **chat_service** (`src/web/services/chat_service.py`) — 持久化 `artifacts/chat.json`
- **preview_service** (`src/web/services/preview_service.py`) — 管理预览子进程、动态端口
- **task_service** (`src/web/services/task_service.py`) — 后台生成，按项目串行化

## See also

- AGENTS_REF — InteractionAgent 的 conversation_to_requirements、merge_requirements
