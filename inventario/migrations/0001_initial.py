import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("pedidos", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Tela",
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
                ("nombre", models.CharField(max_length=120)),
                ("color", models.CharField(max_length=80)),
                (
                    "metros_disponibles",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "precio_metro",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("proveedor", models.CharField(max_length=150)),
                (
                    "stock_minimo",
                    models.DecimalField(
                        decimal_places=2, default=5, max_digits=10
                    ),
                ),
            ],
            options={
                "verbose_name": "tela",
                "verbose_name_plural": "telas",
                "ordering": ["nombre", "id"],
            },
        ),
        migrations.CreateModel(
            name="UsoTela",
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
                    "metros_usados",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usos_tela",
                        to="pedidos.pedido",
                    ),
                ),
                (
                    "tela",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usos",
                        to="inventario.tela",
                    ),
                ),
            ],
            options={
                "verbose_name": "uso de tela",
                "verbose_name_plural": "usos de tela",
                "ordering": ["fecha", "id"],
            },
        ),
    ]
