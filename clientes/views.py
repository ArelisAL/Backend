"""Vistas HTTP del módulo clientes: permiso, servicio y respuesta JSON."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import services
from .permissions import AccesoMedidasCliente, EsAdministradoraORecepcionista
from .serializers import (
    ClienteSerializer,
    CrearClienteSerializer,
    FiltroClientesSerializer,
    MedidaSerializer,
    RegistrarMedidaSerializer,
)


def _error(codigo: str, detalle: str, estado: int) -> Response:
    return Response({"error": codigo, "detalle": detalle}, status=estado)


class ClienteListView(APIView):
    permission_classes = [EsAdministradoraORecepcionista]

    @extend_schema(
        parameters=[FiltroClientesSerializer],
        responses={200: ClienteSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filtro = FiltroClientesSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        clientes = services.listar_clientes(busqueda=filtro.validated_data.get("q"))
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(clientes, request, view=self)
        return paginador.get_paginated_response(
            ClienteSerializer(pagina, many=True).data
        )

    @extend_schema(
        request=CrearClienteSerializer,
        responses={
            201: ClienteSerializer,
            400: OpenApiResponse(description="Datos inválidos"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Rol sin permiso"),
            409: OpenApiResponse(description="Cliente ya registrado"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = CrearClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cliente = services.crear_cliente(serializer.validated_data)
        except services.ClienteDuplicado as exc:
            return _error("cliente_duplicado", str(exc), status.HTTP_409_CONFLICT)
        except services.DatosClienteInvalidos as exc:
            return _error("datos_invalidos", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(ClienteSerializer(cliente).data, status=status.HTTP_201_CREATED)


class ClienteDetailView(APIView):
    permission_classes = [EsAdministradoraORecepcionista]

    @extend_schema(responses={200: ClienteSerializer})
    def get(self, request, cliente_id: int, *args, **kwargs):
        try:
            cliente = services.obtener_cliente(cliente_id)
        except services.ClienteNoEncontrado:
            return _error(
                "no_encontrado", "El cliente no existe.", status.HTTP_404_NOT_FOUND
            )
        return Response(ClienteSerializer(cliente).data)


class ClienteMedidasView(APIView):
    permission_classes = [AccesoMedidasCliente]

    @extend_schema(responses={200: MedidaSerializer(many=True)})
    def get(self, request, cliente_id: int, *args, **kwargs):
        try:
            costurera = request.user if request.user.rol == "costurera" else None
            medidas = services.listar_medidas(cliente_id, costurera=costurera)
        except services.ClienteNoEncontrado:
            return _error(
                "no_encontrado", "El cliente no existe.", status.HTTP_404_NOT_FOUND
            )
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(medidas, request, view=self)
        return paginador.get_paginated_response(
            MedidaSerializer(pagina, many=True).data
        )

    @extend_schema(
        request=RegistrarMedidaSerializer,
        responses={
            201: MedidaSerializer,
            400: OpenApiResponse(description="Medidas inválidas"),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            403: OpenApiResponse(description="Rol sin permiso"),
            404: OpenApiResponse(description="Cliente inexistente"),
        },
    )
    def post(self, request, cliente_id: int, *args, **kwargs):
        entrada = RegistrarMedidaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            cliente = services.obtener_cliente(cliente_id)
            medida = services.registrar_medida(
                cliente=cliente,
                categoria_codigo=entrada.validated_data["categoria"],
                prenda_id=entrada.validated_data.get("prenda"),
                valores_cm=entrada.validated_data["valores_cm"],
                tomada_por=request.user,
            )
        except services.ClienteNoEncontrado:
            return _error(
                "no_encontrado", "El cliente no existe.", status.HTTP_404_NOT_FOUND
            )
        except services.DatosDeMedidaInvalidos as exc:
            return _error("medidas_invalidas", str(exc), status.HTTP_400_BAD_REQUEST)
        return Response(MedidaSerializer(medida).data, status=status.HTTP_201_CREATED)
