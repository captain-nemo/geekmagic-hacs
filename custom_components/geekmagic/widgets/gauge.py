"""Gauge widget for GeekMagic displays."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from ..const import COLOR_CYAN, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE
from .base import Widget, WidgetConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from PIL import ImageDraw

    from ..renderer import Renderer


class GaugeWidget(Widget):
    """Widget that displays a value as a gauge (bar or ring)."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the gauge widget."""
        super().__init__(config)
        self.style = config.options.get("style", "bar")  # bar, ring, arc
        self.min_value = config.options.get("min", 0)
        self.max_value = config.options.get("max", 100)
        self.icon = config.options.get("icon")
        self.show_value = config.options.get("show_value", True)
        self.unit = config.options.get("unit", "")

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the gauge widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        padding = 8

        # Get entity state
        state = self.get_entity_state(hass)
        value = 0.0
        display_value = "--"

        if state is not None:
            with contextlib.suppress(ValueError, TypeError):
                value = float(state.state)
                display_value = f"{value:.0f}"
            if not self.unit:
                self.unit = state.attributes.get("unit_of_measurement", "")

        # Calculate percentage
        value_range = self.max_value - self.min_value
        if value_range > 0:
            percent = max(0, min(100, ((value - self.min_value) / value_range) * 100))
        else:
            percent = 0

        # Get label
        name = self.config.label
        if not name and state:
            name = state.attributes.get("friendly_name", "")
        name = name or ""

        color = self.config.color or COLOR_CYAN

        if self.style == "ring":
            self._render_ring(renderer, draw, rect, percent, display_value, name, color)
        elif self.style == "arc":
            self._render_arc(renderer, draw, rect, percent, display_value, name, color)
        else:
            self._render_bar(renderer, draw, rect, percent, display_value, name, color, padding)

    def _render_bar(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        percent: float,
        value: str,
        name: str,
        color: tuple[int, int, int],
        padding: int,
    ) -> None:
        """Render as horizontal progress bar."""
        x1, y1, x2, y2 = rect
        height = y2 - y1

        # Calculate layout
        icon_size = 14
        label_y = y1 + height // 3
        bar_height = 10
        bar_y = y1 + (height * 2) // 3 - bar_height // 2

        # Draw icon if present
        text_start_x = x1 + padding
        if self.icon is not None:
            renderer.draw_icon(
                draw,
                self.icon,
                (x1 + padding, label_y - icon_size // 2),
                size=icon_size,
                color=color,
            )
            text_start_x = x1 + padding + icon_size + 4

        # Draw label
        if name:
            renderer.draw_text(
                draw,
                name.upper(),
                (text_start_x, label_y),
                font=renderer.font_tiny,
                color=COLOR_GRAY,
                anchor="lm",
            )

        # Draw value
        if self.show_value:
            value_text = f"{value}{self.unit}" if self.unit else value
            renderer.draw_text(
                draw,
                value_text,
                (x2 - padding, label_y),
                font=renderer.font_medium_bold,
                color=COLOR_WHITE,
                anchor="rm",
            )

        # Draw bar
        bar_rect = (x1 + padding, bar_y, x2 - padding, bar_y + bar_height)
        renderer.draw_bar(draw, bar_rect, percent, color, COLOR_DARK_GRAY)

    def _render_ring(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        percent: float,
        value: str,
        name: str,
        color: tuple[int, int, int],
    ) -> None:
        """Render as ring gauge."""
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        center_x = x1 + width // 2
        center_y = y1 + height // 2

        # Calculate ring size
        radius = min(width, height) // 2 - 15
        ring_width = max(5, radius // 5)

        # Draw ring
        renderer.draw_ring_gauge(
            draw,
            center=(center_x, center_y - 5),
            radius=radius,
            percent=percent,
            color=color,
            background=COLOR_DARK_GRAY,
            width=ring_width,
        )

        # Draw value in center
        if self.show_value:
            value_text = f"{value}{self.unit}" if self.unit else value
            renderer.draw_text(
                draw,
                value_text,
                (center_x, center_y - 5),
                font=renderer.font_large,
                color=COLOR_WHITE,
                anchor="mm",
            )

        # Draw label below
        if name:
            renderer.draw_text(
                draw,
                name.upper(),
                (center_x, y2 - 10),
                font=renderer.font_tiny,
                color=COLOR_GRAY,
                anchor="mm",
            )

    def _render_arc(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        percent: float,
        value: str,
        name: str,
        color: tuple[int, int, int],
    ) -> None:
        """Render as arc gauge (semicircle)."""
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        center_x = x1 + width // 2
        center_y = y1 + height // 2 + 10

        # Calculate arc size
        radius = min(width, height) // 2 - 10

        # Draw arc using renderer's draw_arc method
        renderer.draw_arc(
            draw,
            rect=(center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            percent=percent,
            color=color,
            background=COLOR_DARK_GRAY,
        )

        # Draw value
        if self.show_value:
            value_text = f"{value}{self.unit}" if self.unit else value
            renderer.draw_text(
                draw,
                value_text,
                (center_x, center_y - 5),
                font=renderer.font_large,
                color=COLOR_WHITE,
                anchor="mm",
            )

        # Draw label
        if name:
            renderer.draw_text(
                draw,
                name.upper(),
                (center_x, y1 + 12),
                font=renderer.font_small,
                color=COLOR_GRAY,
                anchor="mm",
            )
