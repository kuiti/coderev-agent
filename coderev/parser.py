import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionInfo:
    name: str
    file: str
    lineno: int
    end_lineno: int
    calls: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


@dataclass
class FileInfo:
    path: str
    imports: list[str] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)


def parse_file(filepath: str) -> FileInfo:
    """Parse a Python file and extract structure info."""
    path = Path(filepath)
    with open(filepath, encoding="utf-8", errors="replace") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return FileInfo(path=filepath)

    info = FileInfo(path=filepath)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                info.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                info.imports.append(f"{module}.{alias.name}")
        elif isinstance(node, ast.FunctionDef):
            func = FunctionInfo(
                name=node.name,
                file=filepath,
                lineno=node.lineno,
                end_lineno=node.end_lineno or node.lineno,
                decorators=[_decorator_name(d) for d in node.decorator_list],
            )
            func.calls = _extract_calls(node)
            info.functions.append(func)
        elif isinstance(node, ast.ClassDef):
            info.classes.append(node.name)

    return info


def build_call_graph(files: list[str]) -> dict[str, list[str]]:
    """Build a call graph mapping function -> functions it calls."""
    graph: dict[str, list[str]] = {}
    for fp in files:
        info = parse_file(fp)
        for func in info.functions:
            key = f"{info.path}:{func.name}"
            graph[key] = func.calls
    return graph


def find_callers(call_graph: dict[str, list[str]], target: str) -> list[str]:
    """Find all functions that call the target function."""
    callers = []
    for func, calls in call_graph.items():
        if target in calls or any(c.endswith(f".{target}") for c in calls):
            callers.append(func)
    return callers


def collect_files(target: str, extensions: tuple[str, ...] = (".py",)) -> list[str]:
    """Collect all matching files from a target path (file or directory)."""
    p = Path(target)
    if not p.exists():
        return []
    if p.is_file():
        return [str(p)] if p.suffix in extensions else []
    files = []
    for ext in extensions:
        files.extend(str(fp) for fp in p.rglob(f"*{ext}"))
    return sorted(files)


def _decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return "?"


def _extract_calls(node: ast.FunctionDef) -> list[str]:
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return sorted(set(calls))


def build_context(parse_result: FileInfo, call_graph: dict[str, list[str]]) -> str:
    """Build a context string for review agents."""
    parts = [f"File: {parse_result.path}"]
    if parse_result.imports:
        parts.append(f"Imports: {', '.join(parse_result.imports[:20])}")
    if parse_result.classes:
        parts.append(f"Classes: {', '.join(parse_result.classes)}")
    if parse_result.functions:
        parts.append(f"Functions ({len(parse_result.functions)}):")
        for f in parse_result.functions:
            key = f"{parse_result.path}:{f.name}"
            callees = call_graph.get(key, [])
            parts.append(
                f"  - {f.name}() L{f.lineno}-{f.end_lineno}"
                + (f" -> calls: {', '.join(callees)}" if callees else "")
            )
    return "\n".join(parts)
