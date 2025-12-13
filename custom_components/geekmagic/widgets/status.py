"""Status widget for GeekMagic displays."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..const import COLOR_GRAY, COLOR_LIME, COLOR_RED, COLOR_WHITE
from .base import Widget, WidgetConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from PIL import ImageDraw

    from ..renderer import Renderer


class StatusWidget(Widget):
    """Widget that displays a binary sensor status with colored indicator."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the status widget."""
        super().__init__(config)
        self.on_color = config.options.get("on_color", COLOR_LIME)
        self.off_color = config.options.get("off_color", COLOR_RED)
        self.on_text = config.options.get("on_text", "ON")
        self.off_text = config.options.get("off_text", "OFF")
        self.icon = config.options.get("icon")
        self.show_status_text = config.options.get("show_status_text", True)

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the status widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        center_y = y1 + height // 2
        padding = 8

        # Get entity state
        state = self.get_entity_state(hass)

        # Determine if on or off
        is_on = False
        if state is not None:
            is_on = state.state.lower() in ("on", "true", "home", "open", "unlocked", "1")

        # Get color and text
        color = self.on_color if is_on else self.off_color
        status_text = self.on_text if is_on else self.off_text

        # Get label
        name = self.config.label
        if not name and state:
            name = state.attributes.get("friendly_name", state.entity_id)
        name = name or "Unknown"

        # Truncate name if too long
        max_name_len = (width - 40) // 7
        if len(name) > max_name_len:
            name = name[: max_name_len - 2] + ".."

        # Draw status indicator (dot)
        dot_radius = 5
        dot_x = x1 + padding + dot_radius
        dot_y = center_y

        renderer.draw_ellipse(
            draw,
            rect=(dot_x - dot_radius, dot_y - dot_radius, dot_x + dot_radius, dot_y + dot_radius),
            fill=color,
        )

        # Draw icon if present
        text_x = dot_x + dot_radius + 8
        if self.icon:
            renderer.draw_icon(draw, self.icon, (text_x, center_y - 7), size=14, color=COLOR_GRAY)
            text_x += 18

        # Draw name
        renderer.draw_text(
            draw,
            name,
            (text_x, center_y),
            font=renderer.font_small,
            color=COLOR_WHITE,
            anchor="lm",
        )

        # Draw status text
        if self.show_status_text:
            renderer.draw_text(
                draw,
                status_text,
                (x2 - padding, center_y),
                font=renderer.font_small,
                color=color,
                anchor="rm",
            )


class StatusListWidget(Widget):
    """Widget that displays a list of binary sensors with status indicators."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the status list widget."""
        super().__init__(config)
        # List of (entity_id, label) tuples
        self.entities = config.options.get("entities", [])
        self.on_color = config.options.get("on_color", COLOR_LIME)
        self.off_color = config.options.get("off_color", COLOR_RED)
        self.on_text = config.options.get("on_text")
        self.off_text = config.options.get("off_text")
        self.title = config.options.get("title")

    def get_entities(self) -> list[str]:
        """Return list of entity IDs this widget depends on."""
        return [e[0] if isinstance(e, list | tuple) else e for e in self.entities]

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the status list widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        width = x2 - x1
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
            current_y += 18

        # Calculate row height
        available_height = y2 - current_y - padding
        row_count = len(self.entities) or 1
        row_height = min(20, available_height // row_count)

        # Draw each entity
        for entry in self.entities:
            if isinstance(entry, list | tuple):
                entity_id, label = entry[0], entry[1]
            else:
                entity_id = entry
                label = None

            # Get state
            state = hass.states.get(entity_id) if hass else None

            is_on = False
            if state is not None:
                is_on = state.state.lower() in ("on", "true", "home", "open", "unlocked", "1")
                if not label:
                    label = state.attributes.get("friendly_name", entity_id)
            label = label or entity_id

            # Get color
            color = self.on_color if is_on else self.off_color

            # Truncate label
            max_len = (width - 60) // 7
            if len(label) > max_len:
                label = label[: max_len - 2] + ".."

            # Draw dot
            dot_y = current_y + row_height // 2
            renderer.draw_ellipse(
                draw,
                rect=(x1 + padding, dot_y - 3, x1 + padding + 6, dot_y + 3),
                fill=color,
            )

            # Draw label
            renderer.draw_text(
                draw,
                label,
                (x1 + padding + 12, dot_y),
                font=renderer.font_tiny,
                color=COLOR_WHITE,
                anchor="lm",
            )

            # Draw status text
            if self.on_text or self.off_text:
                status_text = self.on_text if is_on else self.off_text
                if status_text:
                    renderer.draw_text(
                        draw,
                        status_text,
                        (x2 - padding, dot_y),
                        font=renderer.font_tiny,
                        color=color,
                        anchor="rm",
                    )

            current_y += row_height
