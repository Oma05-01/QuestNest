def reconcile_payment_event(event):
    """
    Re-run rules safely for failed or partial executions.
    """

    from operations.rules import execute_rules

    execute_rules(event)