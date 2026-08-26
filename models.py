from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["vpn", "password", "outlook", "wifi", "access", "other"]
Severity = Literal["low", "medium", "high"]


class SupportRequest(BaseModel):
    """Structured triage output for an employee helpdesk request."""

    category: Category = Field(
        description="Primary helpdesk category: vpn, password, outlook, wifi, access, or other."
    )
    severity: Severity = Field(
        description="Business impact level. Use high for urgent blocked work or security risk."
    )
    summary: str = Field(
        description="One short sentence summarizing the employee's issue."
    )
    requires_ticket: bool = Field(
        description="Whether a human support ticket is likely needed."
    )


def triage_to_text(triage: SupportRequest) -> str:
    """Format triage output for notebooks and Streamlit."""

    return (
        f"Category: {triage.category}\n"
        f"Severity: {triage.severity}\n"
        f"Summary: {triage.summary}\n"
        f"Requires ticket: {triage.requires_ticket}"
    )
