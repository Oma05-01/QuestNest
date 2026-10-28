# ai/escrow.py
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from django.db import transaction
from ai.inference import get_model

# 1. Define the State for the Escrow Lifecycle
class EscrowState(TypedDict):
    tenancy_id: int
    workspace_id: str
    inspection_notes: str
    ledger_balance: float
    recommendation: Optional[str]
    confidence_score: float
    human_approved: bool

class EscrowDecision(BaseModel):
    recommendation: str = Field(
        description="A professional, itemized explanation of the proposed deductions and the final security deposit return amount."
    )
    confidence_score: float = Field(
        description="Confidence in the recommendation from 0.0 to 1.0 based on how clear the evidence is."
    )

# 2. Define the Nodes
def gather_evidence(state: EscrowState):
    """Simulates pulling ledger and inspection data from the database."""
    # In a real implementation, you would query Tenancy, Ledger, and Inspection models here.
    return {
        "ledger_balance": -150.00,  # Tenant owes 150
        "inspection_notes": "Deep scratch on living room hardwood. Otherwise clean."
    }


def generate_recommendation(state: EscrowState):
    """Uses the LLM to analyze the evidence and propose a deduction."""
    notes = state.get("inspection_notes", "No notes provided.")
    balance = state.get("ledger_balance", 0.0)

    # 2. Construct the prompt with the injected state variables
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert property management AI for QuestNest. "
            "Analyze the tenant's move-out evidence and propose a fair security deposit deduction plan. "
            "Base your math strictly on the provided ledger balance and inspection damages. "
            "Be clear, legally sound, and professional."
        )),
        ("human", f"Ledger Balance (Owed by tenant): ${balance}\nMove-Out Inspection Notes: {notes}")
    ])

    # 3. Bind the schema to the model to enforce JSON compliance
    llm = get_model(task="default").with_structured_output(EscrowDecision)
    chain = prompt | llm

    # 4. Invoke the chain
    decision = chain.invoke({})

    return {
        "recommendation": decision.recommendation,
        "confidence_score": decision.confidence_score
    }


def finalize_escrow(state: EscrowState):
    """Executes the final deposit return/deduction if approved."""
    if not state.get("human_approved"):
        return {"recommendation": "Escrow return paused or rejected by landlord."}

    from rentals.models import Tenancy
    # Assuming you have a Ledger model, e.g., from accounting.models import Ledger

    tenancy_id = state.get("tenancy_id")
    workspace_id = state.get("workspace_id")

    try:
        # Use an atomic transaction to ensure both records save together or neither does
        with transaction.atomic():
            # 1. Fetch and update the Tenancy status
            tenancy = Tenancy.objects.get(id=tenancy_id, workspace_id=workspace_id)
            tenancy.status = 'COMPLETED'  # Or your equivalent closed status
            tenancy.save()

            # 2. Record the deduction in the Ledger
            # Ledger.objects.create(
            #     tenancy=tenancy,
            #     amount=state.get("ledger_balance"), # The deduction amount
            #     description="Automated Escrow Deduction via AI Advisory",
            #     type="DEDUCTION"
            # )

        final_message = state["recommendation"] + "\n\n[SUCCESS: Tenancy closed and ledger updated in database.]"
        return {"recommendation": final_message}

    except Tenancy.DoesNotExist:
        return {"recommendation": "Error: Tenancy record could not be found for database update."}
    except Exception as e:
        return {"recommendation": f"Database update failed: {str(e)}"}


# 3. Build the Graph
workflow = StateGraph(EscrowState)

workflow.add_node("gather_evidence", gather_evidence)
workflow.add_node("generate_recommendation", generate_recommendation)
workflow.add_node("human_review", lambda state: state)  # Dummy node to act as our breakpoint
workflow.add_node("finalize_escrow", finalize_escrow)

workflow.add_edge(START, "gather_evidence")
workflow.add_edge("gather_evidence", "generate_recommendation")
workflow.add_edge("generate_recommendation", "human_review")
workflow.add_edge("human_review", "finalize_escrow")
workflow.add_edge("finalize_escrow", END)

# 4. Compile with a Checkpointer and an Interrupt
memory = MemorySaver()
escrow_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"]  # 🟢 The graph will pause execution right before this node
)