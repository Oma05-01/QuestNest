from operations.services.event_service import log_event
from operations.rules import execute_rules


class LifecycleMixin:
    DRAFT = "draft"
    LISTED = "listed"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    ARCHIVED = "archived"

    ALLOWED_TRANSITIONS = {
        DRAFT: [LISTED, ARCHIVED],
        LISTED: [RESERVED, ARCHIVED],
        RESERVED: [OCCUPIED, LISTED],
        OCCUPIED: [ARCHIVED],
        ARCHIVED: [],
    }

    def transition_to(self, new_status, *, actor=None, event_type=None):

        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])

        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition from {self.status} to {new_status}"
            )

        old_status = self.status
        self.status = new_status
        self.save()

        if event_type:
            event = log_event(
                organisation=self.organisation,
                actor=actor,
                event_type=event_type,
                object_type=self.__class__.__name__,
                object_id=str(self.id),
                metadata={
                    "from": old_status,
                    "to": new_status
                }
            )

            execute_rules(event)

        return self
