"""Pre-defined task templates for common application patterns.

When TaskDivisionAgent detects that the requirements match a known pattern,
these templates serve as a structural hint — the LLM fills in
project-specific details (entity names, fields, page content).
"""

from typing import List, Dict, Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.data_models import Requirements

# Confidence threshold: only use template for fallback when score >= this
PATTERN_CONFIDENCE_THRESHOLD = 2


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

AUTH_APP_TEMPLATE: List[Dict] = [
    {
        "id": "T1",
        "name": "创建认证完整后端",
        "description": "创建用户认证的数据模型和完整后端API，包括：数据模型 User(id(int), username(str), password(str))、POST /api/auth/register 用户注册、POST /api/auth/login 用户登录、POST /api/auth/logout 登出。使用 werkzeug.security 加密密码，session 存储 user_id。",
        "type": "backend",
        "priority": 5,
        "estimated_complexity": "medium",
        "dependencies": [],
    },
    {
        "id": "T2",
        "name": "创建登录和注册页面",
        "description": "创建 login.html 和 register.html，包含用户名密码表单、提交按钮。登录页必须有「没有账号？去注册」链接指向 /register；注册页必须有「已有账号？去登录」链接指向 /login。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low",
        "dependencies": ["T1"],
    },
]

READONLY_APP_TEMPLATE: List[Dict] = [
    {
        "id": "T1",
        "name": "创建数据源后端",
        "description": "创建只读数据API，GET /api/items 获取列表、GET /api/items/<id> 获取详情。",
        "type": "backend",
        "priority": 5,
        "estimated_complexity": "low",
        "dependencies": [],
    },
    {
        "id": "T2",
        "name": "创建展示页面",
        "description": "创建HTML页面，展示数据列表和详情，无编辑功能。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low",
        "dependencies": ["T1"],
    },
]

PATTERN_KEYWORDS = {
    "crud": ["增删改查", "CRUD", "管理系统", "创建", "编辑", "删除", "列表"],
    "dashboard": ["仪表盘", "dashboard", "统计", "图表", "报表", "数据可视化"],
    "auth": ["登录", "login", "注册", "register", "用户认证", "用户登录", "登录功能"],
    "readonly": ["只读", "展示", "查看", "列表展示", "readonly", "read-only"],
}


def detect_pattern(requirements_text: str) -> Optional[str]:
    """Detect which template pattern best matches the requirements.

    Returns pattern name ('crud', 'dashboard') or None.
    """
    pattern, _ = detect_pattern_with_score(requirements_text)
    return pattern


def detect_pattern_with_score(requirements_text: str) -> Tuple[Optional[str], int]:
    """Detect pattern and confidence score. Score >= 2 suggests high confidence."""
    text_lower = requirements_text.lower()
    scores: Dict[str, int] = {}
    for pattern, keywords in PATTERN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[pattern] = score

    if not scores:
        return None, 0
    best = max(scores, key=scores.get)
    return best, scores[best]


def _infer_entity_from_requirements(requirements: "Requirements") -> Tuple[str, str, str, str]:
    """Infer entity name, lowercase, fields, summary_fields from requirements."""
    # Try first feature name or title
    name = "Item"
    if requirements.features:
        raw = requirements.features[0].name
        name = "".join(w.capitalize() for w in raw.split()[:2]) or raw
    elif requirements.title:
        words = requirements.title.replace("应用", "").replace("App", "").strip().split()
        name = "".join(w.capitalize() for w in words[:2]) if words else requirements.title
    lower = name.lower() if len(name) > 1 else name.lower()
    fields = "id(int), name(str), created_at(datetime)"
    summary_fields = "name"
    return name, lower, fields, summary_fields


def build_fallback_tasks(pattern: str, requirements: "Requirements") -> List[Dict]:
    """Build minimal task dicts from template for fallback when LLM fails."""
    template = get_template(pattern)
    if not template:
        return []

    entity, entity_lower, fields, summary_fields = _infer_entity_from_requirements(requirements)
    id_map = {}  # template id -> output id (T1, T2, ...)
    for i, t in enumerate(template):
        id_map[t["id"]] = f"T{i + 1}"

    tasks: List[Dict] = []
    for i, t in enumerate(template):
        tid = id_map[t["id"]]
        name = (t["name"]).format(
            entity=entity,
            entity_lower=entity_lower,
            fields=fields,
            summary_fields=summary_fields,
        )
        desc = (t.get("description", "")).format(
            entity=entity,
            entity_lower=entity_lower,
            fields=fields,
            summary_fields=summary_fields,
        )
        deps = [id_map.get(d, "T1") for d in t.get("dependencies", [])]

        tasks.append({
            "id": tid,
            "name": name,
            "description": desc,
            "type": t.get("type", "backend"),
            "priority": t.get("priority", 5),
            "estimated_complexity": t.get("estimated_complexity", "medium"),
            "dependencies": deps,
        })
    return tasks


def get_template(pattern: str) -> List[Dict]:
    """Return the template task list for the given pattern."""
    templates = {
        "crud": CRUD_APP_TEMPLATE,
        "dashboard": DASHBOARD_APP_TEMPLATE,
        "auth": AUTH_APP_TEMPLATE,
        "readonly": READONLY_APP_TEMPLATE,
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


def format_scheme_pattern_hint(pattern: str) -> str:
    """Format pattern hint for scheme_planning prompt - task structure for task_files coverage."""
    template = get_template(pattern)
    if not template:
        return ""
    lines = [f"\n## 模式提示 (pattern: {pattern})"]
    lines.append("task_files 必须覆盖以下任务对应的文件：")
    for t in template:
        tid = t["id"] if t["id"].startswith("T") else f"T{template.index(t)+1}"
        lines.append(f"- {tid} [{t['type']}]: {t['name']}")
    return "\n".join(lines)


def build_scheme_fallback(
    pattern: str,
    requirements: "Requirements",
    tasks: List[Any],
) -> Dict[str, Any]:
    """Build minimal scheme (task_files, api_specs, pyi_stubs) for fallback when LLM fails.

    Returns a dict compatible with SchemePlanningAgent parse: task_files, api_specs, pyi_stubs, ui_guidelines.
    """
    entity, entity_lower, fields, _ = _infer_entity_from_requirements(requirements)
    task_ids = [t.id for t in tasks] if tasks else ["T1", "T2"]
    if not task_ids:
        task_ids = ["T1", "T2"]

    if pattern == "crud":
        task_files = {
            task_ids[0]: [
                {"path": f"app/models/{entity_lower}.py", "purpose": f"{entity} model", "dependencies": [], "layer": "base"},
                {"path": f"app/routes/{entity_lower}s.py", "purpose": f"{entity} CRUD API", "dependencies": [f"app/models/{entity_lower}.py"], "layer": "assembly"},
                {"path": "app/__init__.py", "purpose": "Flask app factory", "dependencies": [], "layer": "assembly"},
                {"path": "app/database.py", "purpose": "SQLAlchemy db instance", "dependencies": [], "layer": "base"},
            ],
            task_ids[1] if len(task_ids) > 1 else "T2": [
                {"path": "templates/index.html", "purpose": "Main page", "dependencies": [], "layer": None},
            ],
        }
        endpoints = [
            {"path": f"/api/{entity_lower}s", "method": "GET", "description": f"List {entity}s", "response": f"[{{id, ...}}]"},
            {"path": f"/api/{entity_lower}s", "method": "POST", "description": f"Create {entity}", "request": "{...}", "response": "{id, ...}"},
            {"path": f"/api/{entity_lower}s/<id>", "method": "GET", "description": f"Get {entity}", "response": "{...}"},
            {"path": f"/api/{entity_lower}s/<id>", "method": "PUT", "description": f"Update {entity}", "request": "{...}", "response": "{...}"},
            {"path": f"/api/{entity_lower}s/<id>", "method": "DELETE", "description": f"Delete {entity}", "response": "{message}"},
        ]
        frontend_routes = {"/": {"template": "index.html", "description": "Main app"}}
        pyi_stubs = {
            f"app/models/{entity_lower}.py": f"""class {entity}(db.Model):
    __tablename__ = '{entity_lower}s'
    id: int
    created_at: datetime
    def to_dict(self) -> dict: ...
""",
            f"app/routes/{entity_lower}s.py": f"""{entity_lower}s_bp = Blueprint('{entity_lower}s', __name__)
def get_{entity_lower}s() -> list: ...
def create_{entity_lower}(data: dict) -> dict: ...
def get_{entity_lower}(id: int) -> Optional[dict]: ...
def update_{entity_lower}(id: int, data: dict) -> Optional[dict]: ...
def delete_{entity_lower}(id: int) -> Optional[dict]: ...
""",
            "app/__init__.py": "def create_app() -> Flask: ...",
            "app/database.py": "db: SQLAlchemy",
        }
    elif pattern == "dashboard":
        task_files = {
            task_ids[0]: [
                {"path": "app/routes/stats.py", "purpose": "Stats API", "dependencies": [], "layer": "assembly"},
                {"path": "app/__init__.py", "purpose": "Flask app factory", "dependencies": [], "layer": "assembly"},
            ],
            task_ids[1] if len(task_ids) > 1 else "T2": [
                {"path": "templates/index.html", "purpose": "Dashboard", "dependencies": [], "layer": None},
            ],
        }
        endpoints = [
            {"path": "/api/stats", "method": "GET", "description": "Get stats", "response": "{...}"},
        ]
        frontend_routes = {"/": {"template": "index.html", "description": "Dashboard"}}
        pyi_stubs = {
            "app/routes/stats.py": "stats_bp = Blueprint('stats', __name__)\ndef get_stats() -> dict: ...",
            "app/__init__.py": "def create_app() -> Flask: ...",
        }
    elif pattern == "auth":
        task_files = {
            task_ids[0]: [
                {"path": "app/models/user.py", "purpose": "User model", "dependencies": [], "layer": "base"},
                {"path": "app/routes/auth.py", "purpose": "Auth API", "dependencies": ["app/models/user.py"], "layer": "assembly"},
                {"path": "app/__init__.py", "purpose": "Flask app factory", "dependencies": [], "layer": "assembly"},
                {"path": "app/database.py", "purpose": "SQLAlchemy db", "dependencies": [], "layer": "base"},
            ],
            task_ids[1] if len(task_ids) > 1 else "T2": [
                {"path": "templates/login.html", "purpose": "Login", "dependencies": [], "layer": None},
                {"path": "templates/register.html", "purpose": "Register", "dependencies": [], "layer": None},
                {"path": "templates/index.html", "purpose": "Main", "dependencies": [], "layer": None},
            ],
        }
        endpoints = [
            {"path": "/api/auth/register", "method": "POST", "description": "Register", "request": "{username, password}", "response": "{message}"},
            {"path": "/api/auth/login", "method": "POST", "description": "Login", "request": "{username, password}", "response": "{message}", "session_info": {"sets": "user_id"}},
            {"path": "/api/auth/logout", "method": "POST", "description": "Logout", "response": "{message}"},
        ]
        frontend_routes = {
            "/": {"template": "index.html", "description": "Main"},
            "/login": {"template": "login.html", "description": "Login"},
            "/register": {"template": "register.html", "description": "Register"},
        }
        pyi_stubs = {
            "app/models/user.py": "class User(db.Model):\n    id: int\n    username: str\n    password_hash: str\n",
            "app/routes/auth.py": "auth_bp = Blueprint('auth', __name__)\ndef register(username: str, password: str) -> dict: ...\ndef login(username: str, password: str) -> Optional[dict]: ...\ndef logout() -> dict: ...",
            "app/__init__.py": "def create_app() -> Flask: ...",
            "app/database.py": "db: SQLAlchemy",
        }
    elif pattern == "readonly":
        task_files = {
            task_ids[0]: [
                {"path": f"app/routes/{entity_lower}s.py", "purpose": f"{entity} read-only API", "dependencies": [], "layer": "assembly"},
                {"path": "app/__init__.py", "purpose": "Flask app factory", "dependencies": [], "layer": "assembly"},
            ],
            task_ids[1] if len(task_ids) > 1 else "T2": [
                {"path": "templates/index.html", "purpose": "List view", "dependencies": [], "layer": None},
            ],
        }
        endpoints = [
            {"path": f"/api/{entity_lower}s", "method": "GET", "description": f"List {entity}s", "response": "[...]"},
            {"path": f"/api/{entity_lower}s/<id>", "method": "GET", "description": f"Get {entity}", "response": "{...}"},
        ]
        frontend_routes = {"/": {"template": "index.html", "description": "List"}}
        pyi_stubs = {
            f"app/routes/{entity_lower}s.py": f"def get_{entity_lower}s() -> list: ...\ndef get_{entity_lower}(id: int) -> Optional[dict]: ...",
            "app/__init__.py": "def create_app() -> Flask: ...",
        }
    else:
        return {}

    return {
        "task_files": task_files,
        "api_specs": {
            "endpoints": endpoints,
            "frontend_routes": frontend_routes,
            "description": f"REST API for {requirements.title}",
        },
        "pyi_stubs": pyi_stubs,
        "ui_guidelines": {"theme": "modern"},
    }
