"""Pre-defined task templates for common application patterns.

When TaskDivisionAgent detects that the requirements match a known pattern,
these templates serve as a structural hint — the LLM fills in
project-specific details (entity names, fields, page content).
"""

from typing import List, Dict, Optional


CRUD_APP_TEMPLATE: List[Dict] = [
    {
        "id": "T1",
        "name": "创建{entity}完整后端",
        "description": "创建{entity}的数据模型和完整后端API接口，包括：数据模型({fields})、GET /api/{entity_lower}s 获取列表、GET /api/{entity_lower}s/<id> 获取详情、POST /api/{entity_lower}s 创建、PUT /api/{entity_lower}s/<id> 更新、DELETE /api/{entity_lower}s/<id> 删除。",
        "type": "backend",
        "priority": 5,
        "estimated_complexity": "medium",
        "dependencies": [],
    },
    {
        "id": "T_LIST",
        "name": "创建{entity}列表页",
        "description": "创建{entity}列表HTML页面，展示所有{entity}的{summary_fields}，支持点击查看详情。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low",
        "dependencies": ["T1"],
    },
    {
        "id": "T_DETAIL",
        "name": "创建{entity}详情页",
        "description": "创建{entity}详情HTML页面，显示完整信息。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low",
        "dependencies": ["T1"],
    },
    {
        "id": "T_CREATE",
        "name": "创建新建{entity}页面",
        "description": "创建新建{entity}的HTML表单页面，包含所有必要输入字段。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low",
        "dependencies": ["T1"],
    },
]

DASHBOARD_APP_TEMPLATE: List[Dict] = [
    {
        "id": "T1",
        "name": "创建数据源后端",
        "description": "创建统计数据API，包括各项指标的聚合查询接口。",
        "type": "backend",
        "priority": 5,
        "estimated_complexity": "medium",
        "dependencies": [],
    },
    {
        "id": "T2",
        "name": "创建仪表盘主页",
        "description": "创建仪表盘HTML页面，显示统计卡片和图表区域。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "medium",
        "dependencies": ["T1"],
    },
]


PATTERN_KEYWORDS = {
    "crud": ["增删改查", "CRUD", "管理系统", "创建", "编辑", "删除", "列表"],
    "dashboard": ["仪表盘", "dashboard", "统计", "图表", "报表", "数据可视化"],
}


def detect_pattern(requirements_text: str) -> Optional[str]:
    """Detect which template pattern best matches the requirements.

    Returns pattern name ('crud', 'dashboard') or None.
    """
    text_lower = requirements_text.lower()
    scores = {}
    for pattern, keywords in PATTERN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[pattern] = score

    if not scores:
        return None
    return max(scores, key=scores.get)


def get_template(pattern: str) -> List[Dict]:
    """Return the template task list for the given pattern."""
    templates = {
        "crud": CRUD_APP_TEMPLATE,
        "dashboard": DASHBOARD_APP_TEMPLATE,
    }
    return templates.get(pattern, [])


def format_template_hint(pattern: str) -> str:
    """Format a template as a hint string to inject into the LLM prompt."""
    template = get_template(pattern)
    if not template:
        return ""

    lines = [f"\n## 参考任务模板 (检测到模式: {pattern})"]
    lines.append("以下是此类应用的典型任务结构，请参考但根据具体需求调整：")
    for t in template:
        lines.append(f"- {t['id']}: [{t['type']}] {t['name']} (complexity: {t['estimated_complexity']}, deps: {t['dependencies']})")
    lines.append("注意：请根据实际需求替换占位符、增减任务，不要照搬模板。\n")
    return "\n".join(lines)
