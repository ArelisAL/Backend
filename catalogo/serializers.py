"""Representación JSON del catálogo de medidas."""

from rest_framework import serializers

from .models import CategoriaMedida, Prenda, PrendaMedida


class TipoMedidaSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    como_se_toma = serializers.CharField()

    def to_representation(self, instance):
        return {
            "codigo": instance.codigo,
            "nombre": instance.nombre,
            "como_se_toma": instance.como_se_toma,
        }


class CategoriaMedidaSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField(source="nombre")
    nombre = serializers.CharField(source="get_nombre_display")
    tipos_medida = TipoMedidaSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriaMedida
        fields = ["id", "codigo", "nombre", "tipos_medida"]


class PrendaSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoria.nombre")

    class Meta:
        model = Prenda
        fields = ["id", "codigo", "nombre", "categoria"]


class PrendaMedidaSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField(source="tipo_medida.codigo")
    nombre = serializers.CharField(source="tipo_medida.nombre")
    como_se_toma = serializers.CharField(source="tipo_medida.como_se_toma")

    class Meta:
        model = PrendaMedida
        fields = ["codigo", "nombre", "como_se_toma", "opcional"]


class FiltroPrendasSerializer(serializers.Serializer):
    categoria = serializers.ChoiceField(choices=CategoriaMedida.NOMBRES, required=False)
