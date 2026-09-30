from django.db import migrations, models


def ensure_check_status_columns(apps, schema_editor):
    """Add the legacy check-in flags only when absent; existing databases retain stored values."""
    connection = schema_editor.connection
    Booking = apps.get_model("bookings", "Booking")
    with connection.cursor() as cursor:
        columns = {column.name for column in connection.introspection.get_table_description(cursor, Booking._meta.db_table)}
    for name in ("check_in_status", "check_out_status"):
        if name not in columns:
            field = models.BooleanField(default=False)
            field.set_attributes_from_name(name)
            schema_editor.add_field(Booking, field)


class Migration(migrations.Migration):
    dependencies = [("bookings", "0001_initial")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(ensure_check_status_columns, migrations.RunPython.noop)],
            state_operations=[
                migrations.AddField(
                    model_name="booking",
                    name="check_in_status",
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name="booking",
                    name="check_out_status",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
