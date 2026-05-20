from pathlib import Path
import yaml

CONFIG_PATHS = [
    Path("config.yaml"),
    Path.home() / ".coderev" / "config.yaml",
]


def _find_config() -> Path | None:
    for p in CONFIG_PATHS:
        if p.exists():
            return p
    return None


def load_config(path: str | None = None) -> dict:
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config not found: {p}")
    else:
        p = _find_config()
        if p is None:
            raise FileNotFoundError(
                "No config.yaml found in current dir or ~/.coderev/"
            )
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_config(cfg: dict) -> dict:
    return cfg["api"]


def get_review_config(cfg: dict) -> dict:
    return cfg.get("review", {})


def get_output_config(cfg: dict) -> dict:
    return cfg.get("output", {})
