from django.db import migrations

def create_initial_event_rules(apps, schema_editor):
    EventRule = apps.get_model("operations", "EventRule")
    Organisation = apps.get_model("organisations", "Organisation")

    # Global rules (applies to all organisations)
    EventRule.objects.create(
        event_type="PROPERTY_CREATED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Upload property documents",
        task_description="Upload all required documents for the property",
        execution_order=1,
        is_active=True,
    )

    EventRule.objects.create(
        event_type="PROPERTY_CREATED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Add property units",
        task_description="Add at least one unit to the property",
        execution_order=2,
        is_active=True,
    )

    EventRule.objects.create(
        event_type="PROPERTY_CREATED",
        organisation=None,
        action_type="CREATE_TASK",
        task_title="Assign property manager",
        task_description="Assign a manager to oversee the property",
        execution_order=3,
        is_active=True,
    )

def reverse_func(apps, schema_editor):
    EventRule = apps.get_model("operations", "EventRule")
    EventRule.objects.filter(event_type="PROPERTY_CREATED").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_event_rules, reverse_func),
    ]
