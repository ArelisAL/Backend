"""Serializadores de telas para la API."""

from decimal import Decimal

from rest_framework import serializers

from .models import Tela, UsoTela


class TelaSerializer(serializers.ModelSerializer):
    stock_bajo = serializers.SerializerMethodField()

    class Meta:
        model = Tela
        fields = [
            "id",
            "nombre",
            "color",
            "metros_disponibles",
            "precio_metro",
            "proveedor",
            "stock_minimo",
            "stock_bajo",
        ]
        read_only_fields = ["id", "stock_bajo"]

    def get_stock_bajo(self, tela):
        return tela.metros_disponibles <= tela.stock_minimo


class CrearTelaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    color = serializers.CharField(max_length=80)
    metros_disponibles = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_metro = serializers.DecimalField(max_digits=10, decimal_places=2)
    proveedor = serializers.CharField(max_length=150)
    stock_minimo = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=5
    )


class EditarTelaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120, required=False)
    color = serializers.CharField(max_length=80, required=False)
    metros_disponibles = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    precio_metro = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    proveedor = serializers.CharField(max_length=150, required=False)
    stock_minimo = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )


class ErrorInventarioSerializer(serializers.Serializer):
    error = serializers.CharField()
    detalle = serializers.CharField()


class TelaOpcionConsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tela
        fields = ["id", "nombre", "color", "metros_disponibles"]
        read_only_fields = fields


class UsoTelaSerializer(serializers.ModelSerializer):
    tela_nombre = serializers.CharField(source="tela.nombre", read_only=True)
    tela_color = serializers.CharField(source="tela.color", read_only=True)
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.nombre", read_only=True, allow_null=True
    )
    reemplazado_por_nombre = serializers.CharField(
        source="reemplazado_por.nombre", read_only=True, allow_null=True
    )

    class Meta:
        model = UsoTela
        fields = [
            "id",
            "tela",
            "tela_nombre",
            "tela_color",
            "metros_usados",
            "registrado_por_nombre",
            "confirmado",
            "vigente",
            "reemplazado_en",
            "reemplazado_por_nombre",
            "fecha",
        ]
        read_only_fields = fields


class UsoTelaEntradaSerializer(serializers.Serializer):
    tela = serializers.IntegerField(min_value=1)
    metros_usados = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )


class RegistrarConsumosSerializer(serializers.Serializer):
    usos = UsoTelaEntradaSerializer(many=True, allow_empty=False)


class PaginaTelaOpcionConsumoSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TelaOpcionConsumoSerializer(many=True)


class PaginaUsoTelaSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = UsoTelaSerializer(many=True)
