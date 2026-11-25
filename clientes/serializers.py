"""Forma JSON de clientes y tomas de medidas (sin reglas de negocio)."""

from rest_framework import serializers

from .models import Cliente, Medida


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nombre", "telefono", "correo"]
        read_only_fields = ["id"]


class CrearClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=200)
    telefono = serializers.CharField(max_length=30, required=False, allow_blank=True)
    correo = serializers.EmailField(required=False, allow_blank=True)


class FiltroClientesSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=200)


class RegistrarMedidaSerializer(serializers.Serializer):
    categoria = serializers.CharField(max_length=10)
    prenda = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    valores_cm = serializers.JSONField()


class MedidaSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoria.nombre", read_only=True)
    prenda = serializers.CharField(
        source="prenda.codigo", allow_null=True, read_only=True
    )
    tomada_por = serializers.CharField(source="tomada_por.nombre", read_only=True)

    class Meta:
        model = Medida
        fields = [
            "id",
            "cliente",
            "categoria",
            "prenda",
            "valores_cm",
            "fecha",
            "tomada_por",
        ]
        read_only_fields = fields
