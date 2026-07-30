"""Test suite for TRT CLI.

Covers:
    - Version functions
    - Core data models and board registry
    - Top-level CLI commands (help, version, update, boards, discover)
    - Board sub-commands (info, status, capabilities, gpio, pwm, adc, dac, i2c, spi, debug)
    - LCD, LED, Protocol command groups
    - Update service layer
    - Unknown command error handling
"""

import pytest
from typer.testing import CliRunner

from trt.cli import app
from trt.core.models import (
    Board,
    BoardCapabilities,
    BoardIdentity,
    BoardRegistry,
    BoardStatus,
    BoardType,
    TransportConfig,
    TransportType,
    make_mock_registry,
)
from trt.services.update_service import (
    InstallMethod,
    UpdateStatus,
    _is_newer,
    _parse_version,
    check_for_update,
    detect_install_method,
    install_update,
)
from trt.version import get_version, get_version_info

runner = CliRunner()


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class TestVersion:
    def test_get_version(self) -> None:
        assert get_version() == "0.1.0"

    def test_get_version_info(self) -> None:
        assert get_version_info() == (0, 1, 0)

    def test_version_command(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout
        assert "TRT CLI" in result.stdout


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

class TestHelpCommand:
    def test_help_command_exits_ok(self) -> None:
        result = runner.invoke(app, ["help"])
        assert result.exit_code == 0

    def test_help_shows_command_tree(self) -> None:
        result = runner.invoke(app, ["help"])
        assert "boards" in result.stdout
        assert "discover" in result.stdout
        assert "gpio" in result.stdout
        assert "pwm" in result.stdout

    def test_help_shows_update(self) -> None:
        result = runner.invoke(app, ["help"])
        assert "update" in result.stdout

    def test_no_args_shows_usage(self) -> None:
        result = runner.invoke(app, [])
        # Typer with no_args_is_help=True returns exit code 2 (no-op help)
        assert result.exit_code in (0, 2)


# ---------------------------------------------------------------------------
# Update command
# ---------------------------------------------------------------------------

class TestUpdateCommand:
    def test_update_exits_ok(self) -> None:
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0

    def test_update_shows_current_version(self) -> None:
        result = runner.invoke(app, ["update"])
        assert get_version() in result.stdout

    def test_update_check_flag(self) -> None:
        result = runner.invoke(app, ["update", "--check"])
        assert result.exit_code == 0

    def test_update_install_flag_no_crash(self) -> None:
        # install flag runs but falls through to Phase 1 placeholder
        result = runner.invoke(app, ["update", "--install"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Update service layer
# ---------------------------------------------------------------------------

class TestUpdateService:
    def test_parse_version_plain(self) -> None:
        assert _parse_version("0.1.0") == (0, 1, 0)

    def test_parse_version_with_v_prefix(self) -> None:
        assert _parse_version("v0.2.0") == (0, 2, 0)

    def test_parse_version_prerelease_stripped(self) -> None:
        assert _parse_version("v1.0.0-beta.1") == (1, 0, 0)

    def test_is_newer_true(self) -> None:
        assert _is_newer("0.2.0", "0.1.0") is True

    def test_is_newer_false_same(self) -> None:
        assert _is_newer("0.1.0", "0.1.0") is False

    def test_is_newer_false_older(self) -> None:
        assert _is_newer("0.0.9", "0.1.0") is False

    def test_check_for_update_returns_result(self) -> None:
        result = check_for_update()
        assert result.current_version == get_version()
        assert result.status in UpdateStatus.__members__.values()

    def test_check_for_update_phase1_up_to_date(self) -> None:
        # Phase 1: always returns UP_TO_DATE (no real HTTP)
        result = check_for_update()
        assert result.status == UpdateStatus.UP_TO_DATE

    def test_install_update_returns_result(self) -> None:
        result = install_update()
        assert isinstance(result.success, bool)
        assert isinstance(result.message, str)

    def test_detect_install_method_returns_method(self) -> None:
        method = detect_install_method()
        assert isinstance(method, InstallMethod)

    def test_upgrade_command_contains_package_name(self) -> None:
        result = check_for_update()
        assert "trt-cli" in result.upgrade_command


# ---------------------------------------------------------------------------
# Boards
# ---------------------------------------------------------------------------

class TestBoardsCommand:
    def test_boards_exits_ok(self) -> None:
        result = runner.invoke(app, ["boards"])
        assert result.exit_code == 0

    def test_boards_shows_mock_data(self) -> None:
        result = runner.invoke(app, ["boards"])
        # The mock registry has board0 (TRT_CORE) and board1 (Arduino)
        assert "board0" in result.stdout
        assert "board1" in result.stdout


# ---------------------------------------------------------------------------
# Discover
# ---------------------------------------------------------------------------

class TestDiscoverCommand:
    def test_discover_exits_ok(self) -> None:
        result = runner.invoke(app, ["discover"])
        assert result.exit_code == 0

    def test_discover_shows_boards(self) -> None:
        result = runner.invoke(app, ["discover"])
        assert "board0" in result.stdout or "Discovery" in result.stdout


# ---------------------------------------------------------------------------
# Board sub-commands
# ---------------------------------------------------------------------------

class TestBoardSubcommands:
    def test_info_known_board(self) -> None:
        result = runner.invoke(app, ["board", "info", "board0"])
        assert result.exit_code == 0
        assert "TRT_CORE" in result.stdout

    def test_info_unknown_board(self) -> None:
        result = runner.invoke(app, ["board", "info", "nonexistent"])
        assert result.exit_code != 0

    def test_status(self) -> None:
        result = runner.invoke(app, ["board", "status", "board0"])
        assert result.exit_code == 0

    def test_reset(self) -> None:
        result = runner.invoke(app, ["board", "reset", "board0"])
        assert result.exit_code == 0

    def test_reboot(self) -> None:
        result = runner.invoke(app, ["board", "reboot", "board0"])
        assert result.exit_code == 0

    def test_capabilities(self) -> None:
        result = runner.invoke(app, ["board", "capabilities", "board0"])
        assert result.exit_code == 0
        assert "gpio" in result.stdout

    def test_modules(self) -> None:
        result = runner.invoke(app, ["board", "modules", "board0"])
        assert result.exit_code == 0

    # GPIO
    def test_gpio_list(self) -> None:
        result = runner.invoke(app, ["board", "gpio", "list", "board0"])
        assert result.exit_code == 0

    def test_gpio_read(self) -> None:
        result = runner.invoke(app, ["board", "gpio", "read", "board0", "PA5"])
        assert result.exit_code == 0

    def test_gpio_write(self) -> None:
        result = runner.invoke(app, ["board", "gpio", "write", "board0", "PA5", "1"])
        assert result.exit_code == 0

    # PWM
    def test_pwm_list(self) -> None:
        result = runner.invoke(app, ["board", "pwm", "list", "board0"])
        assert result.exit_code == 0

    def test_pwm_start(self) -> None:
        result = runner.invoke(app, ["board", "pwm", "start", "board0", "1"])
        assert result.exit_code == 0

    def test_pwm_stop(self) -> None:
        result = runner.invoke(app, ["board", "pwm", "stop", "board0", "1"])
        assert result.exit_code == 0

    def test_pwm_set(self) -> None:
        result = runner.invoke(app, ["board", "pwm", "set", "board0", "1", "1000", "50"])
        assert result.exit_code == 0

    # ADC
    def test_adc_list(self) -> None:
        result = runner.invoke(app, ["board", "adc", "list", "board0"])
        assert result.exit_code == 0

    def test_adc_read(self) -> None:
        result = runner.invoke(app, ["board", "adc", "read", "board0", "3"])
        assert result.exit_code == 0

    # DAC
    def test_dac_list(self) -> None:
        result = runner.invoke(app, ["board", "dac", "list", "board0"])
        assert result.exit_code == 0

    def test_dac_read(self) -> None:
        result = runner.invoke(app, ["board", "dac", "read", "board0", "1"])
        assert result.exit_code == 0

    def test_dac_set(self) -> None:
        result = runner.invoke(app, ["board", "dac", "set", "board0", "1", "2048"])
        assert result.exit_code == 0

    # I2C
    def test_i2c_scan(self) -> None:
        result = runner.invoke(app, ["board", "i2c", "scan", "board0"])
        assert result.exit_code == 0

    def test_i2c_read(self) -> None:
        result = runner.invoke(app, ["board", "i2c", "read", "board0"])
        assert result.exit_code == 0

    def test_i2c_write(self) -> None:
        result = runner.invoke(app, ["board", "i2c", "write", "board0"])
        assert result.exit_code == 0

    # SPI
    def test_spi_transfer(self) -> None:
        result = runner.invoke(app, ["board", "spi", "transfer", "board0"])
        assert result.exit_code == 0

    def test_spi_config(self) -> None:
        result = runner.invoke(app, ["board", "spi", "config", "board0"])
        assert result.exit_code == 0

    # Debug
    def test_debug_logs(self) -> None:
        result = runner.invoke(app, ["board", "debug", "logs", "board0"])
        assert result.exit_code == 0

    def test_debug_monitor(self) -> None:
        result = runner.invoke(app, ["board", "debug", "monitor", "board0"])
        assert result.exit_code == 0

    def test_debug_shell(self) -> None:
        result = runner.invoke(app, ["board", "debug", "shell", "board0"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# LCD
# ---------------------------------------------------------------------------

class TestLcdCommands:
    def test_lcd_info(self) -> None:
        result = runner.invoke(app, ["lcd", "info"])
        assert result.exit_code == 0

    def test_lcd_reset(self) -> None:
        result = runner.invoke(app, ["lcd", "reset"])
        assert result.exit_code == 0

    def test_lcd_clear(self) -> None:
        result = runner.invoke(app, ["lcd", "clear"])
        assert result.exit_code == 0

    def test_lcd_write(self) -> None:
        result = runner.invoke(app, ["lcd", "write", "Hello TRT"])
        assert result.exit_code == 0
        assert "Hello TRT" in result.stdout


# ---------------------------------------------------------------------------
# LED
# ---------------------------------------------------------------------------

class TestLedCommands:
    def test_led_on(self) -> None:
        assert runner.invoke(app, ["led", "on"]).exit_code == 0

    def test_led_off(self) -> None:
        assert runner.invoke(app, ["led", "off"]).exit_code == 0

    def test_led_blink(self) -> None:
        assert runner.invoke(app, ["led", "blink"]).exit_code == 0

    def test_led_brightness(self) -> None:
        result = runner.invoke(app, ["led", "brightness", "50"])
        assert result.exit_code == 0

    def test_led_color(self) -> None:
        result = runner.invoke(app, ["led", "color", "255", "0", "0"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class TestProtocolCommands:
    def test_protocol_info(self) -> None:
        result = runner.invoke(app, ["protocol", "info"])
        assert result.exit_code == 0
        assert "TRT Protocol" in result.stdout

    def test_protocol_version(self) -> None:
        result = runner.invoke(app, ["protocol", "version"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class TestBoardModels:
    def test_board_identity(self) -> None:
        ident = BoardIdentity(board_id="test0", board_type=BoardType.TRT_CORE)
        assert ident.board_id == "test0"
        assert ident.board_type == BoardType.TRT_CORE
        assert "test0" in str(ident)

    def test_transport_config(self) -> None:
        cfg = TransportConfig(transport_type=TransportType.USB, port="COM3")
        assert "COM3" in str(cfg)

    def test_capabilities_has(self) -> None:
        caps = BoardCapabilities(gpio=True, pwm=False)
        assert caps.has("gpio") is True
        assert caps.has("pwm") is False
        assert caps.has("nonexistent") is False

    def test_capabilities_as_dict(self) -> None:
        caps = BoardCapabilities(gpio=True)
        d = caps.as_dict()
        assert d["gpio"] is True
        assert "pwm" in d

    def test_board_is_ready(self) -> None:
        ident = BoardIdentity(board_id="b0", board_type=BoardType.TRT_CORE)
        board = Board(identity=ident, status=BoardStatus.READY)
        assert board.is_ready() is True
        assert board.is_connected() is True

    def test_board_disconnected(self) -> None:
        ident = BoardIdentity(board_id="b0", board_type=BoardType.TRT_CORE)
        board = Board(identity=ident, status=BoardStatus.DISCONNECTED)
        assert board.is_ready() is False
        assert board.is_connected() is False


class TestBoardRegistry:
    def test_register_and_get(self) -> None:
        reg = BoardRegistry()
        ident = BoardIdentity(board_id="x0", board_type=BoardType.TRT_CORE)
        board = Board(identity=ident, status=BoardStatus.READY)
        reg.register(board)
        assert reg.get("x0") is board
        assert len(reg) == 1

    def test_connected_filter(self) -> None:
        reg = BoardRegistry()
        for bid, status in [("a", BoardStatus.READY), ("b", BoardStatus.DISCONNECTED)]:
            ident = BoardIdentity(board_id=bid, board_type=BoardType.TRT_CORE)
            reg.register(Board(identity=ident, status=status))
        assert len(reg.connected()) == 1

    def test_remove(self) -> None:
        reg = BoardRegistry()
        ident = BoardIdentity(board_id="z0", board_type=BoardType.TRT_CORE)
        reg.register(Board(identity=ident))
        assert reg.remove("z0") is True
        assert reg.get("z0") is None
        assert reg.remove("z0") is False

    def test_clear(self) -> None:
        reg = make_mock_registry()
        assert len(reg) == 2
        reg.clear()
        assert len(reg) == 0

    def test_mock_registry(self) -> None:
        reg = make_mock_registry()
        assert len(reg) == 2
        board0 = reg.get("board0")
        assert board0 is not None
        assert board0.capabilities.gpio is True
        assert board0.capabilities.has("pwm") is True


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_all_top_level_commands_exit_ok(self) -> None:
        for cmd in ["help", "version", "boards", "discover"]:
            result = runner.invoke(app, [cmd])
            assert result.exit_code == 0, f"Command '{cmd}' exited {result.exit_code}: {result.stdout}"

    def test_invalid_command_fails(self) -> None:
        result = runner.invoke(app, ["thisdoesnotexist"])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

