import argparse
import sys
from pathlib import Path
from coderev.config import load_config, get_api_config, get_output_config, get_review_config
from coderev.agents.base import create_client
from coderev.agents.registry import get_agents
from coderev.orchestrator import run_review
from coderev.reporter import generate_report, print_summary
from coderev.parser import collect_files


def cmd_review(args):
    cfg = load_config(args.config)
    api = get_api_config(cfg)
    out = get_output_config(cfg)
    rev = get_review_config(cfg)

    client = create_client(api["base_url"], api["api_key"])

    agents = get_agents(
        client=client,
        model=args.model or api["model"],
        max_tokens=args.max_tokens or api.get("max_tokens", 4096),
        temperature=api.get("temperature", 0.1),
        timeout=api.get("timeout", 120),
    )

    agent_filter = None
    if args.agents:
        agent_filter = [a.strip() for a in args.agents.split(",")]

    agent_names = list(agent_filter or agents.keys())
    print(f"🔍 CodeRev Agent — Reviewing: {args.target}")
    print(f"   Agents: {', '.join(agent_names)}")

    def _progress(agent, filepath):
        fname = Path(filepath).name
        print(f"   ✓ [{agent}] done → {fname}")

    results = run_review(
        target=args.target,
        agents=agents,
        agent_filter=agent_filter,
        extensions=tuple(rev.get("extensions", [".py"])),
        progress_callback=_progress,
    )

    if not results:
        print("No files found to review.")
        return

    output_format = args.output or out.get("format", "markdown")
    output_dir = args.output_dir or out.get("dir", "./reports")
    path = generate_report(results, output_format=output_format, output_dir=output_dir)

    print()
    print_summary(results)
    print(f"\n📄 Report saved: {path}")


def cmd_diff(args):
    import subprocess
    import tempfile

    cfg = load_config(args.config)
    api = get_api_config(cfg)

    try:
        diff = subprocess.check_output(
            ["git", "diff"], text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.output}")
        sys.exit(1)

    if not diff.strip():
        print("No changes to review (git diff is empty).")
        return

    client = create_client(api["base_url"], api["api_key"])
    agents = get_agents(
        client=client,
        model=args.model or api["model"],
        max_tokens=args.max_tokens or api.get("max_tokens", 4096),
        temperature=api.get("temperature", 0.1),
        timeout=api.get("timeout", 120),
    )

    agent_filter = None
    if args.agents:
        agent_filter = [a.strip() for a in args.agents.split(",")]

    from coderev.agents.base import ReviewResult

    with tempfile.NamedTemporaryFile(suffix=".diff", mode="w", delete=False,
                                     encoding="utf-8") as f:
        f.write(diff)
        tmp = f.name

    selected = {k: v for k, v in agents.items()
                if not agent_filter or k in agent_filter} if agent_filter else agents

    agent_names = list(selected.keys())
    print(f"🔍 CodeRev Agent — Reviewing git diff")
    print(f"   Agents: {', '.join(agent_names)}")

    results = []
    for name, agent in selected.items():
        result = agent.review(diff, "git diff")
        print(f"   ✓ [{name}] done")
        results.append(result)

    output_format = args.output or "markdown"
    path = generate_report(results, output_format=output_format)

    print()
    print_summary(results)
    print(f"\n📄 Report saved: {path}")


def cmd_config(args):
    import shutil
    src = Path(__file__).parent.parent / "config.yaml"
    dst = Path("config.yaml")
    if dst.exists():
        print(f"config.yaml already exists at {dst.absolute()}")
        return
    shutil.copy(src, dst)
    print(f"Created config.yaml at {dst.absolute()}")
    print("Edit it to set your MiMo API key and preferences.")


def main():
    parser = argparse.ArgumentParser(
        prog="coderev",
        description="CodeRev Agent — AI-powered multi-agent code review",
    )
    sub = parser.add_subparsers(dest="command")

    p_review = sub.add_parser("review", help="Review files or directories")
    p_review.add_argument("target", help="File or directory to review")
    p_review.add_argument("--agents", "-a", help="Comma-separated agent names (security,performance,logic,style)")
    p_review.add_argument("--output", "-o", choices=["markdown", "json"], help="Output format")
    p_review.add_argument("--output-dir", "-d", help="Report output directory")
    p_review.add_argument("--model", "-m", help="Model name override")
    p_review.add_argument("--max-tokens", type=int, help="Max tokens override")
    p_review.add_argument("--config", "-c", help="Config file path")

    p_diff = sub.add_parser("diff", help="Review staged/unstaged git changes")
    p_diff.add_argument("--agents", "-a", help="Comma-separated agent names")
    p_diff.add_argument("--output", "-o", choices=["markdown", "json"], help="Output format")
    p_diff.add_argument("--model", "-m", help="Model name override")
    p_diff.add_argument("--max-tokens", type=int, help="Max tokens override")
    p_diff.add_argument("--config", "-c", help="Config file path")

    p_config = sub.add_parser("config", help="Create default config.yaml")

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.command == "review":
        cmd_review(args)
    elif args.command == "diff":
        cmd_diff(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
