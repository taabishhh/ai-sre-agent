from typing import TypedDict


class Diagnosis(TypedDict):
    root_cause: str
    evidence: list[str]
    confidence: str
    affected_resources: list[str]


class RemediationPlan(TypedDict):
    action: str
    params: dict
    rationale: str
    risk_level: str
    expected_outcome: str


# everything the graph passes from one step to the next
class AgentState(TypedDict, total=False):
    namespace: str
    incident_hint: str
    telemetry_transcript: str
    diagnosis: Diagnosis
    proposal: RemediationPlan
    approval_status: str
    approver_note: str
    execution_result: str
    executed: bool
    summary_markdown: str
    started_at: float
    finished_at: float
