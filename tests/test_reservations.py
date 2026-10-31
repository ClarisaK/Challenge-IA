import pytest
from pathlib import Path
from src.inventory import Inventory
from src.reservation_service import ReservationService


@pytest.fixture
def temp_service(tmp_path):
    storage = tmp_path / "reservations.json"
    inventory = Inventory()
    return ReservationService(inventory=inventory, storage_path=storage)


def test_user_validation_success(temp_service):
    res = temp_service.create_reservation(
        unit_id="MIC-01",
        user="  Dr. Alan Turing  ",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T12:00",
    )
    assert res["user"] == "Dr. Alan Turing"
    assert res["status"] == ReservationService.STATUS_ACTIVE


@pytest.mark.parametrize("invalid_user", [None, "", "   ", "\t\n"])
def test_user_validation_failure(temp_service, invalid_user):
    with pytest.raises(ValueError, match="El solicitante no puede ser nulo"):
        temp_service.create_reservation(
            unit_id="MIC-01",
            user=invalid_user,
            start_time="2026-11-01T10:00",
            end_time="2026-11-01T12:00",
        )


def test_unit_must_exist_in_inventory(temp_service):
    with pytest.raises(ValueError, match="no existe en el inventario"):
        temp_service.create_reservation(
            unit_id="INVENTADO-99",
            user="Dra. Ada Lovelace",
            start_time="2026-11-01T10:00",
            end_time="2026-11-01T12:00",
        )


@pytest.mark.parametrize("invalid_date", ["2026/11/01 10:00", "invalid-date", "", "10:00"])
def test_invalid_date_format(temp_service, invalid_date):
    with pytest.raises(ValueError, match="Formato de fecha inválido|La fecha debe ser"):
        temp_service.create_reservation(
            unit_id="MIC-01",
            user="Dra. Ada Lovelace",
            start_time=invalid_date,
            end_time="2026-11-01T12:00",
        )


def test_start_time_must_be_strictly_before_end_time(temp_service):
    with pytest.raises(ValueError, match="inicio < fin"):
        temp_service.create_reservation(
            unit_id="MIC-01",
            user="Dra. Ada Lovelace",
            start_time="2026-11-01T10:00",
            end_time="2026-11-01T10:00",
        )

    with pytest.raises(ValueError, match="inicio < fin"):
        temp_service.create_reservation(
            unit_id="MIC-01",
            user="Dra. Ada Lovelace",
            start_time="2026-11-01T12:00",
            end_time="2026-11-01T10:00",
        )



def test_overlap_rejection_exact_same_range(temp_service):
    temp_service.create_reservation(
        unit_id="OSC-01",
        user="Dra. Ada",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T12:00",
    )
    with pytest.raises(ValueError, match="no está disponible"):
        temp_service.create_reservation(
            unit_id="OSC-01",
            user="Otro Usuario",
            start_time="2026-11-01T10:00",
            end_time="2026-11-01T12:00",
        )


def test_overlap_rejection_partial_cases(temp_service):
    temp_service.create_reservation(
        unit_id="OSC-01",
        user="Dra. Ada",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T12:00",
    )
    # Contenida (10:30 a 11:30)
    with pytest.raises(ValueError, match="no está disponible"):
        temp_service.create_reservation(
            unit_id="OSC-01",
            user="Usuario B",
            start_time="2026-11-01T10:30",
            end_time="2026-11-01T11:30",
        )
    # Envolvente (09:00 a 13:00)
    with pytest.raises(ValueError, match="no está disponible"):
        temp_service.create_reservation(
            unit_id="OSC-01",
            user="Usuario C",
            start_time="2026-11-01T09:00",
            end_time="2026-11-01T13:00",
        )
    # Solapa al inicio (09:30 a 10:30)
    with pytest.raises(ValueError, match="no está disponible"):
        temp_service.create_reservation(
            unit_id="OSC-01",
            user="Usuario D",
            start_time="2026-11-01T09:30",
            end_time="2026-11-01T10:30",
        )
    # Solapa al final (11:30 a 12:30)
    with pytest.raises(ValueError, match="no está disponible"):
        temp_service.create_reservation(
            unit_id="OSC-01",
            user="Usuario E",
            start_time="2026-11-01T11:30",
            end_time="2026-11-01T12:30",
        )


def test_consecutive_reservations_allowed(temp_service):
    res1 = temp_service.create_reservation(
        unit_id="MUL-01",
        user="Investigador 1",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T11:00",
    )
    res2 = temp_service.create_reservation(
        unit_id="MUL-01",
        user="Investigador 2",
        start_time="2026-11-01T11:00",
        end_time="2026-11-01T12:00",
    )
    res3 = temp_service.create_reservation(
        unit_id="MUL-01",
        user="Investigador 3",
        start_time="2026-11-01T09:00",
        end_time="2026-11-01T10:00",
    )
    assert res1["id"] != res2["id"] != res3["id"]


def test_simultaneous_reservations_different_units(temp_service):
    res1 = temp_service.create_reservation(
        unit_id="MIC-01",
        user="Investigador 1",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T12:00",
    )
    res2 = temp_service.create_reservation(
        unit_id="MIC-02",
        user="Investigador 2",
        start_time="2026-11-01T10:00",
        end_time="2026-11-01T12:00",
    )
    assert res1["unit_id"] == "MIC-01"
    assert res2["unit_id"] == "MIC-02"


def test_cancellation_frees_slot(temp_service):
    res = temp_service.create_reservation(
        unit_id="FUE-01",
        user="Investigador",
        start_time="2026-11-01T14:00",
        end_time="2026-11-01T16:00",
    )
    assert not temp_service.is_unit_available("FUE-01", "2026-11-01T14:00", "2026-11-01T16:00")

    cancelled = temp_service.cancel_reservation(res["id"])
    assert cancelled["status"] == ReservationService.STATUS_CANCELLED

    assert temp_service.is_unit_available("FUE-01", "2026-11-01T14:00", "2026-11-01T16:00")
    new_res = temp_service.create_reservation(
        unit_id="FUE-01",
        user="Nuevo Investigador",
        start_time="2026-11-01T14:00",
        end_time="2026-11-01T16:00",
    )
    assert new_res["status"] == ReservationService.STATUS_ACTIVE
