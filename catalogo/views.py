"""Endpoints de consulta del catálogo; todas las reglas de acceso usan JWT."""

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from . import services
from .serializers import (
    CategoriaMedidaSerializer,
    FiltroPrendasSerializer,
    PrendaMedidaSerializer,
    PrendaSerializer,
)


class CategoriaListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CategoriaMedidaSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        categorias = services.listar_categorias()
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(categorias, request, view=self)
        data = CategoriaMedidaSerializer(pagina, many=True).data
        return paginador.get_paginated_response(data)


class PrendaListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter("categoria", str, required=False)],
        responses={200: PrendaSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        filtro = FiltroPrendasSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        prendas = services.listar_prendas(**filtro.validated_data)
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(prendas, request, view=self)
        data = PrendaSerializer(pagina, many=True).data
        return paginador.get_paginated_response(data)


class PrendaMedidaListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: PrendaMedidaSerializer(many=True),
            401: OpenApiResponse(description="Token JWT inválido o ausente"),
            404: OpenApiResponse(description="Prenda inexistente"),
        }
    )
    def get(self, request, prenda_id: int, *args, **kwargs):
        try:
            medidas = services.listar_medidas_prenda(prenda_id)
        except services.PrendaNoEncontrada:
            return Response(
                {
                    "error": "no_encontrado",
                    "detalle": "La prenda no existe en el catálogo.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        paginador = api_settings.DEFAULT_PAGINATION_CLASS()
        pagina = paginador.paginate_queryset(medidas, request, view=self)
        return paginador.get_paginated_response(
            PrendaMedidaSerializer(pagina, many=True).data
        )
