import os
import django

# Setup Django Environment (useful if we add ORM calls later)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questnest.settings')
django.setup()

from ai.escrow import escrow_app

def run_escrow_test():
    print("-" * 50)
    print("Starting Phase 4: Escrow Advisory Interrupt Test")
    print("-" * 50)

    # 1. Define the thread config to track memory state
    config = {"configurable": {"thread_id": "escrow_test_001"}}

    # 2. Define the initial state payload
    initial_state = {
        "tenancy_id": 38,
        "workspace_id": "test-workspace-id",
        "human_approved": False
    }

    print("\n▶️ [STEP 1] Starting the Escrow Graph...")
    # Invoke the graph. It will run gather_evidence -> generate_recommendation -> PAUSE
    escrow_app.invoke(initial_state, config)

    # 3. Inspect the paused state
    state = escrow_app.get_state(config)
    print("\n⏸️ [STEP 2] Graph Paused for Human-in-the-Loop!")
    print(f"AI Recommendation: {state.values.get('recommendation')}")
    print(f"Confidence Score:  {state.values.get('confidence_score')}")
    print(f"Next Node in Queue: {state.next}")  # Should show ('human_review',)

    if 'human_review' not in state.next:
        print("❌ Error: Graph did not pause at the expected breakpoint.")
        return

    print("\n👤 [STEP 3] Simulating Landlord Approval...")
    # 4. Update the state with the human's decision (True)
    escrow_app.update_state(config, {"human_approved": True})

    print("\n▶️ [STEP 4] Resuming the Escrow Graph...")
    # 5. Resume execution by passing None as the input
    escrow_app.invoke(None, config)

    # 6. Check the final finalized state
    final_state = escrow_app.get_state(config)
    print("\n✅ [STEP 5] Escrow Workflow Complete!")
    print(f"Final Recommendation: {final_state.values.get('recommendation')}")
    print(f"Status Finalized:     {final_state.values.get('human_approved')}")

if __name__ == "__main__":
    run_escrow_test()