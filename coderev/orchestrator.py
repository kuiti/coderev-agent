from concurrent.futures import ThreadPoolExecutor, as_completed
from coderev.agents.base import BaseAgent, ReviewResult
from coderev.parser import parse_file, build_call_graph, build_context, collect_files


def run_review(
    target: str,
    agents: dict[str, BaseAgent],
    agent_filter: list[str] | None = None,
    extensions: tuple[str, ...] = (".py",),
    progress_callback=None,
) -> list[ReviewResult]:
    files = collect_files(target, extensions)
    if not files:
        return []

    call_graph = build_call_graph(files)
    selected = _select_agents(agents, agent_filter)
    all_results: list[ReviewResult] = []

    for filepath in files:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            code = f.read()
        info = parse_file(filepath)
        context = build_context(info, call_graph)

        futures = {}
        with ThreadPoolExecutor(max_workers=len(selected)) as executor:
            for name, agent in selected.items():
                fut = executor.submit(agent.review, code, filepath, context)
                futures[fut] = name

            for fut in as_completed(futures):
                name = futures[fut]
                if progress_callback:
                    progress_callback(name, filepath)
                try:
                    result = fut.result()
                except Exception as e:
                    result = ReviewResult(
                        agent_name=name,
                        error=str(e),
                        summary=f"[{name}] Failed: {e}",
                    )
                all_results.append(result)

    return all_results


def _select_agents(agents: dict[str, BaseAgent],
                   agent_filter: list[str] | None) -> dict[str, BaseAgent]:
    if agent_filter:
        return {k: v for k, v in agents.items() if k in agent_filter}
    return dict(agents)
