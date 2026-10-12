"""Typed data models used as the project grows."""

from dataclasses import dataclass
from typing import Literal


Severity = Literal["Low", "Medium", "High", "Critical"]


@dataclass
class Incident:
    title: str
    severity: Severity
    description: str


@dataclass
class InvestigationFinding:
    hypothesis: str
    evidence: list[str]
    confidence: Literal["low", "medium", "high"]
    next_steps: list[str]
