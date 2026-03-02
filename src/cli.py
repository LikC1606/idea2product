"""Command-line interface for Idea2Product."""

import sys
import io
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config.settings import get_settings
from src.core.orchestrator import Orchestrator
from src.utils.file_utils import read_json
from src.agents.stage1_requirements.paper_to_project_agent import PaperToProjectAgent
from src.services.llm_service import LLMService

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Idea2Product - Multi-agent system for automated application generation.

    Transform natural language requirements into production-ready web applications.
    """
    pass


@cli.command()
@click.argument("requirement", type=str, required=False)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for generated project",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode: ask clarification questions before generating",
)
def create(requirement: str, output: str = None, interactive: bool = False):
    """
    Create a new web application from a requirement.

    REQUIREMENT: Natural language description of what you want to build.
    (If not provided, will ask interactively)

    Use --interactive / -i to enable interactive question mode.

    Example:
        idea2product create "Build a todo list app"
        idea2product create -i "Build a todo list app"
    """
    try:
        settings = get_settings()

        console.print(Panel.fit(
            f"[bold cyan]Creating project from requirement:[/bold cyan]\n{requirement}",
            title="Idea2Product",
            border_style="cyan",
        ))

        # Create orchestrator
        orchestrator = Orchestrator(settings)

        # Run workflow
        result = orchestrator.run(requirement, interactive=interactive)

        # Handle result (could be ValidatedProject or None if Stage 4 skipped)
        if result is None:
            # Stage 4 was skipped, use default message
            console.print("\n")
            console.print(Panel.fit(
                "[bold green][OK] Project generated successfully![/bold green]\n\n"
                "(Stage 4 skipped for testing)",
                title="Success",
                border_style="green",
            ))
            return

        validated_project = result

        # Success message
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]✓ Project generated successfully![/bold green]\n\n"
            f"Location: {validated_project.repository.structure.root}\n"
            f"Entry point: {validated_project.repository.structure.entry_point}\n\n"
            f"[bold]Deployment instructions:[/bold]\n"
            f"{validated_project.deployment_instructions}",
            title="Success",
            border_style="green",
        ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("project_id", type=str)
def status(project_id: str):
    """
    Check the status of a project.

    PROJECT_ID: The project identifier (e.g., proj_20260213_001)
    """
    try:
        settings = get_settings()
        project_path = settings.projects_dir / project_id

        if not project_path.exists():
            console.print(f"[red]Project not found: {project_id}[/red]")
            sys.exit(1)

        # Load context
        context_file = project_path / "artifacts" / "context.json"
        if not context_file.exists():
            console.print(f"[red]Project context not found: {context_file}[/red]")
            sys.exit(1)

        context_data = read_json(context_file)

        # Display status
        console.print(Panel.fit(
            f"[bold]Project ID:[/bold] {context_data['project_id']}\n"
            f"[bold]Created:[/bold] {context_data['created_at']}\n"
            f"[bold]Updated:[/bold] {context_data['updated_at']}\n"
            f"[bold]Current Stage:[/bold] {context_data['current_stage']}\n"
            f"[bold]Status:[/bold] {context_data.get('validation_status', 'in_progress')}",
            title=f"Project: {project_id}",
            border_style="blue",
        ))

        # Show requirements if available
        if context_data.get("requirements"):
            req = context_data["requirements"]
            console.print("\n[bold]Requirements:[/bold]")
            console.print(f"  Title: {req.get('title', 'N/A')}")
            console.print(f"  Features: {len(req.get('features', []))}")

        # Show engineering plan if available
        if context_data.get("engineering_plan"):
            plan = context_data["engineering_plan"]
            console.print("\n[bold]Engineering Plan:[/bold]")
            console.print(f"  Tasks: {len(plan.get('tasks', []))}")
            console.print(f"  Files: {len(plan.get('file_structure', []))}")

        # Show code repository if available
        if context_data.get("code_repository"):
            repo = context_data["code_repository"]
            console.print("\n[bold]Generated Code:[/bold]")
            console.print(f"  Files: {len(repo.get('files', []))}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def list():
    """List all generated projects."""
    try:
        settings = get_settings()
        projects_dir = settings.projects_dir

        if not projects_dir.exists():
            console.print("[yellow]No projects found[/yellow]")
            return

        # Find all project directories
        projects = [d for d in projects_dir.iterdir() if d.is_dir()]

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        # Create table
        table = Table(title="Generated Projects")
        table.add_column("Project ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Stage", style="yellow")
        table.add_column("Status", style="blue")

        for project_path in sorted(projects, reverse=True):
            project_id = project_path.name
            context_file = project_path / "artifacts" / "context.json"

            if context_file.exists():
                try:
                    context_data = read_json(context_file)
                    created = context_data.get("created_at", "N/A")[:19]  # Truncate datetime
                    stage = f"Stage {context_data.get('current_stage', '?')}"
                    status = context_data.get("validation_status", "in_progress")
                    table.add_row(project_id, created, stage, status)
                except Exception:
                    table.add_row(project_id, "N/A", "N/A", "error")
            else:
                table.add_row(project_id, "N/A", "N/A", "incomplete")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("paper_path", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for generated project",
)
@click.option(
    "--context",
    "-c",
    type=str,
    help="Additional user context (e.g., 'I want to build a mobile app')",
)
@click.option(
    "--generate/--no-generate",
    default=False,
    help="Also generate the full application (default: only analyze paper)",
)
def from_paper(paper_path: str, output: str = None, context: str = None, generate: bool = False):
    """
    Create a project from an academic paper.

    PAPER_PATH: Path to PDF file or text file containing the paper.

    This command analyzes the paper and generates an application idea
    that can be built using the Idea2Product pipeline.

    Example:
        idea2product from-paper paper.pdf
        idea2product from-paper paper.pdf --generate
        idea2product from-paper paper.txt --context "build a mobile app"
    """
    try:
        settings = get_settings()
        llm_service = LLMService.from_settings(settings)

        # Check file exists
        paper_file = Path(paper_path)
        if not paper_file.exists():
            console.print(f"[red]File not found: {paper_path}[/red]")
            sys.exit(1)

        console.print(Panel.fit(
            f"[bold cyan]Analyzing paper:[/bold cyan]\n{paper_file.name}",
            title="Paper to Project",
            border_style="cyan",
        ))

        # Create agent and analyze
        agent = PaperToProjectAgent(llm_service)
        requirements = agent.execute_from_file(str(paper_file), user_context=context)

        # Display results
        console.print("\n[bold green]Generated Application Idea:[/bold green]\n")
        console.print(Panel.fit(
            f"[bold cyan]{requirements.title}[/bold cyan]\n\n"
            f"{requirements.description}",
            border_style="green",
        ))

        console.print("\n[bold]Features:[/bold]")
        for i, feature in enumerate(requirements.features, 1):
            priority_emoji = {
                "must-have": "🔴",
                "should-have": "🟡",
                "nice-to-have": "🟢",
            }.get(feature.priority, "⚪")
            console.print(f"  {i}. {priority_emoji} {feature.name}")
            console.print(f"     {feature.description}")

        if requirements.target_users:
            console.print(f"\n[bold]Target Users:[/bold] {requirements.target_users}")

        if requirements.data_requirements:
            console.print(f"\n[bold]Data Requirements:[/bold] {requirements.data_requirements}")

        # Optionally generate the full project
        if generate:
            console.print("\n[bold cyan]Generating full application...[/bold cyan]")
            orchestrator = Orchestrator(settings)
            # Generate project ID
            from datetime import datetime
            project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = orchestrator.run_from_stage_2(project_id, requirements)
            console.print(f"\n[bold green]Project created successfully![/bold green]")
            console.print(f"Project ID: {result.project_id}")
        else:
            console.print("\n[yellow]To generate the full application, add --generate flag[/yellow]")

    except ImportError as e:
        console.print(f"[bold red]Missing dependency:[/bold red] {e}")
        console.print("Install pypdf: pip install pypdf")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
