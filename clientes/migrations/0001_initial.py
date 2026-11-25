import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cliente",
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
                ("nombre", models.CharField(max_length=200)),
                (
                    "telefono",
                    models.CharField(
                        blank=True, max_length=30, null=True, unique=True
                    ),
                ),
                (
                    "correo",
                    models.EmailField(blank=True, max_length=254, null=True, unique=True),
                ),
            ],
            options={
                "verbose_name": "cliente",
                "verbose_name_plural": "clientes",
                "ordering": ["nombre", "id"],
            },
        ),
        migrations.CreateModel(
            name="Medida",
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
                ("valores_cm", models.JSONField(default=dict)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tomas_medida",
                        to="catalogo.categoriamedida",
                    ),
                ),
                (
                    "cliente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="medidas",
                        to="clientes.cliente",
                    ),
                ),
                (
                    "prenda",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tomas_medida",
                        to="catalogo.prenda",
                    ),
                ),
                (
                    "tomada_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="medidas_tomadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "toma de medidas",
                "verbose_name_plural": "tomas de medidas",
                "ordering": ["-fecha", "-id"],
            },
        ),
    ]
