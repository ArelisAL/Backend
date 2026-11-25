"""Vista de asignación con autorización por rol y servicio de negocio."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .permissions import EsAdministradora
from .serializers import AsignacionResponseSerializer, AsignarCostureraSerializer


class AsignacionPedidoView(APIView):
    permission_classes = [EsAdministradora]

    @extend_schema(
        request=AsignarCostureraSerializer,
        responses={
            200: AsignacionResponseSerializer,
            400: OpenApiResponse(description="Pedido o costurera inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Solo administradora"),
        },
    )
    def post(self, request, codigo: str, *args, **kwargs):
        entrada = AsignarCostureraSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            pedido = services.asignar_pedido(
                codigo, entrada.validated_data["costurera"]
            )
        except services.AsignacionInvalidas as exc:
            return Response(
                {"error": "asignacion_invalida", "detalle": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        salida = AsignacionResponseSerializer(
            {
                "id": pedido.id,
                "codigo": pedido.codigo,
                "costurera": pedido.costurera_id,
                "costurera_nombre": pedido.costurera.nombre,
            }
        )
        return Response(salida.data)
