"""Representación JSON para transiciones e historial."""

from rest_framework import serializers

from .models import HistorialEstado


class ConfirmarCambioEstadoSerializer(serializers.Serializer):
    confirmar = serializers.BooleanField()


class HistorialEstadoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)

    class Meta:
        model = HistorialEstado
        fields = [
            "id",
            "estado_anterior",
            "estado_nuevo",
            "fecha_hora",
            "usuario_nombre",
        ]
        read_only_fields = fields
