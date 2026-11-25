import pytest

from usuarios.tests.conftest import ClientSeguro


@pytest.fixture
def client():
    return ClientSeguro()
