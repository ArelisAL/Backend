"""Registro de consumos previo al inicio de producción (DERCAS v1.5)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from catalogo.models import CategoriaMedida, Prenda
from clientes.models import Cliente
from flujo.models import HistorialEstado
from inventario import services
from inventario.models import Tela, UsoTela
from pedidos.models import Pedido
from usuarios.models import Usuario


@pytest.fixture
def contexto_consumo():
    admin = Usuario.objects.create_user(
        email="admin-consumos@fran-costuras.test",
        password="Hilo-Morado-2026",
        nombre="Admin",
        rol="administradora",
        debe_cambiar_contraseña=False,
    )
    recepcion = Usuario.objects.create_user(
        email="recepcion-consumos@fran-costuras.test",
        password="Hilo-Morado-2026",
        nombre="Recepción",
        rol="recepcionista",
        debe_cambiar_contraseña=False,
    )
    costurera = Usuario.objects.create_user(
        email="costurera-consumos@fran-costuras.test",
        password="Hilo-Morado-2026",
        nombre="Costurera",
        rol="costurera",
        debe_cambiar_contraseña=False,
    )
    categoria = CategoriaMedida.objects.create(nombre="MUJER")
    prenda = Prenda.objects.create(
        codigo="blusa-test", nombre="Blusa de prueba", categoria=categoria
    )
    cliente = Cliente.objects.create(nombre="Cliente ficticio")
    pedido = Pedido.objects.create(
        codigo="FC-CNS-001",
        cliente=cliente,
        prenda=prenda,
        fecha_entrega=date.today() + timedelta(days=7),
        costurera=costurera,
    )
    tela = Tela.objects.create(
        nombre="Algodón de prueba",
        color="Lila",
        metros_disponibles=Decimal("10.00"),
        precio_metro=Decimal("2.50"),
        proveedor="Proveedor ficticio",
    )
    return {
        "admin": admin,
        "recepcion": recepcion,
        "costurera": costurera,
        "pedido": pedido,
        "tela": tela,
    }


@pytest.mark.django_db
def test_recepcion_registra_sin_descontar_y_admin_confirma_atomicamente(
    client, contexto_consumo
):
    datos = contexto_consumo
    client.force_authenticate(datos["recepcion"])
    opciones = client.get("/api/v1/telas/opciones-consumo/").json()
    assert opciones["results"][0] == {
        "id": datos["tela"].pk,
        "nombre": "Algodón de prueba",
        "color": "Lila",
        "metros_disponibles": "10.00",
    }
    assert "proveedor" not in opciones["results"][0]
    assert "precio_metro" not in opciones["results"][0]

    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/",
        {"usos": [{"tela": datos["tela"].pk, "metros_usados": "2.50"}]},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    datos["tela"].refresh_from_db()
    assert datos["tela"].metros_disponibles == Decimal("10.00")
    assert UsoTela.objects.get(pedido=datos["pedido"]).confirmado is False

    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/",
        {"usos": [{"tela": datos["tela"].pk, "metros_usados": "3.00"}]},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    anteriores = UsoTela.objects.filter(pedido=datos["pedido"], vigente=False)
    assert anteriores.count() == 1
    assert anteriores.get().reemplazado_por == datos["recepcion"]
    listado = client.get(f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/").json()
    assert set(listado) == {"count", "next", "previous", "results"}
    assert listado["results"][0]["vigente"] is True

    client.force_authenticate(datos["admin"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/estado/",
        {"confirmar": True},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    datos["tela"].refresh_from_db()
    datos["pedido"].refresh_from_db()
    uso = UsoTela.objects.get(pedido=datos["pedido"], vigente=True)
    assert datos["tela"].metros_disponibles == Decimal("7.00")
    assert datos["pedido"].estado == Pedido.EN_PROCESO
    assert uso.confirmado is True
    assert HistorialEstado.objects.filter(pedido=datos["pedido"]).count() == 1


@pytest.mark.django_db
def test_inicio_requiere_consumos_registrados(client, contexto_consumo):
    datos = contexto_consumo
    client.force_authenticate(datos["admin"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/estado/",
        {"confirmar": True},
        format="json",
    )
    datos["pedido"].refresh_from_db()
    datos["tela"].refresh_from_db()
    assert respuesta.status_code == 400
    assert datos["pedido"].estado == Pedido.PENDIENTE
    assert datos["tela"].metros_disponibles == Decimal("10.00")
    assert HistorialEstado.objects.filter(pedido=datos["pedido"]).count() == 0


@pytest.mark.django_db
def test_admin_puede_capturar_y_costurera_asignada_confirmar(client, contexto_consumo):
    datos = contexto_consumo
    client.force_authenticate(datos["admin"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/",
        {"usos": [{"tela": datos["tela"].pk, "metros_usados": "1.25"}]},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()

    client.force_authenticate(datos["costurera"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/estado/",
        {"confirmar": True},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    datos["pedido"].refresh_from_db()
    datos["tela"].refresh_from_db()
    assert datos["pedido"].estado == Pedido.EN_PROCESO
    assert datos["tela"].metros_disponibles == Decimal("8.75")


@pytest.mark.django_db
def test_stock_insuficiente_no_confirma_consumo_ni_estado(client, contexto_consumo):
    datos = contexto_consumo
    client.force_authenticate(datos["recepcion"])
    client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/",
        {"usos": [{"tela": datos["tela"].pk, "metros_usados": "12.00"}]},
        format="json",
    )
    client.force_authenticate(datos["admin"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/estado/",
        {"confirmar": True},
        format="json",
    )
    datos["pedido"].refresh_from_db()
    datos["tela"].refresh_from_db()
    uso = UsoTela.objects.get(pedido=datos["pedido"])
    assert respuesta.status_code == 409
    assert datos["pedido"].estado == Pedido.PENDIENTE
    assert datos["tela"].metros_disponibles == Decimal("10.00")
    assert uso.confirmado is False
    assert not HistorialEstado.objects.filter(pedido=datos["pedido"]).exists()


@pytest.mark.django_db
def test_recepcion_no_puede_confirmar_estado_y_costurera_no_captura(
    client, contexto_consumo
):
    datos = contexto_consumo
    client.force_authenticate(datos["recepcion"])
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/estado/",
        {"confirmar": True},
        format="json",
    )
    assert respuesta.status_code == 403

    client.force_authenticate(datos["costurera"])
    respuesta = client.get("/api/v1/telas/opciones-consumo/")
    assert respuesta.status_code == 403
    respuesta = client.post(
        f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/",
        {"usos": [{"tela": datos["tela"].pk, "metros_usados": "1.00"}]},
        format="json",
    )
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_consumos_exigen_autenticacion(client, contexto_consumo):
    respuesta = client.get(
        f"/api/v1/pedidos/{contexto_consumo['pedido'].codigo}/consumos/"
    )
    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_costurera_no_consulta_consumos_de_pedido_ajeno(client, contexto_consumo):
    datos = contexto_consumo
    otra = Usuario.objects.create_user(
        email="otra-costurera@fran-costuras.test",
        password="Hilo-Morado-2026",
        nombre="Otra costurera",
        rol="costurera",
        debe_cambiar_contraseña=False,
    )
    client.force_authenticate(otra)
    respuesta = client.get(f"/api/v1/pedidos/{datos['pedido'].codigo}/consumos/")
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_catalogo_stock_bajo_y_busqueda_de_tela(contexto_consumo):
    datos = contexto_consumo
    datos["tela"].metros_disponibles = Decimal("5.00")
    datos["tela"].save(update_fields=["metros_disponibles"])
    assert list(services.listar_telas()) == [datos["tela"]]
    assert list(services.listar_telas_stock_bajo()) == [datos["tela"]]
    assert services.obtener_tela(datos["tela"].pk).pk == datos["tela"].pk
    with pytest.raises(services.TelaNoEncontrada):
        services.obtener_tela(9999)


@pytest.mark.django_db
def test_crear_tela_y_rechazar_datos_de_stock_invalidos():
    datos = {
        "nombre": "  Lino  ",
        "color": "  Crema  ",
        "metros_disponibles": "8.00",
        "precio_metro": "4.50",
        "proveedor": "  Proveedor ficticio  ",
    }
    tela = services.crear_tela(datos)
    assert (tela.nombre, tela.color, tela.proveedor) == (
        "Lino",
        "Crema",
        "Proveedor ficticio",
    )
    assert tela.stock_minimo == Decimal(5)
    for campo, valor in (("metros_disponibles", "-1"), ("stock_minimo", "-1")):
        invalido = {**datos, campo: valor}
        with pytest.raises(services.DatosInventarioInvalidos):
            services.crear_tela(invalido)


@pytest.mark.django_db
def test_editar_tela_actualiza_campos_y_valida_numeros(contexto_consumo):
    tela = contexto_consumo["tela"]
    actualizada = services.editar_tela(
        tela,
        {
            "nombre": "  Seda  ",
            "color": "  Rosa  ",
            "proveedor": "  Proveedor nuevo  ",
            "metros_disponibles": "8.25",
            "precio_metro": "3.75",
            "stock_minimo": "2.00",
        },
    )
    assert actualizada.nombre == "Seda"
    assert actualizada.color == "Rosa"
    assert actualizada.proveedor == "Proveedor nuevo"
    assert actualizada.metros_disponibles == Decimal("8.25")
    assert actualizada.precio_metro == Decimal("3.75")
    assert actualizada.stock_minimo == Decimal("2.00")
    for campo, valor in (
        ("metros_disponibles", "no-numérico"),
        ("metros_disponibles", "-1"),
        ("precio_metro", "0"),
        ("stock_minimo", "no-numérico"),
        ("stock_minimo", "-1"),
    ):
        with pytest.raises(services.DatosInventarioInvalidos):
            services.editar_tela(tela, {campo: valor})


@pytest.mark.django_db
def test_captura_consumo_valida_rol_estado_y_datos(contexto_consumo):
    datos = contexto_consumo
    with pytest.raises(PermissionError):
        services.registrar_consumos(
            datos["pedido"],
            [{"tela": datos["tela"].pk, "metros_usados": "1.00"}],
            datos["costurera"],
        )
    with pytest.raises(services.DatosInventarioInvalidos):
        services.registrar_consumos(datos["pedido"], [], datos["recepcion"])
    for uso in (
        {"tela": True, "metros_usados": "1.00"},
        {"tela": datos["tela"].pk, "metros_usados": "0"},
    ):
        with pytest.raises(services.DatosInventarioInvalidos):
            services.registrar_consumos(datos["pedido"], [uso], datos["recepcion"])
    with pytest.raises(services.TelaNoEncontrada):
        services.registrar_consumos(
            datos["pedido"],
            [{"tela": 9999, "metros_usados": "1.00"}],
            datos["recepcion"],
        )
