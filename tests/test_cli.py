import pytest
from unittest.mock import patch
from src.cli import LabReservationCLI, main
from src.inventory import Inventory
from src.reservation_service import ReservationService


class MockInput:
    def __init__(self, inputs):
        self.inputs = list(inputs)

    def __call__(self, prompt=""):
        if not self.inputs:
            raise EOFError("No more mock inputs")
        return self.inputs.pop(0)


class MockOutput:
    def __init__(self):
        self.messages = []

    def __call__(self, *args, **kwargs):
        self.messages.append(" ".join(str(a) for a in args))

    def get_output(self):
        return "\n".join(self.messages)


@pytest.fixture
def cli_setup(tmp_path):
    storage = tmp_path / "reservations.json"
    inventory = Inventory()
    service = ReservationService(inventory=inventory, storage_path=storage)
    return inventory, service


def test_cli_exit(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Bienvenido al Sistema de Reservas de Laboratorio" in out
    assert "Gracias por utilizar el sistema" in out


def test_cli_invalid_option(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["99", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Opción inválida: '99'" in out


def test_cli_view_catalog(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["1", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Catálogo de Unidades" in out
    assert "[MIC-01] Microscopio digital" in out
    assert "[MIC-02] Microscopio digital" in out
    assert "[OSC-01] Osciloscopio" in out
    assert "[MUL-01] Multímetro" in out
    assert "[FUE-01] Fuente de alimentación" in out


def test_cli_check_availability_success(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["2", "MIC-01", "2026-11-01T10:00", "2026-11-01T12:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "está DISPONIBLE" in out

def test_cli_check_availability_occupied(cli_setup):
    _, service = cli_setup
    service.create_reservation("MIC-01", "Dra. Turing", "2026-11-01T10:00", "2026-11-01T12:00")

    mock_input = MockInput(["2", "MIC-01", "2026-11-01T11:00", "2026-11-01T13:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "NO está disponible" in out


def test_cli_check_availability_unit_not_exists(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["2", "INEXISTENTE", "2026-11-01T10:00", "2026-11-01T12:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Error: La unidad 'INEXISTENTE' no existe en el inventario." in out


def test_cli_check_availability_invalid_dates(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["2", "MIC-01", "fecha-invalida", "2026-11-01T12:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Error:" in out


def test_cli_create_reservation_success(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["3", "MIC-01", "Alice", "2026-11-01T10:00", "2026-11-01T12:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "¡Reserva creada exitosamente!" in out
    assert "Unidad: MIC-01" in out
    assert "Solicitante: Alice" in out
    assert "Estado: ACTIVA" in out
    assert len(service.get_reservations()) == 1


def test_cli_create_reservation_validation_errors(cli_setup):
    _, service = cli_setup
    mock_input = MockInput([
        "3", "MIC-01", "   ", "2026-11-01T10:00", "2026-11-01T12:00",
        "3", "INVALID-UNIT", "Alice", "2026-11-01T10:00", "2026-11-01T12:00",
        "3", "MIC-01", "Alice", "2026-11-01T12:00", "2026-11-01T10:00",
        "0"
    ])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Error al crear reserva: El solicitante no puede ser nulo" in out
    assert "Error al crear reserva: La unidad 'INVALID-UNIT' no existe en el inventario." in out
    assert "Error al crear reserva: La fecha de inicio debe ser estrictamente anterior a la fecha de fin" in out


def test_cli_create_reservation_overlap_error(cli_setup):
    _, service = cli_setup
    service.create_reservation("OSC-01", "Investigador 1", "2026-11-01T10:00", "2026-11-01T12:00")

    mock_input = MockInput(["3", "OSC-01", "Investigador 2", "2026-11-01T11:00", "2026-11-01T13:00", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Error al crear reserva: La unidad 'OSC-01' no está disponible en el horario solicitado." in out


def test_cli_list_reservations_empty(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["4", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "No hay reservas registradas." in out


def test_cli_list_reservations_with_items(cli_setup):
    _, service = cli_setup
    service.create_reservation("MUL-01", "Investigador A", "2026-11-01T08:00", "2026-11-01T09:00")

    mock_input = MockInput(["4", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Listado de Reservas" in out
    assert "Unidad: MUL-01" in out
    assert "Solicitante: Investigador A" in out


def test_cli_cancel_reservation_success(cli_setup):
    _, service = cli_setup
    res = service.create_reservation("FUE-01", "Investigador B", "2026-11-01T14:00", "2026-11-01T16:00")
    res_id = res["id"]

    mock_input = MockInput(["5", res_id, "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert f"Reserva '{res_id}' cancelada exitosamente." in out
    assert service.get_reservations()[0]["status"] == ReservationService.STATUS_CANCELLED


def test_cli_cancel_reservation_errors(cli_setup):
    _, service = cli_setup
    mock_input = MockInput(["5", "   ", "5", "id-inexistente", "0"])
    mock_output = MockOutput()

    cli = LabReservationCLI(service=service, input_fn=mock_input, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Error: Debe ingresar un ID de reserva." in out
    assert "No se encontró ninguna reserva con ID 'id-inexistente'" in out


def test_cli_interrupt_handling(cli_setup):
    _, service = cli_setup

    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt()

    mock_output = MockOutput()
    cli = LabReservationCLI(service=service, input_fn=raise_interrupt, print_fn=mock_output)
    cli.run()

    out = mock_output.get_output()
    assert "Operación interrumpida por el usuario. Saliendo..." in out


def test_main_entrypoint():
    with patch("src.cli.LabReservationCLI.run") as mock_run:
        main()
        mock_run.assert_called_once()

