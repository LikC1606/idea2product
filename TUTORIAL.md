# Idea2Product Tutorial

A step-by-step guide to using Idea2Product for generating applications from natural language requirements.

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [First Project](#2-first-project)
3. [Understanding the Pipeline](#3-understanding-the-pipeline)
4. [Generated Project Structure](#4-generated-project-structure)
5. [Running Generated Apps](#5-running-generated-apps)
6. [CLI Commands Reference](#6-cli-commands-reference)
7. [Configuration Tips](#7-configuration-tips)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Environment Setup

### Step 1.1: Install Dependencies

```bash
# Clone and enter project
git clone <repo-url>
cd idea2product

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Step 1.2: Configure API Access

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your OpenAI API credentials:

```env
# Required - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxx

# Optional - Custom API endpoint (useful for testing)
OPENAI_BASE_URL=https://api.openai.com/v1

# Model selection
OPENAI_MODEL=gpt-4o
OPENAI_VLM_MODEL=gpt-4o
```

> **Tip**: You can also use compatible API providers like OpenRouter, Azure OpenAI, or custom endpoints by changing `OPENAI_BASE_URL`.

---

## 2. First Project

### Step 2.1: Create a Simple App

Let's generate a simple calculator app:

```bash
python -m src.cli create "Build a calculator app with add, subtract, multiply, and divide functions"
```

### Step 2.2: Watch the Pipeline Execute

You'll see output like:

```
[Stage 1] Requirements Gathering
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 I need to clarify a few details about your calculator app:

1. What type of calculator do you want?
   - Basic (add, subtract, multiply, divide)
   - Scientific (trigonometry, logarithms, etc.)
   - Custom

> Basic

[Stage 2] Technical Planning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Creating technical specifications...
   - Task breakdown: 5 tasks
   - Algorithm analysis: Complete
   - Architecture: MVC pattern

[Stage 3] Code Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 Generating code...
   ✓ calculator.py (main app)
   ✓ operations.py (calculation logic)
   ✓ ui.py (user interface)
   ✓ tests/test_calculator.py

[Stage 4] Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Running tests...
   ✓ test_calculator.py::test_add - PASSED
   ✓ test_calculator.py::test_subtract - PASSED

✓ Project generated successfully!
Location: data/projects/proj_20260214_xxx/generated/
```

### Step 2.3: Run Your App

```bash
cd data/projects/proj_20260214_xxx/generated/calculator_app
python ui.py
```

A tkinter window will appear with your working calculator!

---

## 3. Understanding the Pipeline

### Stage 1: Requirements Gathering

The **Interaction Agent** clarifies your requirements through dialogue:

- Asks clarifying questions
- Identifies missing information
- Ensures complete understanding before proceeding

**Example dialogue:**
```
User: "Build a todo app"
Agent: "Great! I have a few questions:
  1. Should items persist after closing the app (database/file)?
  2. Do you need categories or tags for todos?
  3. Any specific platform (web, desktop, mobile)?"
```

### Stage 2: Technical Planning

Three agents create the engineering specification:

| Agent | Purpose |
|-------|---------|
| Task Division Agent | Breaks requirements into actionable tasks |
| Algorithm Analysis Agent | Designs data structures and algorithms |
| Scheme Planning Agent | Creates architectural plan |

Output: `plan.json` with:
- Task breakdown
- File structure
- API definitions
- Database schema (if needed)

### Stage 3: Code Generation

Three agents produce working code:

| Agent | Purpose |
|-------|---------|
| Code Generation Agent | Writes the application code |
| Code Memory Agent | Leverages past patterns |
| Code Mining Agent | Retrieves relevant external code |

**Key features:**
- Dependency resolution (auto-generates missing imports)
- Creates `__init__.py` files
- Generates pytest tests
- Produces `.pyi` interface files

### Stage 4: Validation

Three agents validate and fix:

| Agent | Purpose |
|-------|---------|
| BDD Testing Agent | Runs Gherkin-style test scenarios |
| Visual Verification Agent | Uses GPT-4o Vision to verify UI |
| Fine-tuning Agent | Automatically fixes failing tests |

**Automatic fixes include:**
- Syntax errors
- Import mismatches
- Missing entry points
- Test failures

---

## 4. Generated Project Structure

A typical generated project:

```
data/projects/proj_20260214_161539_5cb02d/
├── context.json              # Original requirements
├── plan.json                 # Technical specifications
├── metadata.json             # Project metadata
└── generated/
    └── calculator_app/
        ├── __init__.py       # Package init
        ├── app.py            # Main application
        ├── config.py         # Configuration
        ├── models.py         # Data models
        ├── operations.py     # Business logic
        ├── ui.py             # User interface
        └── tests/
            ├── __init__.py
            └── test_calculator.py
```

### Key Files

| File | Description |
|------|-------------|
| `context.json` | Original requirements and clarifications |
| `plan.json` | Technical specifications and task list |
| `generated/app.py` | Main entry point |
| `generated/tests/` | Auto-generated pytest tests |

---

## 5. Running Generated Apps

### Web Applications (Flask/FastAPI)

```bash
cd data/projects/{project_id}/generated

# For Flask apps
pip install flask
python -m flask run
# or
python app.py

# For FastAPI apps
pip install fastapi uvicorn
uvicorn app:app --reload
```

### Desktop Applications (Tkinter/PyQt)

```bash
cd data/projects/{project_id}/generated/app_name
python ui.py
```

### CLI Applications

```bash
cd data/projects/{project_id}/generated/app_name
python main.py
```

---

## 6. CLI Commands Reference

### Create Project

```bash
# Interactive mode (default) - asks clarifying questions
python -m src.cli create "Build a weather app"

# Non-interactive mode - skips questions
python -m src.cli create "Build a weather app" --no-interactive
```

### List Projects

```bash
# List all projects
python -m src.cli list
```

Output:
```
📁 All Projects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
proj_20260214_142450_d87387  Todo App        2026-02-14 14:24  ✓
proj_20260214_152357_f0b339  Calculator      2026-02-14 15:23  ✓
proj_20260214_161539_5cb02d  Weather App     2026-02-14 16:15  ✗
```

### Check Status

```bash
python -m src.cli status proj_20260214_xxx
```

### View Details

```bash
python -m src.cli details proj_20260214_xxx
```

Shows:
- Requirements
- Generated files
- Test results
- Errors (if any)

---

## 7. Configuration Tips

### Using Custom API Providers

```env
# OpenRouter (many model options)
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-xxxxx

# Azure OpenAI
OPENAI_BASE_URL=https://your-resource.openai.azure.com/
OPENAI_API_KEY=your-azure-key
```

### Adjusting Model Behavior

```env
# More deterministic outputs
TEMPERATURE=0.1

# More creative outputs
TEMPERATURE=0.9

# Longer responses
MAX_TOKENS=8192
```

### Performance Tuning

```env
# Faster test execution
SANDBOX_TIMEOUT=60

# More fix attempts
MAX_FIX_ATTEMPTS=3
```

---

## 8. Troubleshooting

### API Errors

**401 Unauthorized**
- Check your `OPENAI_API_KEY` in `.env`
- Ensure `.env` takes precedence over environment variables

**Rate Limit Exceeded**
- Add to `.env`: `OPENAI_BASE_URL` with a provider with higher limits
- Or upgrade your OpenAI plan

### Generation Errors

**"Module not found"**
- The system attempts to resolve dependencies automatically
- Check if the required package is installed: `pip install package-name`

**Tests failing**
- The Fine-tuning Agent attempts automatic fixes
- Check `generated/tests/` and manually fix if needed

### Running Issues

**App won't start**
- Check the generated app's requirements: `pip install -r requirements.txt`
- Verify Python version compatibility

---

## Examples

### Example 1: Todo List App

```bash
python -m src.cli create "A todo list app with add, delete, complete, and filter by status"
```

### Example 2: Weather Widget

```bash
python -m src.cli create "A weather widget showing current temperature and forecast for user input city"
```

### Example 3: Blog Platform

```bash
python -m src.cli create "A simple blog with create post, view posts, and comment features"
```

---

## Next Steps

- Explore the [Architecture](docs/architecture.md) for deeper understanding
- Check [Agent Specifications](docs/agent_specifications.md) for implementation details
- Contribute by adding new templates or improving agents
