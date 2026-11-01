import sys
from pathlib import Path
from typing import Callable, Optional

from src.inventory import Inventory
from src.reservation_service import DEFAULT_RESERVATIONS_PATH, ReservationService


class LabReservationCLI:
    """CLI interactiva para el sistema de reservas de laboratorio."""

    def __init__(
        self,
        service: Optional[ReservationService] = None,
        inventory: Optional[Inventory] = None,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> None:
        self.input_fn = input_fn
        self.print_fn = print_fn
        self.inventory = inventory if inventory is not None else Inventory()
        self.service = (
            service
            if service is not None
            else ReservationService(inventory=self.inventory, storage_path=DEFAULT_RESERVATIONS_PATH)
        )

    def print_menu(self) -> None:
        self.print_fn("\n" + "=" * 45)
        self.print_fn("   SISTEMA DE RESERVAS DE LABORATORIO")
        self.print_fn("=" * 45)
        self.print_fn("1. Ver catálogo de unidades del laboratorio")
        self.print_fn("2. Consultar disponibilidad de una unidad en un rango horario [inicio, fin)")
        self.print_fn("3. Crear una nueva reserva")
        self.print_fn("4. Listar todas las reservas existentes")
        self.print_fn("5. Cancelar una reserva por ID")
        self.print_fn("0. Salir")
        self.print_fn("=" * 45)

    def handle_view_catalog(self) -> None:
        self.print_fn("\n--- Catálogo de Unidades ---")
        units = self.inventory.get_all()
        if not units:
            self.print_fn("No hay unidades registradas en el inventario.")
            return
        for unit in units:
            self.print_fn(f"- [{unit.get('id')}] {unit.get('name')}")

    def handle_check_availability(self) -> None:
        self.print_fn("\n--- Consultar Disponibilidad ---")
        unit_id = self.input_fn("ID de la unidad: ").strip()
        start_time = self.input_fn("Fecha y hora de inicio (YYYY-MM-DDTHH:MM): ").strip()
        end_time = self.input_fn("Fecha y hora de fin (YYYY-MM-DDTHH:MM): ").strip()

        if not self.inventory.exists(unit_id):
            self.print_fn(f"Error: La unidad '{unit_id}' no existe en el inventario.")
            return

        try:
            available = self.service.is_unit_available(unit_id, start_time, end_time)
            msg = "está DISPONIBLE" if available else "NO está disponible"
            self.print_fn(f"Resultado: La unidad '{unit_id}' {msg} en el rango [{start_time}, {end_time}).")
        except ValueError as err:
            self.print_fn(f"Error: {err}")

    def handle_create_reservation(self) -> None:
        self.print_fn("\n--- Crear Nueva Reserva ---")
        unit_id = self.input_fn("ID de la unidad: ").strip()
        user = self.input_fn("Nombre del solicitante: ")
        start_time = self.input_fn("Fecha y hora de inicio (YYYY-MM-DDTHH:MM): ").strip()
        end_time = self.input_fn("Fecha y hora de fin (YYYY-MM-DDTHH:MM): ").strip()

        try:
            res = self.service.create_reservation(
                unit_id=unit_id,
                user=user,
                start_time=start_time,
                end_time=end_time,
            )
            self.print_fn("\n¡Reserva creada exitosamente!")
            self.print_fn(f"  ID: {res['id']}")
            self.print_fn(f"  Unidad: {res['unit_id']}")
            self.print_fn(f"  Solicitante: {res['user']}")
            self.print_fn(f"  Inicio: {res['start_time']}")
            self.print_fn(f"  Fin: {res['end_time']}")
            self.print_fn(f"  Estado: {res['status']}")
        except ValueError as err:
            self.print_fn(f"Error al crear reserva: {err}")

    def handle_list_reservations(self) -> None:
        self.print_fn("\n--- Listado de Reservas ---")
        reservations = self.service.get_reservations()
        if not reservations:
            self.print_fn("No hay reservas registradas.")
            return

        for idx, res in enumerate(reservations, 1):
            self.print_fn(
                f"{idx}. [{res.get('status')}] ID: {res.get('id')} | "
                f"Unidad: {res.get('unit_id')} | Solicitante: {res.get('user')} | "
                f"Rango: {res.get('start_time')} -> {res.get('end_time')}"
            )

    def handle_cancel_reservation(self) -> None:
        self.print_fn("\n--- Cancelar Reserva ---")
        res_id = self.input_fn("ID de la reserva a cancelar: ").strip()
        if not res_id:
            self.print_fn("Error: Debe ingresar un ID de reserva.")
            return

        try:
            cancelled = self.service.cancel_reservation(res_id)
            self.print_fn(f"Reserva '{cancelled['id']}' cancelada exitosamente.")
        except (KeyError, ValueError) as err:
            self.print_fn(f"Error al cancelar: {err}")

    def run(self) -> None:
        self.print_fn("Bienvenido al Sistema de Reservas de Laboratorio.")
        while True:
            try:
                self.print_menu()
                choice = self.input_fn("Seleccione una opción: ").strip()

                if choice == "1":
                    self.handle_view_catalog()
                elif choice == "2":
                    self.handle_check_availability()
                elif choice == "3":
                    self.handle_create_reservation()
                elif choice == "4":
                    self.handle_list_reservations()
                elif choice == "5":
                    self.handle_cancel_reservation()
                elif choice == "0":
                    self.print_fn("Gracias por utilizar el sistema. ¡Hasta luego!")
                    break
                else:
                    self.print_fn(f"Opción inválida: '{choice}'. Por favor seleccione una opción del menú.")
            except (KeyboardInterrupt, EOFError):
                self.print_fn("\nOperación interrumpida por el usuario. Saliendo...")
                break


def main() -> None:
    cli = LabReservationCLI()
    cli.run()


if __name__ == "__main__":
    main()

