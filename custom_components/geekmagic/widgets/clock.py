"""Clock widget for GeekMagic displays."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from ..const import COLOR_GRAY, COLOR_WHITE
from .base import Widget, WidgetConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ..render_context import RenderContext

_LOGGER = logging.getLogger(__name__)


class ClockWidget(Widget):
    """Widget that displays current time and date."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the clock widget."""
        super().__init__(config)
        self.show_date = config.options.get("show_date", True)
        self.show_seconds = config.options.get("show_seconds", False)
        self.time_format = config.options.get("time_format", "24h")
        self.timezone = config.options.get("timezone")

    def get_entities(self) -> list[str]:
        """Clock widget doesn't depend on entities."""
        return []

    def render(
        self,
        ctx: RenderContext,
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the clock widget.

        Args:
            ctx: RenderContext for drawing
            hass: Home Assistant instance (used for timezone)
        """
        center_x = ctx.width // 2
        center_y = ctx.height // 2

        # Get timezone: custom timezone option > HA config > UTC
        tz = None
        if self.timezone:
            try:
                tz = ZoneInfo(self.timezone)
            except Exception:
                _LOGGER.warning("Invalid timezone: %s, using HA timezone", self.timezone)
                tz = None

        if tz is None and hass is not None:
            tz = getattr(hass.config, "time_zone_obj", None) or UTC

        now = datetime.now(tz=tz or UTC)

        # Format time
        if self.show_seconds:
            if self.time_format == "12h":
                time_str = now.strftime("%I:%M:%S")
                ampm = now.strftime("%p")
            else:
                time_str = now.strftime("%H:%M:%S")
                ampm = None
        elif self.time_format == "12h":
            time_str = now.strftime("%I:%M")
            ampm = now.strftime("%p")
        else:
            time_str = now.strftime("%H:%M")
            ampm = None

        # Calculate available space for time
        # Reserve space for date, label, and AM/PM indicator
        time_area_height = ctx.height
        if self.show_date:
            time_area_height = int(ctx.height * 0.65)  # 65% for time when showing date
        if self.config.label:
            time_area_height = int(time_area_height * 0.85)  # Reduce for label

        # Use fit_text for maximum time visibility
        # Time should fill available width/height for best readability
        font_time = ctx.fit_text(
            time_str,
            max_width=int(ctx.width * 0.95),
            max_height=int(time_area_height * 0.60),
            bold=False,
        )

        # Use semantic sizes for secondary elements
        font_date = ctx.get_font("secondary")
        font_small = ctx.get_font("tertiary")

        # Calculate positions relative to container
        offset_y = int(ctx.height * 0.08) if self.show_date else 0
        time_y = center_y - offset_y

        # Draw time
        color = self.config.color or COLOR_WHITE
        ctx.draw_text(
            time_str,
            (center_x, time_y),
            font=font_time,
            color=color,
            anchor="mm",
        )

        # Draw AM/PM if 12-hour format
        if ampm:
            ampm_x = center_x + ctx.get_text_size(time_str, font_time)[0] // 2 + 5
            ctx.draw_text(
                ampm,
                (ampm_x, time_y - int(ctx.height * 0.08)),
                font=font_small,
                color=COLOR_GRAY,
                anchor="lm",
            )

        # Draw date
        if self.show_date:
            date_str = now.strftime("%a, %b %d")
            date_y = center_y + int(ctx.height * 0.20)
            ctx.draw_text(
                date_str,
                (center_x, date_y),
                font=font_date,
                color=COLOR_GRAY,
                anchor="mm",
            )

        # Draw label if provided
        if self.config.label:
            label_y = int(ctx.height * 0.12)
            ctx.draw_text(
                self.config.label.upper(),
                (center_x, label_y),
                font=font_small,
                color=COLOR_GRAY,
                anchor="mm",
            )
