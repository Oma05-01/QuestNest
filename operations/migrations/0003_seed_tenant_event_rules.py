from django.db import migrations

def create_tenant_event_rules(apps, schema_editor):
    EventRule = apps.get_model("operations", "EventRule")
    Organisation = apps.get_model("organisations", "Organisation")

    # Global rules for tenant registration
    EventRule.objects.create(
        event_type="TENANT_REGISTERED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Verify tenant email",
        task_description="Ensure the tenant's email has been verified",
        execution_order=1,
        is_active=True,
    )

    EventRule.objects.create(
        event_type="TENANT_REGISTERED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Verify tenant ID",
        task_description="Verify uploaded identification documents for the tenant",
        execution_order=2,
        is_active=True,
    )

    EventRule.objects.create(
        event_type="TENANT_REGISTERED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Assign initial workspace",
        task_description="Assign tenant to the appropriate organisation workspace if applicable",
        execution_order=3,
        is_active=True,
    )

def reverse_func(apps, schema_editor):
    EventRule = apps.get_model("operations", "EventRule")
    EventRule.objects.filter(event_type="TENANT_REGISTERED").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0002_seed_initial_event_rules'),
    ]

    operations = [
        migrations.RunPython(create_tenant_event_rules, reverse_func),
    ]
