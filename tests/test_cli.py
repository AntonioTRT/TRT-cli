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
)
from trt.protocol.models import GpioReadRequest, GpioReadResponse, ProtocolOperation
from trt.protocol.protocol_client import MockProtocolClient
from trt.repositories.board_repository import BoardRepository
from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.board_service import BoardService
from trt.services.capability_service import CapabilityService
from trt.transport.mock_transport import MockTransport
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


def make_test_repository() -> BoardRepository:
    registry = BoardRegistry()
    registry.register(
        Board(
            identity=BoardIdentity(board_id="board0", board_type=BoardType.TRT_CORE),
            status=BoardStatus.READY,
            transport=TransportConfig(transport_type=TransportType.USB, port="TEST"),
            capabilities=BoardCapabilities(
                gpio=True,
                pwm=True,
                adc=True,
                dac=True,
                i2c=True,
                spi=True,
                uart=True,
                debug_shell=True,
            ),
        )
    )
    return BoardRepository(registry)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class TestVersion:
    def test_get_version(self) -> None:
        assert get_version() == "1.0.0"

    def test_get_version_info(self) -> None:
        assert get_version_info() == (1, 0, 0)

    def test_version_command(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.stdout
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

    def test_boards_shows_discovered_real_board(self) -> None:
        result = runner.invoke(app, ["boards"])
        assert "101" in result.stdout
        assert "COM4" in result.stdout


# ---------------------------------------------------------------------------
# Discover
# ---------------------------------------------------------------------------

class TestDiscoverCommand:
    def test_discover_exits_ok(self) -> None:
        result = runner.invoke(app, ["discover"])
        assert result.exit_code == 0

    def test_discover_shows_boards(self) -> None:
        result = runner.invoke(app, ["discover"])
        assert "101" in result.stdout or "Discovery" in result.stdout


# ---------------------------------------------------------------------------
# Board sub-commands
# ---------------------------------------------------------------------------

class TestBoardSubcommands:
    def test_info_known_board(self) -> None:
        result = runner.invoke(app, ["board", "info", "101"])
        assert result.exit_code == 0
        assert "BUILD_ID" in result.stdout

    def test_info_unknown_board(self) -> None:
        result = runner.invoke(app, ["board", "info", "nonexistent"])
        assert result.exit_code != 0

    def test_status(self) -> None:
        result = runner.invoke(app, ["board", "status", "101"])
        assert result.exit_code == 0

    def test_capabilities(self) -> None:
        result = runner.invoke(app, ["board", "capabilities", "101"])
        assert result.exit_code == 0
        assert "gpio" in result.stdout

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
        reg = BoardRegistry()
        reg.register(Board(identity=BoardIdentity(board_id="board0", board_type=BoardType.TRT_CORE)))
        assert len(reg) == 1
        reg.clear()
        assert len(reg) == 0

    def test_discovery_service_populates_registry_from_transport(self) -> None:
        service = BoardDiscoveryService()
        boards = service.discover()
        assert len(boards) >= 1
        board = service.repository.get_by_id("101")
        assert board is not None
        assert board.identity.firmware == "0.1.0"
        assert board.metadata["build_id"] == "000004"


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


class TestArchitectureServices:
    def test_service_can_resolve_board_and_capability(self) -> None:
        service = BoardService(repository=make_test_repository(), protocol_client=MockProtocolClient())
        board = service.get_board("board0")
        assert board is not None
        assert board.identity.board_id == "board0"

        capability_service = CapabilityService()
        assert capability_service.supports(board, "gpio") is True
        assert capability_service.supports(board, "missing_cap") is False

    def test_protocol_client_returns_mock_response(self) -> None:
        service = BoardService(repository=make_test_repository(), protocol_client=MockProtocolClient())
        result = service.read_gpio("board0", "PA5")
        assert result.status == "ok"
        assert isinstance(result.payload, dict)
        assert result.payload["pin"] == "PA5"

    def test_protocol_operation_is_typed(self) -> None:
        request = GpioReadRequest(board_id="board0", pin="PA5")
        assert request.operation is ProtocolOperation.GPIO_READ
        assert request.capability == "gpio"

    def test_mock_transport_returns_typed_response(self) -> None:
        response = MockTransport().send(GpioReadRequest(board_id="board0", pin="PA5"))
        assert isinstance(response, GpioReadResponse)
        assert response.operation is ProtocolOperation.GPIO_READ
        assert response.pin == "PA5"


class TestMockBoardOperations:
    def service(self) -> BoardService:
        return BoardService(repository=make_test_repository(), protocol_client=MockProtocolClient())

    def test_mock_gpio_read(self) -> None:
        result = self.service().read_gpio("board0", "PA5")
        assert result.status == "ok"

    def test_mock_pwm_set(self) -> None:
        result = self.service().set_pwm("board0", 1, 1000, 50)
        assert result.status == "ok"

    def test_mock_adc_read(self) -> None:
        result = self.service().read_adc("board0", 3)
        assert result.status == "ok"

    def test_mock_dac_set(self) -> None:
        result = self.service().set_dac("board0", 1, 2048)
        assert result.status == "ok"

    def test_mock_i2c_scan(self) -> None:
        result = self.service().scan_i2c("board0")
        assert result.status == "ok"

    def test_mock_spi_transfer(self) -> None:
        result = self.service().transfer_spi("board0", "0x00")
        assert result.status == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

