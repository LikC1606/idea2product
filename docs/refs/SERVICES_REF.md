# 服务层参考

来源：`src/services/`

## LLMService

- **文件**：`src/services/llm_service.py`
- **作用**：OpenAI 兼容 API 调用，重试、流式、超时
- **创建**：`LLMService.from_settings(settings)` — 根据 `primary_llm_provider`（openai | anthropic | google）选择对应 key、base_url、model；所有 Agent 应通过此方式获取实例
- **主用 API 配置**：`config/settings.py` 中 `get_primary_llm_config(settings)` 返回 `(api_key, base_url, model, vlm_model)`；校验时 `validate_settings(settings, require_llm_key=True)` 要求主用 key 已配置
- **模型切换**：`with_model(model_id, base_url=...)` 返回配置不同模型/端点的副本
- **ProviderAdapter**：支持 OpenRouter、Azure 等，按 base_url 自动检测

## ModelRegistry / ModelSelector

- **ModelRegistry**（`model_registry.py`）：从 `config/models_registry.json` 加载模型定义
- **ModelSelector**（`model_selector.py`）：按 stage、requires_vision、prefer_fast 选择模型
- **路由**：stage_routing 映射 stage → preferred_role、required_capabilities
- **Fallback**：registry 为空或未匹配时使用 `OPENAI_MODEL` / `OPENAI_VLM_MODEL`

## CodeMemoryService

- **文件**：`src/services/code_memory_service.py`
- **存储**：SQLite，`data/code_memory.db`
- **功能**：AST 解析、symbol_table、相似片段检索（FTS5 code_search）
- **开关**：`ENABLE_CODE_MEMORY`（默认 True），`enable_cross_project_memory` 控制跨项目预取
- **FTS5 同步**：`add_snippet` 在 REPLACE code_snippets 前先 DELETE code_search 对应 row，确保 rowid 与 code_snippets 一致，避免 FTS5 行错位

## CodeMiningService

- **文件**：`src/services/code_mining_service.py`
- **功能**：GitHub 代码检索，支持缓存与接口适配
- **开关**：`ENABLE_CODE_MINING`（默认 True），无 GITHUB_TOKEN 时建议关闭
- **可选**：`ENABLE_LLM_CODE_ADAPTATION` 启用 LLM 适配挖掘代码（增加 API 成本）
- **缓存分层**：query 级 raw 结果缓存（_raw_cache）+ (content_hash, interface_spec) 级 adapt 缓存（_adapt_cache），相同 query 仅打一次 API，不同 interface 本地 adapt
- **限流退避**：`_get_with_retry` 在 403 时指数退避重试 1–2 次

## HfModelService

- **文件**：`src/services/hf_model_service.py`
- **功能**：Hugging Face 模型搜索（AlgorithmAnalysis 等）
- **开关**：`enable_hf_model_search`（默认 False）
- **缓存**：`use_cache=True` 时 LRU 缓存 search_and_fetch_docs（max 32），由 `enable_hf_cache` 配置

## ImageGenerationService

- **文件**：`src/services/image_generation_service.py`
- **作用**：按任务类型接入的图生服务，与 LLM 分离；支持前端 hero/占位图生成与设计参考
- **接口**：`ImageGenerationProvider` 协议，`generate(prompt, size=..., n=1) -> List[bytes]`
- **实现**：`OpenAIImageProvider`（DALL-E）、`GenericHTTPImageProvider`（任意 HTTP 图生 API，配置 base_url、api_key、response_image_path 等）
- **工厂**：`get_image_provider(settings)` — `enable_image_generation=False` 时返回 `None`
- **配置**：`enable_image_generation`、`image_generation_provider`（openai | generic_http）、`image_generation_openai_model`、`image_generation_base_url`、`image_generation_api_key`、`image_generation_extra_headers`、`image_generation_response_image_path`、`image_generation_timeout`

## Video/PPT/LaTeX/Audio Generation Services（多模态生成）

- **视频生成**（VideoGenerationService）
  - **文件**：`src/services/video_generation_service.py`
  - **接口**：`VideoGenerationProvider.generate_video(prompt, duration_seconds=None, format=\"mp4\") -> Path`
  - **实现**：`GenericHTTPVideoProvider`（通用 HTTP 客户端，具体 API 由 settings / ExternalModelSpec 决定）
  - **工厂**：`get_video_provider(settings, spec=None)` — 当 `enable_video_generation=False` 或 base_url 缺失时返回 None
  - **配置**：`enable_video_generation`、`video_generation_provider`（generic_http）、`video_generation_base_url`、`video_generation_api_key`、`video_generation_extra_headers`、`video_generation_timeout`

- **PPT 生成**（PresentationGenerationService）
  - **文件**：`src/services/ppt_generation_service.py`
  - **接口**：`PresentationGenerationProvider.generate_ppt(slides_spec, format=\"pptx\") -> Path`
  - **实现**：`GenericHTTPPresentationProvider`
  - **工厂**：`get_ppt_provider(settings, spec=None)`
  - **配置**：`enable_ppt_generation`、`ppt_generation_provider`、`ppt_generation_base_url`、`ppt_generation_api_key`、`ppt_generation_extra_headers`、`ppt_generation_timeout`

- **LaTeX/PDF 生成**（LatexGenerationService）
  - **文件**：`src/services/latex_generation_service.py`
  - **接口**：`LatexGenerationProvider.render(spec, output_format=\"tex\") -> Path`
  - **实现**：`GenericHTTPLatexProvider`
  - **工厂**：`get_latex_provider(settings, spec=None)`
  - **配置**：`enable_latex_generation`、`latex_generation_provider`、`latex_generation_base_url`、`latex_generation_api_key`、`latex_generation_extra_headers`、`latex_generation_timeout`

- **音频生成（TTS/音乐）**（AudioGenerationService）
  - **文件**：`src/services/audio_generation_service.py`
  - **接口**：`AudioGenerationProvider.generate_audio(text, voice=None, format=\"mp3\") -> Path`
  - **实现**：`GenericHTTPAudioProvider`
  - **工厂**：`get_audio_provider(settings, spec=None)`
  - **配置**：`enable_audio_generation`、`audio_generation_provider`、`audio_generation_base_url`、`audio_generation_api_key`、`audio_generation_extra_headers`、`audio_generation_timeout`

## AssetGeneration（Stage 3 可选步骤）

- **文件**：`src/services/asset_generation.py`
- **作用**：根据 plan 的 `image_specs` 或默认规则（hero + placeholder）调用图生服务，将图片写入 `generated/static/images/`，并写回 `context.generated_image_paths`
- **调用**：Orchestrator 在 Stage 3 中、CodeGenerationAgent 之前，当 `enable_image_generation` 为 True 时调用 `run_asset_generation(context, settings)`
- **CodeGen 引用**：CodeGenerationAgent 在前端任务 prompt 中注入 `generated_image_paths`，提示使用 `/static/images/xxx.png`
- **Plan 覆盖**：若 plan.external_model_specs 中存在 capability_type=image_generation 且含 base_url_hint，则优先用该 spec 配置 GenericHTTPImageProvider（api_key 仍从 settings 读）

## WebSearchService（Stage 2 模型发现）

- **文件**：`src/services/web_search_service.py`
- **作用**：为 ModelIntegrationPlanningAgent 提供联网搜索（检索 API 文档等）
- **接口**：`WebSearchProvider.search(query, num_results=5) -> List[Dict]`（title, link, snippet）
- **实现**：SerperSearchProvider（Serper API，Google 搜索）
- **工厂**：`get_web_search_provider(settings)` — `enable_stage2_web_search=False` 或未配置 API Key 时返回 `None`
- **配置**：enable_stage2_web_search、web_search_provider（serper）、web_search_api_key（或 serper_api_key）、web_search_num_results、web_search_timeout

## execution_service

- **文件**：`src/services/execution_service.py`
- **状态**：保留，当前 pipeline 未使用

## See also

- AGENTS_REF — 各 Agent 使用 LLMService
- config/settings.py — 完整配置项
