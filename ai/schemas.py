# ai/schemas.py
from typing import Literal
from pydantic import BaseModel, Field

class TriageResult(BaseModel):
    category: Literal["plumbing", "electrical", "hvac", "structural", "appliance", "general"] = Field(
        description="The primary classification of the maintenance complaint."
    )
    urgency: Literal["low", "medium", "high", "urgent"] = Field(
        description="Priority level based on potential structural damage, health risks, or uninhabitablity."
    )
    suggested_title: str = Field(
        description="Concise, standardized 5-8 word title for the ticket."
    )
    summary: str = Field(
        description="Clean, factual summary stripping emotional language and highlighting technical impact."
    )
    actionable_steps: list[str] = Field(
        description="Recommended immediate containment steps for the tenant or property manager."
    )
    requires_emergency_dispatch: bool = Field(
        description="True if the issue poses immediate risk to safety or major structural loss (e.g. active main pipe burst, exposed high-voltage wiring)."
    )
    is_landlord_responsible: bool = Field(
        description="True if the landlord is responsible for this repair based on the lease, False if the tenant is responsible.")

    responsibility_reasoning: str = Field(
        description="A brief explanation citing the lease context to justify who is responsible.")

    severity: str = Field(description="Explanation of the severity and potential damage.")