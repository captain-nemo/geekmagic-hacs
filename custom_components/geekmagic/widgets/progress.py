"""Progress widget for GeekMagic displays."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from ..const import COLOR_CYAN, COLOR_DARK_GRAY, COLOR_GRAY, COLOR_WHITE
from .base import Widget, WidgetConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from PIL import ImageDraw

    from ..renderer import Renderer


class ProgressWidget(Widget):
    """Widget that displays progress with label (like fitness tracking)."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the progress widget."""
        super().__init__(config)
        self.target = config.options.get("target", 100)
        self.unit = config.options.get("unit", "")
        self.show_target = config.options.get("show_target", True)
        self.icon = config.options.get("icon")

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the progress widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        height = y2 - y1
        padding = 8

        # Get entity state
        state = self.get_entity_state(hass)
        current_value = 0.0
        display_value = "0"

        if state is not None:
            with contextlib.suppress(ValueError, TypeError):
                current_value = float(state.state)
                display_value = f"{current_value:.0f}"
            if not self.unit:
                self.unit = state.attributes.get("unit_of_measurement", "")

        # Calculate percentage
        target = self.target or 100
        percent = min(100, (current_value / target) * 100) if target > 0 else 0

        # Get label
        name = self.config.label
        if not name and state:
            name = state.attributes.get("friendly_name", "")
        name = name or "Progress"

        color = self.config.color or COLOR_CYAN

        # Layout: icon/label on left, value/target on right, bar below
        row_height = height // 2
        bar_height = 10

        # Top row: label and value
        top_y = y1 + row_height // 2

        # Icon if present
        text_x = x1 + padding
        if self.icon:
            renderer.draw_icon(draw, self.icon, (x1 + padding, top_y - 7), size=14, color=color)
            text_x = x1 + padding + 18

        # Label
        renderer.draw_text(
            draw,
            name.upper(),
            (text_x, top_y),
            font=renderer.font_small,
            color=COLOR_GRAY,
            anchor="lm",
        )

        # Value / target
        value_text = f"{display_value}/{target:.0f}" if self.show_target else display_value
        if self.unit:
            value_text += f" {self.unit}"

        renderer.draw_text(
            draw,
            value_text,
            (x2 - padding, top_y),
            font=renderer.font_regular,
            color=COLOR_WHITE,
            anchor="rm",
        )

        # Bottom row: progress bar and percentage
        bar_y = y1 + row_height + (row_height - bar_height) // 2 - 5
        bar_rect = (x1 + padding, bar_y, x2 - 50, bar_y + bar_height)
        renderer.draw_bar(draw, bar_rect, percent, color, COLOR_DARK_GRAY)

        # Percentage
        renderer.draw_text(
            draw,
            f"{percent:.0f}%",
            (x2 - padding, bar_y + bar_height // 2),
            font=renderer.font_small,
            color=COLOR_WHITE,
            anchor="rm",
        )


class MultiProgressWidget(Widget):
    """Widget that displays multiple progress items in a list."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the multi-progress widget."""
        super().__init__(config)
        # List of progress configs: [(entity_id, label, target, color, icon), ...]
        self.items = config.options.get("items", [])
        self.title = config.options.get("title")

    def get_entities(self) -> list[str]:
        """Return list of entity IDs this widget depends on."""
        return [item.get("entity_id") for item in self.items if item.get("entity_id")]

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the multi-progress widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        padding = 8
        current_y = y1 + padding

        # Draw title if present
        if self.title:
            renderer.draw_text(
                draw,
                self.title.upper(),
                (x1 + padding, current_y),
                font=renderer.font_small,
                color=COLOR_GRAY,
                anchor="lm",
            )
            current_y += 20

        # Calculate row height
        available_height = y2 - current_y - padding
        row_count = len(self.items) or 1
        row_height = min(50, available_height // row_count)
        bar_height = 8

        # Draw each progress item
        for item in self.items:
            entity_id = item.get("entity_id")
            label = item.get("label", "")
            target = item.get("target", 100)
            color = item.get("color", COLOR_CYAN)
            icon = item.get("icon")
            unit = item.get("unit", "")

            # Get state
            current_value = 0.0
            if hass and entity_id:
                state = hass.states.get(entity_id)
                if state is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        current_value = float(state.state)
                    if not label:
                        label = state.attributes.get("friendly_name", entity_id)
                    if not unit:
                        unit = state.attributes.get("unit_of_measurement", "")

            label = label or entity_id or "Item"
            percent = min(100, (current_value / target) * 100) if target > 0 else 0

            # Draw icon if present
            label_x = x1 + padding
            if icon:
                renderer.draw_icon(draw, icon, (x1 + padding, current_y + 2), size=12, color=color)
                label_x = x1 + padding + 16

            # Draw label
            renderer.draw_text(
                draw,
                label.upper(),
                (label_x, current_y + 6),
                font=renderer.font_tiny,
                color=COLOR_GRAY,
                anchor="lm",
            )

            # Draw value/target
            value_text = f"{current_value:.0f}/{target:.0f}"
            if unit:
                value_text += f" {unit}"
            renderer.draw_text(
                draw,
                value_text,
                (x2 - padding, current_y + 6),
                font=renderer.font_tiny,
                color=COLOR_WHITE,
                anchor="rm",
            )

            # Draw progress bar
            bar_y = current_y + 18
            bar_rect = (x1 + padding, bar_y, x2 - 45, bar_y + bar_height)
            renderer.draw_bar(draw, bar_rect, percent, color, COLOR_DARK_GRAY)

            # Draw percentage
            renderer.draw_text(
                draw,
                f"{percent:.0f}%",
                (x2 - padding, bar_y + bar_height // 2),
                font=renderer.font_tiny,
                color=COLOR_WHITE,
                anchor="rm",
            )

            current_y += row_height
