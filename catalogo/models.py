"""
Catálogo de medidas — DERCAS §7.1 y AGENTS.md §4.4.

Se carga desde MEDIDAS.md (versión 2) con el fixture
`catalogo/fixtures/catalogo_medidas.json`. Los códigos se usan tal cual
aparecen en la guía; no se inventan otros.
"""

from django.db import models


class CategoriaMedida(models.Model):
    """Grupo de la guía de medidas (DERCAS §1.5)."""

    MUJER = "MUJER"
    HOMBRE = "HOMBRE"
    NINO = "NINO"
    BEBE = "BEBE"
    NOMBRES = [
        (MUJER, "Mujer"),
        (HOMBRE, "Hombre"),
        (NINO, "Niño/a"),
        (BEBE, "Bebé"),
    ]

    nombre = models.CharField(max_length=10, choices=NOMBRES, unique=True)

    class Meta:
        verbose_name = "categoría de medidas"
        verbose_name_plural = "categorías de medidas"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.get_nombre_display()


class TipoMedida(models.Model):
    """Una medida del catálogo con su forma de tomarla (en centímetros)."""

    codigo = models.CharField(max_length=60)
    nombre = models.CharField(max_length=120)
    como_se_toma = models.TextField()
    categoria = models.ForeignKey(
        CategoriaMedida, on_delete=models.PROTECT, related_name="tipos_medida"
    )

    class Meta:
        verbose_name = "tipo de medida"
        verbose_name_plural = "tipos de medida"
        ordering = ["categoria_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "codigo"], name="tipomedida_unico_por_categoria"
            )
        ]

    def __str__(self) -> str:
        return f"{self.categoria.nombre}:{self.codigo}"


class Prenda(models.Model):
    """Tipo de prenda del catálogo y las medidas que necesita."""

    codigo = models.CharField(max_length=60)
    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(
        CategoriaMedida, on_delete=models.PROTECT, related_name="prendas"
    )
    medidas = models.ManyToManyField(
        TipoMedida, through="PrendaMedida", related_name="prendas"
    )

    class Meta:
        verbose_name = "prenda"
        verbose_name_plural = "prendas"
        ordering = ["categoria_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "codigo"], name="prenda_unica_por_categoria"
            )
        ]

    def __str__(self) -> str:
        return f"{self.categoria.nombre}:{self.codigo}"


class PrendaMedida(models.Model):
    """Medida requerida por una prenda; `opcional` según MEDIDAS.md."""

    prenda = models.ForeignKey(
        Prenda, on_delete=models.CASCADE, related_name="medidas_requeridas"
    )
    tipo_medida = models.ForeignKey(
        TipoMedida, on_delete=models.PROTECT, related_name="en_prendas"
    )
    opcional = models.BooleanField(default=False)

    class Meta:
        verbose_name = "medida de la prenda"
        verbose_name_plural = "medidas de la prenda"
        ordering = ["prenda_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["prenda", "tipo_medida"], name="prendamedida_unica"
            )
        ]

    def __str__(self) -> str:
        return f"{self.prenda} -> {self.tipo_medida.codigo}"
