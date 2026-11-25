"""Serializadores de pagos y saldo."""

from rest_framework import serializers

from .models import Pago


class CrearPagoSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)


class PagoSerializer(serializers.ModelSerializer):
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.nombre", read_only=True
    )
    anulado_por_nombre = serializers.CharField(
        source="anulado_por.nombre", read_only=True, allow_null=True
    )

    class Meta:
        model = Pago
        fields = [
            "id",
            "pedido",
            "monto",
            "fecha",
            "registrado_por",
            "registrado_por_nombre",
            "anulado",
            "anulado_por",
            "anulado_por_nombre",
        ]
        read_only_fields = fields


class PagoConSaldoSerializer(PagoSerializer):
    saldo = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta(PagoSerializer.Meta):
        fields = [*PagoSerializer.Meta.fields, "saldo"]


class PaginaPagosSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PagoSerializer(many=True)
    saldo = serializers.DecimalField(max_digits=10, decimal_places=2)
