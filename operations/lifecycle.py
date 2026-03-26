from operations.services.event_service import log_event
from organisations.models import Organisation


class LifecycleMixin:
    ALLOWED_TRANSITIONS = {}

    # Type hints tell IDE these attributes exist in subclasses
    status: str
    organisation: "Organisation"

    def save(self, *args, **kwargs):
        """This is just a stub for static analysis; actual save comes from Django Model"""
        pass

    def transition_to(self, new_status, *, actor=None, event_type=None, metadata=None):
        from operations.rules import execute_rules

        # 1️⃣ Validate allowed transition
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")

        old_status = self.status
        self.status = new_status
        self.save()

        # 2️⃣ Prepare metadata
        event_metadata = {"from": old_status, "to": new_status}
        if metadata:
            event_metadata.update(metadata)  # merge user-provided metadata

        # 3️⃣ Log event and trigger rules
        if event_type:
            event = log_event(
                organisation=self.organisation,
                actor=actor,
                event_type=event_type,
                object_type=self.__class__.__name__,
                object_id=str(self.id),
                metadata=event_metadata
            )

            execute_rules(event)

        return self
