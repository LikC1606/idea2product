# 代码生成规范

## Interface-First 流程

1. **pyi_stubs** — SchemePlanningAgent 输出 `.pyi` 占位；若为空，`skeleton_builder.generate_minimal_pyi_from_interface_specs` 补全
2. **CodeSkeleton** — `skeleton_builder.build_skeleton_from_pyi` 从 pyi 构建 interfaces + dependency_graph
3. **依赖顺序** — 按 dependency_graph 拓扑排序生成实现
4. **实现填充** — 每文件遵循接口约束，生成业务逻辑

## 关键文件

- `src/utils/skeleton_builder.py` — 构建 CodeSkeleton、解析 pyi
- `config/prompts/code_gen_*.txt` — CodeGenerationAgent 模块化提示（system_base, critical_rules, quality）
- `config/prompts/frontend_design_guidelines.txt` — 前端任务设计规范（包含 Bento Grid、Masonry Grid 等主页/图片布局建议）
- `templates/flask_base/` — 生成应用的模板基础
- `src/agents/stage3_generation/code_gen_templates.py` — Agent 失败兜底 stub 生成

## 禁止事项

- 不要绕过 skeleton_builder 直接修改 pyi 生成逻辑
- 生成实现时必须遵守 pyi 中定义的接口签名
- 跨文件调用时使用 symbol_table 提供的签名，不要臆造

## 输出

- 生成代码保存在 `data/projects/{id}/generated/`
- 包含 app.py、app/、config.py、templates/、requirements.txt

## theme 与 theme-factory 对应（可选扩展）

design_mode（modern/minimal/dashboard）可映射到 theme-factory 的 10 主题，供 ui_guidelines 产出更具体配色与字体：
- modern → Ocean Depths / Tech Innovation / Modern Minimalist
- minimal → Arctic Frost / Desert Rose
- dashboard → Golden Hour / Botanical Garden

## Masonry 图片布局推荐

- 当应用需要图片瀑布流、作品集、截图墙等页面时，优先考虑 **Masonry-style** 布局，而不是僵硬等高网格：
  - 使用多列布局（column-width + column-gap）或 dense grid，让不同高度的图片自然错落排布。
  - 列数随屏幕宽度自适应：小屏 1–2 列，中屏 2–3 列，大屏 3–5 列，避免单一固定列数。
  - 统一控制图片容器的圆角、阴影与间距，减少明显“大洞”和割裂感。
- 当 `ui_guidelines.layout == "masonry_grid"` 时，Stage 3 前端代码应在对应模板中采用上述 Masonry 布局策略，并参考 `frontend_design_guidelines.txt` 中的详细规则。

## Editorial / Magazine 布局推荐

- 对于以**内容阅读、报告、案例研究、长文档/知识**为主的页面（如 overview/report/insights/knowledge 等），Stage 2/Stage 3 可以采用 editorial/magazine 式布局，而不是平均分布的卡片网格：
  - 使用非对称网格（例如一大列正文 + 一窄列侧栏），避免机械 50/50 分栏。
  - 大标题 + 副标题 + Pull Quote 形成强排版层级，正文采用合适行宽与行距，配合充足留白。
  - 视觉元素（插图、示意图、截图）与文字内容交错出现，形成「图文交错」的阅读节奏。
- 当 Stage 2 在 `EngineeringPlan.ui_guidelines` 中设置 `global_layout_style: "editorial_magazine"` 或在 `ui_guidelines.page_layouts[route].layout_archetype == "editorial_magazine"` 时，Stage 3 在生成对应页面时应：
  - 按提示实现大标题+副标题+段落+侧栏/脚注的布局结构，避免简单三列平均卡片。
  - 保持整体对比度与留白，确保主要内容块有足够呼吸空间。
  - 在前端实现中优先使用 section/aside/figure 等语义化结构，并遵守 `frontend_design_guidelines.txt` 中的排版与可访问性建议。

详见 `npx openskills read theme-factory`。

## Split Hero 布局 archetype（左文案 / 右预览）

为复用项目首页中常见的「左侧主文案 / 右侧产品界面预览」分屏 Hero 布局，Stage 2/Stage 3 通过 `EngineeringPlan.ui_guidelines.hero_layouts` 进行约定与消费：

- **数据约定（Stage 2 输出）**
  - `engineering_plan.ui_guidelines.hero_layouts: Dict[str, Dict]`，key 为路由（如 `"/"`, `"/overview"`），value 为该页面首屏 Hero 的布局语义：
    - `layout_archetype: str`：当采用分屏 Hero 时应为 `"split_hero_left_text_right_preview"`。
    - `primary_column: "left" | "right"`：主要文案与 CTA 所在列，分屏 Hero 默认 `"left"`。
    - `contrast_mode: "dark_bg_light_text" | "light_bg_dark_text"`：Hero 背景与文字的对比模式，便于 Stage 3 选择合适的配色与阴影。
    - `notes: str`：补充说明 Hero 结构要素，例如「左列包含大标题、副标题、2–3 个卖点要点与主/次 CTA 按钮；右列为带 glow 的产品界面预览卡片，略小于左列，整体比例约 3:2 或 5:4」。
  - SchemePlanningAgent 在检测到应用存在 Landing/Homepage/入口 Hero 语义（title/description 中含 landing/homepage/入口页/产品介绍/选择生成方向/hero 等，或 Requirements.layout_preferences 中显式包含 `split_hero_left_text_right_preview`）时，应为首页路由写入上述 hero_layouts 条目。

- **实现约定（Stage 3 消费）**
  - CodeGenerationAgent 在构建 system prompt 时，从 `plan.api_specs.ui_guidelines.hero_layouts` 中读取当前应用的 hero 布局信息，并在「UI Guidelines」段落下追加「Hero Layouts (per route)」说明：
    - 对每个有 hero_layouts 的路由，明确 `layout_archetype`、`primary_column`、`contrast_mode` 以及 `notes`。
    - 在追加说明中重申：对于 `layout_archetype == "split_hero_left_text_right_preview"` 的路由，前端模板必须实现左文案 / 右预览的分屏 Hero，左列承载主文案+CTA，右列为产品界面预览卡片。
  - 针对首页或主要入口模板（通常是 index.html 或对应 route 的模板），前端生成时应：
    - 使用两列布局（CSS Grid 或 Flex），保持左列略宽于右列（例如 3:2 或 5:4），并对 primary_column 进行语义化实现。
    - 按 notes 中描述摆放标题、副标题、卖点列表、主/次按钮与预览卡片，避免退回成简单堆叠或均分栅格。
    - 保持与 `ui_guidelines.theme`、`primary_color`、`contrast_mode` 一致的配色与对比度。

## Gradient + Noise Hero 背景（aurora_parallax_with_noise）

在某些 modern/dashboard 风格的首页 Hero 或工作台背景中，可以在渐变/极光背景上叠加**细腻的噪点纹理**，以增加质感和纵深感，同时保持文案可读性。Stage 2/Stage 3 通过 `ui_design_spec.page_layouts[route].background` 约定：

- **数据约定（Stage 2 输出）**
  - 当某个路由的背景需要 aurora + noise 风格时，Stage 2 可以在对应的 `page_layouts[route]` 中写入：
    - `background.type: "aurora_parallax_with_noise"`：表示在基础 aurora/parallax 渐变层之上叠加细腻噪点纹理。
    - `background.parallax_speed: float`：视差滚动速度，建议约 0.5（前景滚动速度的 50% 左右）。
    - `background.noise_opacity: float`：噪点层的不透明度，通常在 0.04–0.08 区间，用于传递「质感明显但不过度显眼」的强度。
    - `background.notes: str`：补充说明，例如「使用深色渐变+柔和极光带，顶部覆盖低对比度噪点纹理，须确保标题/正文对比度充足且无明显平铺拼接痕迹」。

- **实现约定（Stage 3 消费）**
  - CodeGenerationAgent 在构建「UI Design Spec」说明时，会将 `background` 的 `type`、`parallax_speed` 与 `noise_opacity` 一并写入 system prompt，并在 `type == "aurora_parallax_with_noise"` 时明确：
    - 使用 CSS 渐变或 aurora 渐变作为主背景层。
    - 通过伪元素或覆盖层添加一层细腻噪点纹理（小尺寸无缝纹理 PNG/SVG 或 data URL），不透明度取自 `noise_opacity`，默认约 0.06。
    - 允许使用柔和的混合模式（如 soft-light/overlay），但必须确保标题与正文对比度不被削弱，且画面不会出现明显的网格/重复纹理。
  - 前端实现时应：
    - 将 gradient + noise 视为**大面积 shell 背景**（Hero 区或 workspace 背景），而不是每个卡片内部都单独叠加噪点，避免整体显得嘈杂。
    - 结合「Parallax background」与 Skeleton/Reveal/微交互等规范，一并遵守 `prefers-reduced-motion`：视差动画可以被冻结，但静态噪点纹理可保留，只要不产生闪烁或动画噪点。

## Code Generation 配置

- `use_fast_model_for_simple_code_tasks` — frontend+low 任务使用 fast model
- `fast_model_for_code_gen` — 默认 gpt-4o-mini
- `skip_mining_for_simple_tasks` — frontend/config-only 任务不注入 mining_context
- `max_system_prompt_chars` — system prompt 截断上限（默认 16000）
- `use_fast_model_for_syntax_fix` — 语法修复轮使用 fast model
- `code_gen_syntax_fix_retries` — 语法修复重试次数

## Loading 状态与 Skeleton 设计

- **适用场景**：页面存在明显等待（例如首屏加载远程数据、触发 AI 生成代码/报告/多媒体、批量导入/导出、长耗时计算）时，生成的前端代码必须为主内容区域设计清晰的 Loading 状态，而不是简单留白或只在页面中间放一个 Spinner。
- **首选方案：Skeleton Screen**  
  - 使用浅灰色块模拟最终布局的轮廓：列表行、详情卡片、表格行、侧边栏区块、图表占位等。  
  - Skeleton 风格应为简单灰块 + 渐变闪动（shimmer），对暗色主题友好，不要使用高对比度闪烁。  
  - 在实现时需兼容 `prefers-reduced-motion: reduce`，在该模式下关闭 shimmer，仅保留静态灰块。
- **布局模式建议**（Stage 2/3 仅需在规划中描述结构，不要求写死具体 CSS）：  
  - **列表页**：顶部工具栏/筛选条骨架 + 多行列表 item 骨架（左侧图标/checkbox 占位 + 文字行占位）。  
  - **详情页**：顶部概要卡片骨架（标题、关键字段条状占位）+ 下方分区/标签页内容骨架。  
  - **Dashboard/工作台**：若干卡片/图表区域的矩形骨架，保留与真实布局相同的网格结构。  
  - **编辑器/代码浏览器类界面**：左侧一列较窄的文件名骨架条，右侧多行代码行骨架条，顶部有文件信息/语言标签骨架。
- **规划阶段要求（Stage 2）**：  
  - 在 `ui_design_spec.page_layouts` 中，对每个需要等待的页面路由，`loading_state` 应优先使用 `\"type\": \"skeleton\"`，并在 `description` 或附加字段中描述骨架布局结构（例如哪些 section 显示骨架、每个区域大致形状）。  
  - 仅在等待时间极短、Skeleton 带来的收益有限时，可以退回简单 Spinner，但规划中必须显式说明理由。
- **实现阶段要求（Stage 3）**：  
  - 严格按照 Stage 2 的 `loading_state` 规划实现 Skeleton 布局，避免忽略或简化为单一 Spinner。  
  - Skeleton 只占用 Loading 状态；一旦真实数据/结果返回，应平滑切换到真实内容，避免 Skeleton 与真实内容长时间同时存在。
  - 当 Stage 2 在 `ui_design_spec` 中为某些 section 或卡片列表显式提到 “reveal on scroll” 之类的滚动进场动效时，Stage 3 在实现前端时应优先采用 **小幅上浮（≈6–10px）+ 轻微淡入（opacity 0 → 1，约 200–300ms）** 的 subtle 动画，并通过 IntersectionObserver 或等效机制确保每个元素只在首次进入视口时触发一次，且必须遵守 `prefers-reduced-motion` 设置（在 reduced 模式下降级为无动画或瞬时过渡）。

> 对于采用 Aurora / Parallax 背景的工作台或 Dashboard 布局，当 Stage 2 在 `ui_design_spec` 中给出相关 hint（例如 aurora_parallax + parallax_speed ≈ 0.5）时，Stage 3 实现应将视差背景作为独立背景层处理，使用滚动驱动的 transform 实现约 50% 的滚动速度，并同样尊重 `prefers-reduced-motion` 设置。

## Hover Micro-interactions（悬停微交互）

- 当 Stage 2 在 `ui_guidelines.layout_hints`、`ui_design_spec.product_grade_rules` 或各页面的 section 描述中提到 **hover micro-interactions**（例如主按钮、Tab、可点击卡片在悬停时轻微放大+阴影加深），Stage 3 在实现前端时应：
  - 使用少量 **共享的 CSS 工具类或小型 helper**（例如 `.interactive-scale` / `.interactive-scale-sm` 风格的类）统一实现 scale + shadow 效果，而不是在每个元素上散落独立的 `transform`/`box-shadow` 样式。
  - 将微交互主要应用于关键可点击元素（主/次按钮、导航 tab、可点击卡片/tiles 等），保持动效幅度克制（scale 约 1.01–1.03，150–200ms 过渡），避免影响布局或产生视觉噪音。
  - 严格遵守 `prefers-reduced-motion`：在 reduced 模式下关闭基于 transform 的缩放动画，仅保留颜色、边框或轻量阴影变化作为 hover 提示。

## Page & Stage Transitions（页面与阶段平滑转场）

- **适用范围**：
  - 主要面向使用 `vue-router` 或等价多路由视图的 Vue Web 应用。
  - 优先为以下场景提供平滑转场，而不是瞬间内容替换：
    - 路由级页面切换（例如 `/`, `/code`, `/video`, `/slides` 等主视图）。
    - 关键主视图/Stage 切换（如 Plan / Code / Preview 等右侧 pane）。
    - 状态栏或步骤指示中的阶段文案变化（如 Stage 1 → Stage 2 → Stage 3 → Stage 4）。
- **设计原则**：
  - 使用 **短时长（约 200–300ms）+ 低位移** 的淡入/轻微滑动动画，强调“顺滑”而非“炫技”。
  - 动画只作用于不影响布局的属性（opacity、transform），避免引起内容抖动或布局重排。
  - 所有转场必须遵守 `prefers-reduced-motion`：在该模式下降级为无位移、无长时间过渡的静态切换。
- **Vue 实现模式（推荐骨架）**：
  - 路由层（页面切换）：
    - 在根组件 `App.vue` 中使用：
      - `<Transition name="page-transition" mode="out-in"><RouterView /></Transition>`
    - 在全局或组件样式中定义：
      - `.page-transition-enter-active, .page-transition-leave-active`：对 `opacity` 与 `transform` 做过渡。
      - `.page-transition-enter-from, .page-transition-leave-to`：`opacity: 0; transform: translateY(10–16px);`
      - `.page-transition-enter-to, .page-transition-leave-from`：`opacity: 1; transform: translateY(0);`
  - 主视图 Tab 层（例如 WorkspaceShell 中的 Plan / Code / Preview）：
    - 使用 `<Transition name="tab-fade" mode="out-in">` 包裹主 pane：
      - `.tab-fade-enter-active, .tab-fade-leave-active`：对 `opacity` + `transform` 做过渡（可使用 `var(--transition-normal)`）。
      - `.tab-fade-enter-from, .tab-fade-leave-to`：`opacity: 0; transform: translateY(8–12px);`
      - `.tab-fade-enter-to, .tab-fade-leave-from`：`opacity: 1; transform: translateY(0);`
  - 阶段指示（例如状态栏中的 Stage 文案）：
    - 使用 `<Transition name="stage-fade" mode="out-in">` 包裹阶段文本，并以 `:key="currentStage"` 区分不同阶段：
      - `.stage-fade-enter-active, .stage-fade-leave-active`：对 `opacity` + `transform` 做短时过渡（可使用 `var(--transition-fast)`）。
      - `.stage-fade-enter-from, .stage-fade-leave-to`：`opacity: 0; transform: translateY(4px);`
      - `.stage-fade-enter-to, .stage-fade-leave-from`：`opacity: 1; transform: translateY(0);`
- **Reduced motion 处理**：
  - 在全局或组件样式中对上述类统一加入：
    - `@media (prefers-reduced-motion: reduce)` 下，将 `*-enter-active` / `*-leave-active` 的 `transition` 设为 `none`。
    - 对 `*-enter-from` / `*-enter-to` / `*-leave-from` / `*-leave-to` 中的 `transform` 强制设为 `none`，必要时也可轻微保留 opacity 过渡。
- **模板与骨架建议**：
  - Vue 前端的标准骨架应默认包含上述结构和 CSS 片段：
    - `App.vue` 预置 `page-transition` 包裹的 `RouterView`。
    - 主要布局组件（如工作台/编辑器 Shell）预置 `tab-fade` 包裹的右侧主 pane。
    - 状态栏组件预置 `stage-fade` 包裹的阶段指示。
  - CodeGenerationAgent 在生成 Vue 应用时，应优先沿用这些 archetype，只有在需求明确要求“极简静态无动效”时才降级为无动画或仅淡入。
  - 后续在 skeleton/template 层实现时，可将上述结构抽象为可复用骨架片段：
    - Vue 应用脚手架模板中直接包含 `App.vue` 的 `page-transition` 结构。
    - 针对「工作台/编辑器 Shell」和「状态栏」定义带 `tab-fade` / `stage-fade` 的通用组件模版，供不同项目复用。

## See also

- AGENTS_REF — SchemePlanningAgent、CodeGenerationAgent
- DATA_MODELS_REF — CodeSkeleton、CodeRepository、EngineeringPlan
