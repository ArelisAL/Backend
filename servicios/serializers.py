"""Contrato JSON para la administración del catálogo de servicios."""

from rest_framework import serializers

from .models import HistorialServicio, Servicio


class ServicioSerializer(serializers.ModelSerializer):
    configuracion_pendiente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Servicio
        fields = [
            "id",
            "codigo",
            "nombre",
            "categoria",
            "descripcion",
            "unidad",
            "tarifa_base",
            "requiere_valoracion",
            "configuracion_pendiente",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]
        extra_kwargs = {
            "tarifa_base": {
                "required": False,
                "allow_null": True,
                "min_value": 0,
            },
            "descripcion": {"required": False, "allow_blank": True},
            "requiere_valoracion": {"required": False},
            "activo": {"required": False},
        }


class HistorialServicioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)

    class Meta:
        model = HistorialServicio
        fields = ["id", "accion", "datos", "usuario_nombre", "fecha_hora"]


class PaginaServicioSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ServicioSerializer(many=True)


class PaginaHistorialServicioSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = HistorialServicioSerializer(many=True)
