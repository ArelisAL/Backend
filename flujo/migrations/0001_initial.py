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
            name="HistorialEstado",
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
                    "estado_anterior",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("EN_PROCESO", "En Proceso"),
                            ("TERMINADO", "Terminado"),
                            ("ENTREGADO", "Entregado"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "estado_nuevo",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("EN_PROCESO", "En Proceso"),
                            ("TERMINADO", "Terminado"),
                            ("ENTREGADO", "Entregado"),
                        ],
                        max_length=20,
                    ),
                ),
                ("fecha_hora", models.DateTimeField(auto_now_add=True)),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="historial_estados",
                        to="pedidos.pedido",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cambios_estado_pedido",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historial de estado",
                "verbose_name_plural": "historiales de estado",
                "ordering": ["fecha_hora", "id"],
            },
        ),
    ]
