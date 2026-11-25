"""Representación de solicitud para asignación de costurera."""

from rest_framework import serializers


class AsignarCostureraSerializer(serializers.Serializer):
    costurera = serializers.IntegerField(min_value=1)


class AsignacionResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    costurera = serializers.IntegerField()
    costurera_nombre = serializers.CharField()
