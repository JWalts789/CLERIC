"""Command-line interface for C.L.E.R.I.C. research pipeline."""

import argparse
import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode/emoji output
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.markdown import Markdown

from cleric.config import Config
from cleric.orchestrator import ResearchPipeline, PipelineResult
from cleric.output.mermaid import MermaidGenerator
from cleric.output.report import ReportGenerator


console = Console(force_terminal=True)

STAGE_LABELS = {
    "bias_detection": ("🛡️", "Bias Detection", "Analyzing query for bias..."),
    "research": ("🔎", "Research", "Gathering multi-perspective sources..."),
    "fact_checking": ("✅", "Fact Checking", "Independently verifying claims..."),
    "devils_advocate": ("😈", "Devil's Advocate", "Challenging findings..."),
    "synthesis": ("📝", "Synthesis", "Producing balanced report..."),
    "evaluation": ("📊", "Evaluation", "Scoring research quality..."),
}


def main():
    parser = argparse.ArgumentParser(
        prog="cleric",
        description="Multi-agent research system for unbiased, auditable research.",
    )
    parser.add_argument("query", nargs="?", help="Research query to investigate")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    parser.add_argument("--no-mermaid", action="store_true", help="Skip Mermaid diagram generation")
    parser.add_argument("--no-report", action="store_true", help="Skip markdown report generation")
    parser.add_argument("--output-dir", type=str, help="Override output directory")
    parser.add_argument("--model", type=str, help="Override Claude model")
    parser.add_argument("--verbose", action="store_true", help="Show detailed agent output")

    args = parser.parse_args()

    if not args.query:
        console.print(Panel(
            "[bold]C.L.E.R.I.C.[/bold] — Cross-Lateral Evidence Review for Information Clarity\n\n"
            "Usage: cleric \"Your research question here\"\n\n"
            "Options:\n"
            "  --json         Output raw JSON\n"
            "  --no-mermaid   Skip diagram generation\n"
            "  --no-report    Skip report generation\n"
            "  --verbose      Show detailed agent output\n"
            "  --model MODEL  Override Claude model\n"
            "  --output-dir   Override output directory",
            title="C.L.E.R.I.C.",
            border_style="blue",
        ))
        sys.exit(0)

    # Load config
    config = Config.from_env()
    if args.model:
        config.model = args.model
    if args.output_dir:
        config.output_dir = args.output_dir

    # Banner
    console.print()
    console.print(Panel(
        f"[bold]{args.query}[/bold]",
        title="[bold blue]C.L.E.R.I.C. Research Pipeline[/bold blue]",
        border_style="blue",
    ))
    console.print()

    # Run pipeline with progress display
    pipeline = ResearchPipeline(config)
    current_task_id = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall = progress.add_task("[bold]Running research pipeline...", total=6)

        def on_start(stage: str):
            nonlocal current_task_id
            icon, label, desc = STAGE_LABELS.get(stage, ("", stage, "Processing..."))
            current_task_id = progress.add_task(f"  {icon} {desc}", total=None)

        def on_complete(stage: str, result):
            nonlocal current_task_id
            if current_task_id is not None:
                icon, label, _ = STAGE_LABELS.get(stage, ("", stage, ""))
                tokens = result.tokens_used.get("input", 0) + result.tokens_used.get("output", 0)
                progress.update(current_task_id, description=f"  {icon} {label} [green]✓[/green] ({tokens:,} tokens)")
                progress.stop_task(current_task_id)
            progress.advance(overall)

        pipeline.on_stage_start(on_start)
        pipeline.on_stage_complete(on_complete)

        result = pipeline.run(args.query)
        progress.update(overall, description="[bold green]Pipeline complete!")

    console.print()

    # JSON output mode
    if args.json:
        console.print_json(json.dumps(result.to_dict(), indent=2, default=str))
        return

    # Display results
    _display_results(result, args.verbose)

    # Generate outputs
    generated_files = []

    if not args.no_mermaid:
        mermaid = MermaidGenerator(config.output_dir)
        diagrams = mermaid.generate_all(result)
        for name, path in diagrams.items():
            generated_files.append(("Mermaid", name, str(path)))

    if not args.no_report:
        reporter = ReportGenerator(config.output_dir)
        report_path = reporter.generate(result)
        generated_files.append(("Report", "Full Report", str(report_path)))

    # Save raw JSON
    json_path = Path(config.output_dir) / f"{Path(generated_files[0][2]).stem.rsplit('_', 1)[0]}_raw.json" if generated_files else None
    if json_path:
        json_path.write_text(json.dumps(result.to_dict(), indent=2, default=str), encoding="utf-8")
        generated_files.append(("JSON", "Raw Data", str(json_path)))

    # Show generated files
    if generated_files:
        console.print()
        table = Table(title="Generated Files", border_style="blue")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Path", style="dim")
        for ftype, fname, fpath in generated_files:
            table.add_row(ftype, fname, fpath)
        console.print(table)

    console.print()


def _display_results(result: PipelineResult, verbose: bool):
    """Display research results in the terminal."""
    # Bias Analysis Summary
    bias = result.stages.get("bias_detection")
    if bias:
        score = bias.data.get("bias_score", "?")
        color = "green" if isinstance(score, (int, float)) and score <= 3 else "yellow" if isinstance(score, (int, float)) and score <= 6 else "red"
        console.print(Panel(
            f"[bold]Bias Score:[/bold] [{color}]{score}/10[/{color}]\n"
            f"[bold]Neutral Queries:[/bold] {', '.join(bias.data.get('neutral_queries', ['N/A']))}",
            title="🛡️ Bias Analysis",
            border_style=color,
        ))

    # Evaluation Summary
    eval_stage = result.stages.get("evaluation")
    if eval_stage:
        scores = eval_stage.data.get("scores", {})
        grade = eval_stage.data.get("grade", "?")

        table = Table(title=f"📊 Research Quality: Grade {grade}", border_style="blue")
        table.add_column("Dimension", style="white")
        table.add_column("Score", justify="center")
        table.add_column("Bar", style="bold")

        for metric, score in scores.items():
            if isinstance(score, (int, float)):
                label = metric.replace("_", " ").title()
                bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                color = "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
                table.add_row(label, f"[{color}]{score:.0%}[/{color}]", f"[{color}]{bar}[/{color}]")

        console.print(table)

    # Final Report
    console.print()
    console.print(Panel(
        Markdown(result.final_report[:3000] if result.final_report else "*No report generated*"),
        title="📝 Synthesized Report",
        border_style="purple",
    ))

    # Verbose: show all stage outputs
    if verbose:
        for name, stage in result.stages.items():
            icon = STAGE_LABELS.get(name, ("", "", ""))[0]
            console.print(Panel(
                stage.content[:2000],
                title=f"{icon} {name}",
                border_style="dim",
            ))

    # Token summary
    tokens = result.total_tokens
    console.print(f"\n[dim]Total tokens: {tokens['input'] + tokens['output']:,} | Duration: {result.duration_seconds:.1f}s[/dim]")


if __name__ == "__main__":
    main()
