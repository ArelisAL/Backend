import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pedidos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pago",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "monto",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("anulado", models.BooleanField(default=False)),
                (
                    "anulado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos_anulados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos",
                        to="pedidos.pedido",
                    ),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagos_registrados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "pago",
                "verbose_name_plural": "pagos",
                "ordering": ["fecha", "id"],
            },
        ),
    ]
