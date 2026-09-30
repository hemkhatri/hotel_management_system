from django.db import migrations


def repair_legacy_order_items(apps, schema_editor):
    """Rebuild old OrderItem rows that referenced Service so they reference SubServiceItem."""
    connection = schema_editor.connection
    OrderItem = apps.get_model("services", "OrderItem")
    Service = apps.get_model("services", "Service")
    SubServiceItem = apps.get_model("services", "SubServiceItem")
    table = OrderItem._meta.db_table
    with connection.cursor() as cursor:
        columns = {column.name for column in connection.introspection.get_table_description(cursor, table)}
        if "item_id" in columns or "service_id" not in columns:
            return
        cursor.execute(
            f"SELECT id, order_id, service_id, quantity, unit_price, subtotal, created_at FROM {schema_editor.quote_name(table)}"
        )
        legacy_rows = cursor.fetchall()

    # Preserve each historical line and price; link it to that service's first current menu item.
    repaired_rows = []
    item_for_service = {}
    for row_id, order_id, service_id, quantity, unit_price, subtotal, created_at in legacy_rows:
        if service_id not in item_for_service:
            service = Service.objects.using(connection.alias).get(pk=service_id)
            item = SubServiceItem.objects.using(connection.alias).filter(service_id=service_id).order_by("pk").first()
            if item is None:
                # Keep legacy orders readable even if the old service has no current menu item.
                item = SubServiceItem.objects.using(connection.alias).create(
                    service_id=service_id,
                    name=service.name,
                    description=service.description,
                    price=unit_price,
                    is_available=True,
                )
            item_for_service[service_id] = item.pk
        repaired_rows.append((row_id, order_id, item_for_service[service_id], quantity, unit_price, subtotal, created_at))

    # The table's database shape drifted from the committed migration; recreate it in current model shape.
    schema_editor.delete_model(OrderItem)
    schema_editor.create_model(OrderItem)
    for row_id, order_id, item_id, quantity, unit_price, subtotal, created_at in repaired_rows:
        OrderItem.objects.using(connection.alias).create(
            pk=row_id,
            order_id=order_id,
            item_id=item_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            created_at=created_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0002_booking_check_status"),
        ("services", "0001_initial"),
    ]

    operations = [migrations.RunPython(repair_legacy_order_items, migrations.RunPython.noop)]
