# TRT CLI - Referencia rápida

## Requisitos

```text
Paquete: trt-cli 1.0.0
Python: 3.13+
Dependencias: Typer, Rich, pyserial
Comando: trt
Hardware validado: Arduino Uno en COM4 con firmware TRT-Core
```

## Cómo ejecutar TRT en un PC (Windows)

1. **Instala Python 3.13 o superior** desde <https://www.python.org/downloads/>.
   En el instalador, marca **"Add python.exe to PATH"**.

2. **Abre una terminal** (PowerShell o Símbolo del sistema) y comprueba la versión:

   ```powershell
   python --version
   ```

3. **Descarga el código** y entra en la carpeta del repositorio:

   ```powershell
   git clone <repo-url> TRT-cli
   cd TRT-cli
   ```

4. **Instala TRT y sus dependencias:**

   ```powershell
   pip install -e .
   ```

   Esto instala Typer, Rich y pyserial, y añade el comando `trt` a la carpeta
   `Scripts` de Python.

5. **Comprueba que funciona.** Se puede ejecutar desde cualquier carpeta:

   ```powershell
   trt version
   trt --help
   ```

   Salida esperada de `trt version`:

   ```text
    TRT CLI
    Version:  1.0.0
   ```

   Si aparece `'trt' is not recognized`, la carpeta `Scripts` de Python no está
   en el PATH. Normalmente es
   `%LOCALAPPDATA%\Programs\Python\Python313\Scripts`. Puedes añadirla al PATH
   o usar `python -m trt` en su lugar.

6. **Conecta la placa.** Conecta por USB el Arduino Uno con el firmware
   TRT-Core. Debe aparecer como **COM4**; compruébalo en
   *Administrador de dispositivos → Puertos (COM y LPT)*. Después ejecuta:

   ```powershell
   trt discover
   trt boards
   trt board info 101
   ```

## Comandos principales

```bash
trt help
trt version
trt discover
trt boards
trt board info 101
trt board capabilities 101
```

Sin ninguna placa conectada, `trt discover` muestra `Found 0 board(s)` y
`trt boards` muestra `No boards detected`. `trt board info 101` falla con
`could not open port 'COM4'`. Es lo esperado cuando no hay nada conectado en COM4.

## Ruta de hardware validada

```text
TRT-CLI -> COM4 -> Arduino Uno -> TRT-Core -> respuesta real del protocolo
```

`trt board info 101` devuelve datos reales del firmware:

```text
Board ID      101
BOARD_INFO    UNSPECIFIED
FW_VERSION    0.1.0
BUILD_ID      000004
```

## Actualizar / desinstalar

La instalación es editable, así que los cambios en el código (por ejemplo,
después de `git pull`) se aplican al momento. Solo hay que volver a ejecutar
`pip install -e .` si cambian las dependencias.

```powershell
pip uninstall trt-cli
```

## Desarrollo

```powershell
pip install -e ".[dev]"
pytest
```

Algunas pruebas necesitan el Arduino Uno con TRT-Core conectado en COM4. Sin
él, fallan 5 pruebas y el resto pasan:

```text
TestBoardsCommand::test_boards_shows_discovered_real_board
TestBoardSubcommands::test_info_known_board
TestBoardSubcommands::test_status
TestBoardSubcommands::test_capabilities
TestBoardRegistry::test_discovery_service_populates_registry_from_transport
```
