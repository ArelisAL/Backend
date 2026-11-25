import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogo", "0001_initial"),
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pedido",
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
                ("codigo", models.CharField(max_length=20, unique=True)),
                ("descripcion", models.TextField(blank=True)),
                ("fecha_entrega", models.DateField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("EN_PROCESO", "En Proceso"),
                            ("TERMINADO", "Terminado"),
                            ("ENTREGADO", "Entregado"),
                        ],
                        default="PENDIENTE",
                        max_length=20,
                    ),
                ),
                ("nota_interna", models.TextField(blank=True)),
                (
                    "total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("entregado_en", models.DateTimeField(blank=True, null=True)),
                (
                    "cliente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pedidos",
                        to="clientes.cliente",
                    ),
                ),
                (
                    "costurera",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pedidos_asignados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "prenda",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pedidos",
                        to="catalogo.prenda",
                    ),
                ),
            ],
            options={
                "verbose_name": "pedido",
                "verbose_name_plural": "pedidos",
                "ordering": ["fecha_entrega", "id"],
            },
        ),
    ]
