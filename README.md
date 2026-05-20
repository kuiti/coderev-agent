# CodeRev Agent

AI-powered multi-agent code review tool. Four specialized agents review your code in parallel — security, performance, logic, and style — then aggregate their findings into a structured report.

Built for the Xiaomi MiMo ecosystem.

## Architecture

```
coderev review app/

┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│ Security    │    │ Performance  │    │ Logic       │    │ Style       │
│ Agent       │    │ Agent        │    │ Agent       │    │ Agent       │
│ SQL注入     │    │ N+1查询      │    │ 空值检查    │    │ 命名规范    │
│ 命令注入    │    │ 循环IO       │    │ 边界条件    │    │ 嵌套深度    │
│ 密钥泄露    │    │ 内存泄漏     │    │ 异常处理    │    │ DRY原则     │
└─────┬───────┘    └──────┬───────┘    └──────┬──────┘    └──────┬──────┘
      │                   │                   │                  │
      └───────────────────┴───────────────────┴──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Reporter   │
                    │  MD / JSON  │
                    └─────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create config
python main.py config
# Edit config.yaml with your MiMo API key

# Review a file
python main.py review app/main.py

# Review a directory
python main.py review src/

# Review git changes
python main.py diff

# Only security + logic agents
python main.py review app/ --agents security,logic

# JSON output
python main.py review app/ --output json
```

## Review Dimensions

| Agent | Checks |
|---|---|
| **security** | SQL injection, command injection, hardcoded secrets, unsafe deserialization, path traversal |
| **performance** | N+1 queries, blocking IO, missing generators, repeated computation, memory leaks |
| **logic** | Null checks, off-by-one, exception swallowing, race conditions, division by zero |
| **style** | Long functions, deep nesting, poor naming, missing type hints, duplicate code |

## Config

```yaml
# config.yaml
api:
  base_url: "https://api.xiaomimimo.com/v1"
  api_key: "your-key"
  model: "mimo-v2.5-pro"
```

## Use Cases

- **Pre-commit review**: `python main.py diff` before committing
- **CI integration**: Run in GitHub Actions / GitLab CI
- **Onboarding**: Review legacy code to understand its issues
- **Pair programming**: Second set of eyes on new features
