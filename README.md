# Sistema de Reservas para Laboratorio - Challenge IA

Sistema interactivo de gestión y verificación de reservas para recursos de laboratorio, desarrollado mediante un modelo de programación autónoma supervisada utilizando el agente Cline en VS Code, con control de versiones en Git y verificación formal mediante pruebas unitarias en `pytest`.

---

## 1. Contexto de Negocio y Reglas Críticas

El sistema administra recursos físicos compartidos con disponibilidad limitada y reglas estrictas de persistencia e integridad de datos:

1. **Catálogo de Inventario Precargado (Solo Lectura):**
   - `MIC-01`: Microscopio digital
   - `MIC-02`: Microscopio digital
   - `OSC-01`: Osciloscopio
   - `MUL-01`: Multímetro digital
   - `FUE-01`: Fuente regulable

2. **Validaciones de Solicitud:**
   - Existencia estricta de la unidad en el catálogo precargado (`data/inventory.json`).
   - Identificador del solicitante no nulo ni compuesto exclusivamente por espacios en blanco (`solicitante.strip()`).
   - Formato temporal estándar ISO 8601 (`YYYY-MM-DDTHH:MM`).
   - Consistencia temporal: `start_time < end_time`.

3. **Lógica de Superposición y Turnos Contiguos:**
   - La condición estricta de solapamiento entre dos intervalos $[A_{inicio}, A_{fin})$ y $[B_{inicio}, B_{fin})$ para un mismo recurso es:
     $$\max(A_{inicio}, B_{inicio}) < \min(A_{fin}, B_{fin})$$
   - El uso de desigualdad estricta ($<$) permite admitir turnos contiguos exactos (por ejemplo, 10:00–11:00 y 11:00–12:00) sin generar falsas colisiones.
   - Recursos distintos pueden operar simultáneamente en el mismo intervalo sin restricciones cruzadas.

---

## 2. Pila Tecnológica y Arquitectura

* **Lenguaje:** Python 3.13+
* **Framework de Pruebas:** `pytest` (36 casos de prueba unitarios e integrados al 100% de éxito)
* **Persistencia:** Archivos JSON estructurados (`data/inventory.json` y `data/reservations.json`)
* **Entorno de Delegación:** VS Code + Cline Extension
* **Modelos LLM:** Google Gemini API 

### Estructura del Repositorio

```text
challenge-agents-topicos/
├── .clinerules              # Reglas de gobernanza y directivas para el agente
├── .gitignore               # Exclusión de entornos virtuales y cachés (__pycache__)
├── requirements.txt         # Especificación de dependencias reproducibles
├── main.py                  # Punto de entrada de la aplicación
├── data/
│   ├── inventory.json       # Catálogo estático de unidades
│   └── reservations.json    # Registro persistente de reservas
├── src/
│   ├── __init__.py
│   ├── inventory.py         # Módulo de carga y consulta de inventario
│   ├── reservation_service.py # Lógica de negocio y motor de colisiones
│   └── cli.py               # Interfaz interactiva por consola
└── tests/
    ├── __init__.py
    ├── test_inventory.py    # Pruebas del catálogo fijo (4 tests)
    ├── test_reservations.py # Pruebas del servicio y solapamientos (16 tests)
    └── test_cli.py          # Pruebas de interfaz y mocks de consola (16 tests)
```

---

## 3. Gobernanza, Supervisión Humana y Gestión de Riesgos

La interacción con el agente se rigió por un esquema de delegación acotada con validación humana previa a cada persistencia:

* **Control de Alcance y Bucles:** Se configuró `.clinerules` para forzar al agente a operar exclusivamente en el directorio del proyecto y evitar modificaciones fuera del ámbito. Ante exploraciones redundantes del agente (`Get-ChildItem -Recurse`), se intervino cancelando la acción para mantener el consumo de contexto controlado.
* **Tolerancia a Fallos de Cuota (Fallback):** Durante el desarrollo se identificaron agotamientos de cuota en el proveedor base de API; se gestionaron mediante directivas desacopladas y correcciones manuales directas en los puntos de mock.
* **Criterios de Aceptación:** Ningún archivo fue incorporado al historial de Git sin antes ejecutar `pytest -v` y verificar el 100% de éxito en los casos de prueba.

### 3.1. Entorno, Versión e Identificador del Modelo
* **Entorno de ejecución del agente:** Extensión Cline (v3.x) integrada en Visual Studio Code sobre sistema operativo Windows 10/11 x64.
* **Proveedor de API / Plataforma:** Google AI Studio (Gemini API) a través de claves de autenticación en entorno seguro.
* **Identificador exacto del modelo:** `gemini-2.5-flash` / `gemini-2.0-flash` (identificado en la interfaz de Cline como familia `gemini-flash`).
* **Función asignada:** Desarrollador principal autónomo subordinado a supervisión humana, responsable de la generación de código modular, refactorizaciones y creación de pruebas automatizadas en `pytest`.
* **Motivo de la elección:** Ventana de contexto amplia (1.0M tokens), baja latencia de respuesta para edición de código en bucle y soporte nativo para invocación de herramientas CLI.
* **Transparencia de datos no visibles:** La temperatura exacta del modelo y los hiperparámetros de muestreo internos son gestionados internamente por la extensión Cline bajo la configuración predeterminada del backend, sin exposición explícita en la interfaz gráfica.

### 3.2. Instrucciones y Configuraciones Utilizadas (Saneadas) y Gestión de Contexto
* **Archivo de Gobernanza (`.clinerules`):**
  Se estableció una directiva restrictiva en la raíz del repositorio con el siguiente contenido saneado:
``` text
 # Reglas del Sistema de Reservas de Laboratorio

Eres un agente de programación encargado de construir un sistema de reservas verificable para laboratorios.

## Reglas de Negocio Estrictas:
1. Inventario Precargado (Fijo, solo lectura):
   - MIC-01: Microscopio digital
   - MIC-02: Microscopio digital
   - OSC-01: Osciloscopio
   - MUL-01: Multímetro
   - FUE-01: Fuente de alimentación
2. Validaciones:
   - Unidad existente en el inventario.
   - Solicitante no nulo ni compuesto exclusivamente por espacios en blanco.
   - Fechas válidas en formato ISO 8601 (YYYY-MM-DDTHH:MM), con inicio estrictamente anterior al fin (inicio < fin).
3. Reglas de Disponibilidad y Solapamiento:
   - Una reserva activa ocupa el intervalo [inicio, fin).
   - Se solapan si: max(inicio_A, inicio_B) < min(fin_A, fin_B).
   - Rechazar superposiciones de reservas activas sobre la misma unidad.
   - Permitir turnos consecutivos exactos (ej. 10:00 a 11:00 y 11:00 a 12:00 en la misma unidad).
   - Permitir reservas simultáneas de unidades distintas (ej. MIC-01 y MIC-02 al mismo tiempo).
4. Cancelaciones y Persistencia:
   - Cancelar conserva el registro y su ID cambiando su estado a CANCELADA, liberando inmediatamente el horario.
   - Persistir en un archivo local JSON (data/reservations.json) para recuperar estado tras reinicios.

## Directivas de Desarrollo:
- Toda modificación debe acompañarse de pruebas con `pytest`.
- Mantén el código desacoplado: persistencia, lógica de dominio y CLI separados.
 ```
* **Contexto Suministrado:**
  - Estructura base del proyecto (`src/`, `data/`, `tests/`).
  - Especificación formal del catálogo de 5 recursos (`MIC-01`, `MIC-02`, `OSC-01`, `MUL-01`, `FUE-01`).
  - Restricción estricta de validación temporal y cálculo matemático de colisiones.
* **Contexto Excluido Deliberadamente:**
  - Credenciales y claves de API (gestionadas fuera del código y nunca rastreadas por Git).
  - Entorno virtual (`.venv/`) y cachés compiladas de Python (`__pycache__/`, `*.pyc`), excluidos vía `.gitignore` para prevenir polución de contexto y consumo innecesario de tokens.

### 3.3. Herramientas, Acciones Permitidas y Protocolo de Aprobación Humana
* **Herramientas Habilitadas al Agente:**
  1. `Read File`: Inspección de archivos de configuración y código existente.
  2. `Write / Edit File`: Propuesta de modificaciones mediante diffs interactivos.
  3. `Execute Command`: Ejecución supervisada de comandos de terminal en PowerShell (ejecución de pruebas `pytest` y lectura controlada del árbol de directorios).
* **Protocolo de Control y Aprobaciones Humanas:**
  - **Revisión previa de diffs:** Cada cambio de código fue revisado línea por línea en el panel de diferencias de VS Code antes de autorizar su escritura.
  - **Aprobación comando a comando:** Ningún comando de terminal se ejecutó con auto-aprobación indiscriminada; cada invocación requirió presionar manualmente `Run Command`.
  - **Cancelación preventiva de bucles:** Ante comandos de lectura excesiva o recursiva sobre dependencias del entorno (`Get-ChildItem -Recurse`), se intervino cancelando la tarea (`Cancel`/`Reject`) para evitar el agotamiento de contexto y consumo de cuota.

### 3.4. Adaptaciones Específicas Comprobables
* **Caso 1: Soporte Estricto de Turnos Consecutivos Contiguos**
  - **Regla de Negocio:** Permitir que una reserva finalice a las `11:00` y otra comience exactamente a las `11:00` sobre la misma unidad sin generar colisión.
  - **Implementación Matemática:** Se exigió y auditó el uso de la desigualdad estricta `<` en lugar de `<=`:
    $$\max(A_{inicio}, B_{inicio}) < \min(A_{fin}, B_{fin})$$
  - **Evidencia Comprobable en Código:** Función `test_consecutive_reservations_allowed` en `tests/test_reservations.py`, validada al 100% en el commit `12ea5e2`.
* **Caso 2: Aislamiento de Persistencia durante Pruebas**
  - **Procedimiento:** En lugar de modificar el archivo real `data/reservations.json` durante la batería de tests, se instruyó el uso de la fixture nativa `tmp_path` de `pytest`.
  - **Evidencia Comprobable:** Definición de `temp_service` en `tests/test_reservations.py` (`storage = tmp_path / "reservations.json"`), garantizando idempotencia y cero efectos secundarios en el repositorio versionado.

---

---

## 4. Evidencia de Delegación y Supervisión (Tres Episodios)

| Episodio | Tarea Delegada | Prompt Clave / Directiva | Comportamiento del Agente | Intervención / Corrección Humana | Validación y Hash de Commit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Núcleo de Reservas y Solapamientos** | Implementación de `src/reservation_service.py` y detección matemática de conflictos. | *"Implementa la validación ISO 8601, solapamiento estricto $\max(A, B) < \min(A, B)$ y turnos contiguos permitidos."* | El agente codificó el servicio y estructuró 16 tests con `tmp_path` fixture. | Se verificó visualmente en el diff que la condición utilizara `<` estricto y no `<=`. | 16 tests pasados. Commit: `12ea5e2` |
| **2. Interfaz de Usuario y CLI** | Creación de menú interactivo por consola y suite de pruebas simuladas. | *"Implementa `src/cli.py` con menú numérico, manejo de excepciones sin crash y tests con mocks."* | Generó la interfaz y 16 pruebas adicionales, pero `test_main_entrypoint` falló con `OSError` por captura de `stdin`. | Intervención manual en `tests/test_cli.py` mockeando `LabReservationCLI.run` para desacoplar el bucle de entrada nativo. | 36 tests pasados (100%). Commit: `58f71f4` |
| **3. Saneamiento de Repositorio y Git** | Exclusión de artefactos compilados y configuración de entorno reproducible. | *"Normaliza `.gitignore` y asegura exclusión de `.pyc` y cachés."* | El agente intentó múltiples comandos de lectura exploratoria de directorio sin avanzar en la reindexación. | Cancelación deliberada del agente (`Cancel/Reject`), saneamiento directo por consola (`git rm -r --cached .`) y actualización limpia. | Repositorio libre de binarios. Commit: `1d75622` |

---

## 5. Instrucciones de Reproducibilidad

### 1. Clonar el repositorio
```bash
git clone git@github.com:ClarisaK/Challenge-IA.git
cd Challenge-IA
```

### 2. Configurar el entorno virtual
```bash
python -m venv .venv
# En Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la suite de pruebas
```bash
pytest -v
```

### 5. Iniciar la aplicación interactiva
```bash
python main.py
```
