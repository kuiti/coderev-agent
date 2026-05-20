from dataclasses import dataclass, field
from openai import OpenAI


@dataclass
class ReviewIssue:
    severity: str  # critical, warning, info
    file: str
    line: int
    message: str
    suggestion: str = ""
    category: str = ""


@dataclass
class ReviewResult:
    agent_name: str
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    error: str | None = None


class BaseAgent:
    name: str = "base"

    SYSTEM_PROMPT = """You are a code review expert. Analyze the provided code and report issues.
For each issue, use this exact format:
  SEVERITY: <critical|warning|info>
  FILE: <filename>
  LINE: <line number>
  MESSAGE: <brief description>
  SUGGESTION: <how to fix>

Only report real issues. Do not praise good code. Be concise."""

    def __init__(self, client: OpenAI, model: str, max_tokens: int = 4096,
                 temperature: float = 0.1, timeout: int = 120):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

    def build_prompt(self, code: str, filename: str) -> str:
        return f"""File: {filename}

```python
{code}
```"""

    def review(self, code: str, filename: str,
               context: str | None = None) -> ReviewResult:
        user_prompt = self.build_prompt(code, filename)
        if context:
            user_prompt = f"Context:\n{context}\n\n{user_prompt}"

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            raw = resp.choices[0].message.content or ""
            return self._parse(raw)
        except Exception as e:
            return ReviewResult(
                agent_name=self.name,
                error=str(e),
                summary=f"Error: {e}",
            )

    def _parse(self, raw: str) -> ReviewResult:
        result = ReviewResult(agent_name=self.name, raw_response=raw)
        for block in raw.split("\n\n"):
            lines = block.strip().split("\n")
            issue = {}
            for line in lines:
                line = line.strip()
                if line.lower().startswith("severity:"):
                    issue["severity"] = line.split(":", 1)[1].strip().lower()
                elif line.lower().startswith("file:"):
                    issue["file"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("line:"):
                    try:
                        issue["line"] = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        issue["line"] = 0
                elif line.lower().startswith("message:"):
                    issue["message"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("suggestion:"):
                    issue["suggestion"] = line.split(":", 1)[1].strip()
            if "severity" in issue and "message" in issue:
                result.issues.append(ReviewIssue(
                    severity=issue.get("severity", "info"),
                    file=issue.get("file", ""),
                    line=issue.get("line", 0),
                    message=issue.get("message", ""),
                    suggestion=issue.get("suggestion", ""),
                    category=self.name,
                ))
        count = len(result.issues)
        result.summary = f"[{self.name}] Found {count} issue(s)" if count else f"[{self.name}] No issues found."
        return result


def create_client(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key)
