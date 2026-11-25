"""Permisos por rol del módulo clientes."""

from rest_framework.permissions import BasePermission


class EsAdministradoraORecepcionista(BasePermission):
    message = "Solo la administradora o la recepcionista pueden acceder a clientes."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol in {"administradora", "recepcionista"}
        )


class AccesoMedidasCliente(BasePermission):
    """Costurera solo accede a medidas ligadas a sus pedidos asignados."""

    message = "Solo puedes consultar medidas de clientes con pedidos asignados."

    def has_permission(self, request, view):
        usuario = request.user
        rol = getattr(usuario, "rol", None)
        if rol in {"administradora", "recepcionista"}:
            return True
        if rol != "costurera":
            return False
        from pedidos import services as pedidos_services

        cliente_id = view.kwargs.get("cliente_id")
        if not cliente_id:
            return False
        if request.method == "GET":
            return bool(
                pedidos_services.prendas_asignadas_de_cliente(usuario, cliente_id)
            )
        if request.method == "POST":
            prenda_id = request.data.get("prenda")
            try:
                prenda_id = int(prenda_id) if prenda_id not in (None, "") else None
            except (TypeError, ValueError):
                return False
            return pedidos_services.puede_trabajar_con_medidas(
                usuario, cliente_id, prenda_id
            )
        return False
