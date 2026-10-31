import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_INVENTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.json"


class Inventory:
    """Gestiona el inventario de equipos del laboratorio."""

    def __init__(self, file_path: Optional[Path | str] = None) -> None:
        self.file_path = Path(file_path) if file_path else DEFAULT_INVENTORY_PATH
        self._items: List[Dict[str, Any]] = []
        self._items_by_id: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Carga el inventario desde el archivo JSON especificado."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Inventario no encontrado en: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("El archivo de inventario debe contener una lista de equipos.")

        self._items = data
        self._items_by_id = {item["id"]: item for item in self._items if "id" in item}

    def exists(self, unit_id: str) -> bool:
        """Verifica si un ID de unidad existe en el inventario."""
        if not unit_id:
            return False
        return unit_id in self._items_by_id

    def get_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de una unidad por su ID."""
        return self._items_by_id.get(unit_id)

    def get_all(self) -> List[Dict[str, Any]]:
        """Devuelve la lista completa de unidades registradas."""
        return list(self._items)
