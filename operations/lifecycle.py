from operations.services.event_service import log_event
from workspaces.models import Workspace # 🟢 Updated import


class LifecycleMixin:
    ALLOWED_TRANSITIONS = {}

    # Type hints tell IDE these attributes exist in subclasses
    status: str
    workspace: "Workspace" # 🟢 Updated type hint

    def transition_to(self, new_status, *, actor=None, event_type=None, metadata=None):
        # 1️⃣ Validate allowed transition
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")

        old_status = self.status
        self.status = new_status
        self.save(update_fields=['status']) # 🟢 Minor optimization: only save the status field

        # 2️⃣ Prepare metadata
        event_metadata = {"from": old_status, "to": new_status}
        if metadata:
            event_metadata.update(metadata)

        # 3️⃣ Log event (Event Rules are now triggered asynchronously inside log_event!)
        if event_type:
            log_event(
                workspace=self.workspace, # 🟢 Passing the workspace context
                actor=actor,
                event_type=event_type,
                object_type=self.__class__.__name__,
                object_id=str(self.id),
                metadata=event_metadata
            )

        return self