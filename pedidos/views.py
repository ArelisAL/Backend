"""Vistas del módulo pedidos: permisos, servicios y respuesta JSON."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import services
from .permissions import (
    EsAdministradora,
    EsAdministradoraORecepcionista,
    EsCosturera,
    EsPersonalTaller,
    EsRecepcionista,
)
from .serializers import (
    AgregarServicioPedidoSerializer,
    CrearPedidoSerializer,
    EditarNotaPedidoSerializer,
    EditarPedidoSerializer,
    FiltroPedidosSerializer,
    PedidoCostureraSerializer,
    PedidoSerializer,
    ServicioPedidoSerializer,
    serializer_pedido_para,
)


def _error(codigo: str, detalle: str, estado: int) -> Response:
    return Response({"error": codigo, "detalle": detalle}, status=estado)


class PedidoListView(APIView):
    permission_classes = [EsPersonalTaller]

    def get_permissions(self):
        clases = (
            [EsAdministradoraORecepcionista]
            if self.request.method == "POST"
            else self.permission_classes
        )
        return [clase() for clase in clases]

    @extend_schema(
        parameters=[FiltroPedidosSerializer],
        responses={200: PedidoSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filtro = FiltroPedidosSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        pedidos = services.listar_pedidos(
            request.user,
            busqueda=filtro.validated_data.get("q"),
            incluir_entregados=filtro.validated_data["incluir_entregados"],
            estado=filtro.validated_data.get("estado"),
        )
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(pedidos, request, view=self)
        return paginador.get_paginated_response(
            serializer_pedido_para(request.user)(pagina, many=True).data
        )

    @extend_schema(
        request=CrearPedidoSerializer,
        responses={
            201: PedidoSerializer,
            400: OpenApiResponse(description="Datos de pedido inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Rol sin permiso"),
        },
    )
    def post(self, request, *args, **kwargs):
        entrada = CrearPedidoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            pedido = services.crear_pedido(datos)
        except services.DatosPedidoInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.CodigoPedidoEnConflicto:
            return _error(
                "conflicto_codigo",
                "No se pudo generar un código único. Intenta de nuevo.",
                status.HTTP_409_CONFLICT,
            )
        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)


class MisPedidosView(APIView):
    permission_classes = [EsCosturera]

    @extend_schema(
        parameters=[FiltroPedidosSerializer],
        responses={200: PedidoCostureraSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filtro = FiltroPedidosSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        pedidos = services.listar_pedidos(
            request.user,
            busqueda=filtro.validated_data.get("q"),
            incluir_entregados=filtro.validated_data["incluir_entregados"],
            estado=filtro.validated_data.get("estado"),
        )
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(pedidos, request, view=self)
        return paginador.get_paginated_response(
            serializer_pedido_para(request.user)(pagina, many=True).data
        )


class PedidoDetailView(APIView):
    permission_classes = [EsPersonalTaller]

    def get_permissions(self):
        return [clase() for clase in self.permission_classes]

    @extend_schema(responses={200: PedidoSerializer})
    def get(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = services.obtener_pedido_por_codigo(codigo, request.user)
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        return Response(serializer_pedido_para(request.user)(pedido).data)

    @extend_schema(
        request=EditarPedidoSerializer,
        responses={
            200: PedidoSerializer,
            400: OpenApiResponse(description="Fecha inválida"),
            403: OpenApiResponse(description="Solo administradora"),
        },
    )
    def patch(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = services.obtener_pedido_por_codigo(codigo, request.user)
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        entrada = EditarPedidoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        if not EsAdministradora().has_permission(request, self):
            return _error(
                "sin_permiso",
                "Solo la administradora puede modificar la fecha de entrega.",
                status.HTTP_403_FORBIDDEN,
            )
        try:
            pedido = services.cambiar_fecha_entrega(
                pedido, entrada.validated_data["fecha_entrega"]
            )
        except services.DatosPedidoInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(PedidoSerializer(pedido).data)


class PedidoNotaView(APIView):
    permission_classes = [EsPersonalTaller]

    @extend_schema(
        request=EditarNotaPedidoSerializer,
        responses={
            200: PedidoSerializer,
            400: OpenApiResponse(description="Nota inválida"),
            403: OpenApiResponse(description="Pedido ajeno a la costurera"),
            404: OpenApiResponse(description="Pedido inexistente"),
        },
    )
    def patch(self, request, codigo: str, *args, **kwargs):
        entrada = EditarNotaPedidoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            pedido = services.obtener_pedido_por_codigo(codigo, request.user)
            pedido = services.cambiar_nota_interna(
                pedido, entrada.validated_data["nota_interna"]
            )
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except PermissionError as exc:
            return _error("sin_permiso", str(exc), status.HTTP_403_FORBIDDEN)
        return Response(serializer_pedido_para(request.user)(pedido).data)


class PedidoServiciosView(APIView):
    """Prendas del pedido tomadas del catálogo de servicios (auditoría C1)."""

    permission_classes = [EsAdministradoraORecepcionista]

    @extend_schema(responses={200: ServicioPedidoSerializer(many=True)})
    def get(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = services.obtener_pedido_por_codigo(codigo, request.user)
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        lineas = services.listar_servicios_pedido(pedido)
        return Response(ServicioPedidoSerializer(lineas, many=True).data)

    @extend_schema(
        request=AgregarServicioPedidoSerializer,
        responses={
            201: ServicioPedidoSerializer,
            400: OpenApiResponse(description="Servicio inválido o sin tarifa"),
            403: OpenApiResponse(description="Rol sin permiso"),
            404: OpenApiResponse(description="Pedido inexistente"),
            409: OpenApiResponse(description="El total ya está cerrado"),
        },
    )
    def post(self, request, codigo: str, *args, **kwargs):
        entrada = AgregarServicioPedidoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            linea = services.agregar_servicio_pedido(
                codigo,
                datos["servicio"],
                datos["cantidad"],
                datos.get("detalle", ""),
                request.user,
            )
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.DatosPedidoInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.TotalYaCerrado as exc:
            return _error("total_cerrado", str(exc), status.HTTP_409_CONFLICT)
        return Response(
            ServicioPedidoSerializer(linea).data, status=status.HTTP_201_CREATED
        )


class PedidoServicioDetalleView(APIView):
    permission_classes = [EsAdministradoraORecepcionista]

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Prenda quitada del pedido"),
            400: OpenApiResponse(description="La prenda no es de este pedido"),
            404: OpenApiResponse(description="Pedido inexistente"),
            409: OpenApiResponse(description="El total ya está cerrado"),
        },
    )
    def delete(self, request, codigo: str, linea_id: int, *args, **kwargs):
        try:
            services.quitar_servicio_pedido(codigo, linea_id)
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.DatosPedidoInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.TotalYaCerrado as exc:
            return _error("total_cerrado", str(exc), status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PedidoCerrarTotalView(APIView):
    permission_classes = [EsRecepcionista]

    @extend_schema(
        request=None,
        responses={
            200: PedidoSerializer,
            400: OpenApiResponse(description="El pedido no tiene prendas"),
            403: OpenApiResponse(description="Solo recepcionista"),
            404: OpenApiResponse(description="Pedido inexistente"),
            409: OpenApiResponse(description="El total ya está cerrado"),
        },
    )
    def post(self, request, codigo: str, *args, **kwargs):
        try:
            pedido = services.cerrar_total(codigo, request.user)
        except services.PedidoNoEncontrado:
            return _error(
                "no_encontrado", "El pedido no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.DatosPedidoInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        except services.TotalYaCerrado as exc:
            return _error("total_cerrado", str(exc), status.HTTP_409_CONFLICT)
        return Response(PedidoSerializer(pedido).data)
