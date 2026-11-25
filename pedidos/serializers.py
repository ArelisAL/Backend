"""Representación HTTP de pedidos; las reglas permanecen en services.py."""

from rest_framework import serializers

from .models import Pedido


class FiltroPedidosSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=200)
    incluir_entregados = serializers.BooleanField(required=False, default=False)
    estado = serializers.ChoiceField(choices=Pedido.ESTADOS, required=False)


class CrearPedidoSerializer(serializers.Serializer):
    cliente = serializers.IntegerField(min_value=1)
    prenda = serializers.IntegerField(min_value=1)
    fecha_entrega = serializers.DateField()
    descripcion = serializers.CharField(required=False, allow_blank=True)


class EditarFechaPedidoSerializer(serializers.Serializer):
    fecha_entrega = serializers.DateField()


class EditarPedidoSerializer(serializers.Serializer):
    fecha_entrega = serializers.DateField()


class EditarNotaPedidoSerializer(serializers.Serializer):
    nota_interna = serializers.CharField(allow_blank=True)


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    prenda_nombre = serializers.CharField(source="prenda.nombre", read_only=True)
    categoria_codigo = serializers.CharField(
        source="prenda.categoria.nombre", read_only=True
    )
    costurera_nombre = serializers.CharField(
        source="costurera.nombre", read_only=True, allow_null=True
    )
    medidas_ultima_toma = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "codigo",
            "cliente",
            "cliente_nombre",
            "prenda",
            "prenda_nombre",
            "categoria_codigo",
            "descripcion",
            "fecha_entrega",
            "estado",
            "costurera",
            "costurera_nombre",
            "nota_interna",
            "total",
            "creado_en",
            "entregado_en",
            "medidas_ultima_toma",
        ]
        read_only_fields = fields

    def get_medidas_ultima_toma(self, pedido) -> dict | None:
        from . import services

        toma = services.ultimas_medidas(pedido)
        if toma is None:
            return None
        return {
            "valores_cm": toma.valores_cm,
            "fecha": toma.fecha,
            "categoria": toma.categoria.nombre,
        }
