import json
from datetime import datetime
from pathlib import Path
from coderev.agents.base import ReviewResult


def generate_report(results: list[ReviewResult], output_format: str = "markdown",
                    output_dir: str = "./reports") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_format == "json":
        path = Path(output_dir) / f"coderev_{ts}.json"
        data = _build_json(results)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
    else:
        path = Path(output_dir) / f"coderev_{ts}.md"
        md = _build_markdown(results)
        path.write_text(md, encoding="utf-8")
        return str(path)


def print_summary(results: list[ReviewResult]):
    from rich.console import Console
    from rich.table import Table

    console = Console()
    all_issues = []
    errors = []
    for r in results:
        if r.error:
            errors.append((r.agent_name, r.error))
        all_issues.extend(r.issues)

    table = Table(title="CodeRev Agent — Review Summary")
    table.add_column("Agent", style="cyan")
    table.add_column("Critical", style="red")
    table.add_column("Warning", style="yellow")
    table.add_column("Info", style="dim")

    agent_stats: dict[str, dict[str, int]] = {}
    for r in results:
        stats = agent_stats.setdefault(r.agent_name, {"critical": 0, "warning": 0, "info": 0})
        for iss in r.issues:
            sev = iss.severity.lower()
            if sev in stats:
                stats[sev] += 1

    for name, stats in agent_stats.items():
        table.add_row(name, str(stats["critical"]), str(stats["warning"]), str(stats["info"]))

    total = agent_stats.values()
    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        str(sum(s["critical"] for s in total)),
        str(sum(s["warning"] for s in total)),
        str(sum(s["info"] for s in total)),
    )

    console.print(table)

    if errors:
        console.print("\n[red]Errors:[/red]")
        for agent, err in errors:
            console.print(f"  [red]×[/red] {agent}: {err}")

    if all_issues:
        console.print("\n[bold]Issues Detail:[/bold]")
        for iss in sorted(all_issues, key=lambda i: (i.severity, i.file, i.line)):
            color = {"critical": "red", "warning": "yellow", "info": "dim"}.get(
                iss.severity.lower(), "dim"
            )
            console.print(
                f"  [{color}]{iss.severity.upper():8s}[/{color}] "
                f"{iss.file}:{iss.line} — {iss.message}"
            )


def _build_json(results: list[ReviewResult]) -> dict:
    data = {
        "generated_at": datetime.now().isoformat(),
        "agents": [],
    }
    for r in results:
        agent_data = {
            "name": r.agent_name,
            "error": r.error,
            "summary": r.summary,
            "issues": [],
        }
        for iss in r.issues:
            agent_data["issues"].append({
                "severity": iss.severity,
                "file": iss.file,
                "line": iss.line,
                "message": iss.message,
                "suggestion": iss.suggestion,
            })
        data["agents"].append(agent_data)
    return data


def _build_markdown(results: list[ReviewResult]) -> str:
    lines = [
        f"# CodeRev Agent — Review Report",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
    ]

    all_issues = []
    errors = []
    for r in results:
        if r.error:
            errors.append((r.agent_name, r.error))
        all_issues.extend(r.issues)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"Total issues: {len(all_issues)}")
    for r in results:
        status = "OK" if not r.error else f"ERROR: {r.error}"
        lines.append(f"- **{r.agent_name}**: {len(r.issues)} issues ({status})")
    lines.append("")

    if errors:
        lines.append("## Errors")
        lines.append("")
        for agent, err in errors:
            lines.append(f"- **{agent}**: {err}")
        lines.append("")

    if all_issues:
        lines.append("## Issues")
        lines.append("")
        for iss in sorted(all_issues, key=lambda i: (0 if i.severity == "critical" else 1 if i.severity == "warning" else 2, i.file, i.line)):
            icon = {"critical": "🔴", "warning": "🟡", "info": "⚪"}.get(
                iss.severity.lower(), "⚪"
            )
            lines.append(f"### {icon} [{iss.severity.upper()}] {iss.file}:{iss.line}")
            lines.append(f"- **Agent**: {iss.category}")
            lines.append(f"- **Message**: {iss.message}")
            lines.append(f"- **Suggestion**: {iss.suggestion}")
            lines.append("")
    else:
        lines.append("## No Issues Found")
        lines.append("")
        lines.append("The review found no issues. Good work!")

    return "\n".join(lines)
