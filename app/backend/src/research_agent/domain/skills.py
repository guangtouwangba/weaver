from dataclasses import dataclass


@dataclass
class Skill:
    """
    Represents a specialized capability or protocol that can be injected into an agent.
    """

    name: str
    description: str
    instruction: str  # The prompt injection for this skill
