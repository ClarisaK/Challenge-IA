import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.inventory import Inventory

DEFAULT_RESERVATIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "reservations.json"


class ReservationService:
    STATUS_ACTIVE = "ACTIVA"
    STATUS_CANCELLED = "CANCELADA"

    def __init__(
        self,
        inventory: Optional[Inventory] = None,
        storage_path: Optional[Union[Path, str]] = None,
    ) -> None:
        self.inventory = inventory if inventory is not None else Inventory()
        self.storage_path = Path(storage_path) if storage_path else DEFAULT_RESERVATIONS_PATH
        self._reservations: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path and self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._reservations = data
                except (json.JSONDecodeError, OSError):
                    self._reservations = []
        else:
            self._reservations = []

    def _save(self) -> None:
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._reservations, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_iso_datetime(dt_str: str) -> datetime:
        if not isinstance(dt_str, str) or not dt_str.strip():
            raise ValueError("La fecha debe ser una cadena de texto no vacía.")
        try:
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Formato de fecha inválido '{dt_str}'. Debe ser ISO 8601 (YYYY-MM-DDTHH:MM).") from exc

    @staticmethod
    def check_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
        """Determina si dos intervalos semiabiertos [inicio, fin) se solapan:
        max(inicio_A, inicio_B) < min(fin_A, fin_B)
        """
        return max(start_a, start_b) < min(end_a, end_b)

    def is_unit_available(
        self,
        unit_id: str,
        start_time: Union[str, datetime],
        end_time: Union[str, datetime],
        exclude_reservation_id: Optional[str] = None,
    ) -> bool:
        start_dt = start_time if isinstance(start_time, datetime) else self._parse_iso_datetime(start_time)
        end_dt = end_time if isinstance(end_time, datetime) else self._parse_iso_datetime(end_time)

        if start_dt >= end_dt:
            raise ValueError("La fecha de inicio debe ser estrictamente anterior a la de fin.")

        for res in self._reservations:
            if res.get("status") != self.STATUS_ACTIVE:
                continue
            if res.get("unit_id") != unit_id:
                continue
            if exclude_reservation_id and res.get("id") == exclude_reservation_id:
                continue

            existing_start = self._parse_iso_datetime(res["start_time"])
            existing_end = self._parse_iso_datetime(res["end_time"])

            if self.check_overlap(start_dt, end_dt, existing_start, existing_end):
                return False

        return True

    def create_reservation(
        self,
        unit_id: str,
        user: str,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        if user is None or not isinstance(user, str) or not user.strip():
            raise ValueError("El solicitante no puede ser nulo ni estar compuesto únicamente por espacios.")
        user_clean = user.strip()

        if not self.inventory.exists(unit_id):
            raise ValueError(f"La unidad '{unit_id}' no existe en el inventario.")

        start_dt = self._parse_iso_datetime(start_time)
        end_dt = self._parse_iso_datetime(end_time)
        if start_dt >= end_dt:
            raise ValueError("La fecha de inicio debe ser estrictamente anterior a la fecha de fin (inicio < fin).")

        if not self.is_unit_available(unit_id, start_dt, end_dt):
            raise ValueError(f"La unidad '{unit_id}' no está disponible en el horario solicitado.")

        reservation = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "user": user_clean,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "status": self.STATUS_ACTIVE,
        }
        self._reservations.append(reservation)
        self._save()
        return reservation

    def cancel_reservation(self, reservation_id: str) -> Dict[str, Any]:
        for res in self._reservations:
            if res.get("id") == reservation_id:
                if res.get("status") == self.STATUS_CANCELLED:
                    raise ValueError("La reserva ya se encuentra cancelada.")
                res["status"] = self.STATUS_CANCELLED
                self._save()
                return res

        raise KeyError(f"No se encontró ninguna reserva con ID '{reservation_id}'.")

    def get_reservations(
        self,
        unit_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = self._reservations
        if unit_id is not None:
            results = [r for r in results if r.get("unit_id") == unit_id]
        if status is not None:
            results = [r for r in results if r.get("status") == status]
        return list(results)
