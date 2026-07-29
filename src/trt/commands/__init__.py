"""Commands package for TRT CLI.

Each module implements one top-level command or command group:

    help        — rich overview of the full command tree
    version     — version information
    boards      — list all known boards
    discover    — rescan for connected boards
    board       — per-board sub-commands (gpio, pwm, adc, dac, i2c, spi, debug)
    lcd         — LCD display control (HD44780-style over I2C)
    led         — LED control (WS2812 / NeoPixel)
    protocol    — TRT Protocol information placeholders

To add a new top-level command:
    1. Create a new module here.
    2. Register it in trt/cli.py.
"""

