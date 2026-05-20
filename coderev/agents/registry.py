from coderev.agents.base import BaseAgent


def get_agents(client, model: str, max_tokens: int,
               temperature: float, timeout: int) -> dict[str, BaseAgent]:
    from coderev.agents.security import SecurityAgent
    from coderev.agents.performance import PerformanceAgent
    from coderev.agents.logic import LogicAgent
    from coderev.agents.style import StyleAgent

    agent_classes = {
        "security": SecurityAgent,
        "performance": PerformanceAgent,
        "logic": LogicAgent,
        "style": StyleAgent,
    }
    agents = {}
    for name, cls in agent_classes.items():
        agents[name] = cls(
            client=client,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
    return agents
