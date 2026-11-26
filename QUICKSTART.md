# TRT CLI - Guía rápida (Windows)

Primeros pasos con `trt` en un PC con Windows: instalar, encontrar una placa, comprobar que su
firmware corresponde a la placa hija conectada y actualizarlo si no. Referencia completa en inglés:
[README](README.md) y [docs/cli-reference.md](docs/cli-reference.md).

## Requisitos

| Qué | Para qué |
|---|---|
| Python 3.13 o superior | Siempre |
| Git | Descargar el código |
| Una placa con firmware TRT-Core (p. ej. STM32 NUCLEO-L073RZ) conectada por USB | Hablar con hardware |
| Repositorio TRT-core, junto a TRT-cli | Compilar, grabar y actualizar firmware (`trt list-modes`, `trt build`, `trt flash`, `trt board update`) |
| STM32CubeIDE (instalado en `C:\ST`) | Compilar y grabar STM32; el CLI encuentra sus herramientas solo |

Las dependencias de Python (Typer, Rich, pyserial) se instalan con TRT.

## 1. Instalar

1. **Instala Python 3.13+** desde <https://www.python.org/downloads/> y marca
   **"Add python.exe to PATH"**. Comprueba en PowerShell:

   ```powershell
   python --version
   ```

2. **Descarga el código** (TRT-core al lado de TRT-cli):

   ```powershell
   mkdir trt; cd trt
   git clone https://github.com/AntonioTRT/TRT-cli.git
   git clone https://github.com/AntonioTRT/TRT-core.git
   cd TRT-cli
   ```

3. **Crea un entorno virtual e instala TRT:**

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -e .
   ```

   Si PowerShell no permite ejecutar `Activate.ps1`, ejecuta una vez
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

4. **Comprueba que funciona** (desde cualquier carpeta, con el entorno activo):

   ```powershell
   trt version
   trt
   ```

   `trt version` muestra `Version: 1.0.0`; `trt` solo muestra la guía rápida (*Quick Start*).
   Si aparece `'trt' is not recognized`, activa el entorno virtual o usa `python -m trt`.

## 2. Encontrar la placa

Conecta la placa por USB y ejecuta:

```powershell
trt discover
```

```text
Connected Boards
Addr  Name           Firmware       Mode              HWID         Status
201   am-modulation  0.1.0 #000001  mode_0002_analog  0010 / 0010  MATCH
HWID: read from hardware / expected by the installed mode
```

- **Addr**: la dirección de la placa (201). Es el número que usan los demás comandos.
- **Mode**: el modo de firmware instalado.
- **HWID**: HWID leído de la placa hija / HWID que espera el modo instalado.
- **Status**: `MATCH` = todo correcto; `MISMATCH` = hay que actualizar.

Sin placa conectada, `trt discover` muestra `Found 0 board(s)`.

## 3. Revisar y actualizar

```powershell
trt board info 201        # detalle de la placa
trt board hwid 201        # qué placa hija está conectada
trt board mode 201        # qué modo está instalado
trt board update 201      # si hay MISMATCH: compila, graba, reinicia y verifica
```

`trt board update 201` termina con `Updated and verified: ... is active.` Con `--check` solo informa
(código de salida 0 = MATCH, 1 = no MATCH).

**Primera vez con una placa de firmware antiguo** (estado `NO HWID`):

```powershell
trt build stm32 mode_0000_base
trt flash stm32
trt discover
trt board update 201
```

## 4. Vigilar la placa

```powershell
trt listen
```

Muestra `Board 201: HEARTBEAT` una vez por segundo: el firmware funciona y la conexión placa → PC
está bien. Ctrl+C para salir (mientras escucha, el puerto está ocupado para otros comandos).

## Conceptos

| Término | Qué es |
|---|---|
| Dirección (*address*) | Cómo habla TRT con la placa: `201`. No identifica hardware. |
| HWID | Código de la placa hija conectada (`0010` = analógica). |
| Board ID | Identificador futuro de la placa base. Aún no existe. |
| Modo | Firmware instalado, `mode_<ID>_<nombre>`; el ID es el HWID para el que está hecho. `mode_0000_base` = Modo Base (sin placa hija, recuperación y mantenimiento). |

Más ayuda en el propio CLI: `trt` (guía rápida), `trt --help` (todos los comandos) y `trt help`
(conceptos, MATCH/MISMATCH, flujo de trabajo, heartbeat).

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `Found 0 board(s)` | Comprueba el cable y el puerto COM (*Administrador de dispositivos → Puertos*). Cierra monitores serie y cualquier `trt listen`. |
| `could not open port` | Otro programa usa el puerto; ciérralo. |
| `only event frames` una vez | Repite el comando. Si pasa siempre, reinicia la placa o actualízala. |
| `Missing build tools` / `STM32_Programmer_CLI not found` | Instala STM32CubeIDE en `C:\ST`. |
| `Could not locate the STM32CubeIDE project` | Clona TRT-core junto a TRT-cli o usa `--project-dir`. |
| `trt stm32 test` falla con `expected 0x0002` | Usa `trt stm32 test --board-id 201`. |

Más casos: [README → Troubleshooting](README.md#troubleshooting).

## Actualizar / desinstalar

La instalación es editable: tras `git pull` los cambios se aplican al momento. Solo hay que repetir
`python -m pip install -e .` si cambian las dependencias.

```powershell
python -m pip uninstall trt-cli
```

## Desarrollo

```powershell
python -m pip install -e ".[dev]"
pytest
```

5 pruebas de `tests/test_cli.py` necesitan un Arduino Uno con TRT-Core en la dirección 101; sin él
fallan y el resto (130) pasan. Para añadir comandos: [docs/adding-commands.md](docs/adding-commands.md).
