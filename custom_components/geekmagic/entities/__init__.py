"""Entity platforms for GeekMagic integration.

This module contains all Home Assistant entity platforms for device configuration:
- button: Action buttons (refresh, next/prev screen)
- entity: Base entity class
- number: Numeric settings (brightness, intervals, screen count)
- select: Dropdown selectors (screens, layouts, widgets, templates)
- sensor: Diagnostic sensors (status, last update)
- switch: Boolean widget options
- text: Text inputs (screen names, labels)
"""

from .button import async_setup_entry as async_setup_button
from .entity import GeekMagicEntity
from .number import async_setup_entry as async_setup_number
from .select import async_setup_entry as async_setup_select
from .sensor import async_setup_entry as async_setup_sensor
from .switch import async_setup_entry as async_setup_switch
from .text import async_setup_entry as async_setup_text

__all__ = [
    "GeekMagicEntity",
    "async_setup_button",
    "async_setup_number",
    "async_setup_select",
    "async_setup_sensor",
    "async_setup_switch",
    "async_setup_text",
]
