"""Weather widget for GeekMagic displays."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..const import (
    COLOR_CYAN,
    COLOR_GOLD,
    COLOR_GRAY,
    COLOR_WHITE,
)
from .base import Widget, WidgetConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from PIL import ImageDraw

    from ..renderer import Renderer


# Map weather conditions to icons
WEATHER_ICONS = {
    "sunny": "sun",
    "clear-night": "moon",
    "partlycloudy": "cloud",
    "cloudy": "cloud",
    "rainy": "rain",
    "pouring": "rain",
    "snowy": "cloud",
    "fog": "cloud",
    "windy": "wind",
    "lightning": "bolt",
    "lightning-rainy": "bolt",
}


class WeatherWidget(Widget):
    """Widget that displays weather information."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the weather widget."""
        super().__init__(config)
        self.show_forecast = config.options.get("show_forecast", True)
        self.forecast_days = config.options.get("forecast_days", 3)
        self.show_humidity = config.options.get("show_humidity", True)
        self.show_wind = config.options.get("show_wind", False)

    def render(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        hass: HomeAssistant | None = None,
    ) -> None:
        """Render the weather widget.

        Args:
            renderer: Renderer instance
            draw: ImageDraw instance
            rect: (x1, y1, x2, y2) bounding box
            hass: Home Assistant instance
        """
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        center_x = x1 + width // 2
        padding = 10

        # Get entity state
        state = self.get_entity_state(hass)

        if state is None:
            # Show placeholder
            renderer.draw_text(
                draw,
                "No Weather Data",
                (center_x, y1 + height // 2),
                font=renderer.font_regular,
                color=COLOR_GRAY,
                anchor="mm",
            )
            return

        attrs = state.attributes
        condition = state.state
        temperature = attrs.get("temperature", "--")
        humidity = attrs.get("humidity", "--")
        forecast = attrs.get("forecast", [])

        # Get weather icon
        icon_name = WEATHER_ICONS.get(condition, "sun")

        # Layout depends on available space
        if height > 150 and self.show_forecast:
            self._render_full(
                renderer, draw, rect, icon_name, temperature, humidity, condition, forecast, padding
            )
        else:
            self._render_compact(
                renderer, draw, rect, icon_name, temperature, humidity, condition, padding
            )

    def _render_full(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        icon_name: str,
        temperature: Any,
        humidity: Any,
        condition: str,
        forecast: list[dict],
        padding: int,
    ) -> None:
        """Render full weather with forecast."""
        x1, y1, x2, y2 = rect
        width = x2 - x1
        center_x = x1 + width // 2

        # Current weather section
        current_y = y1 + padding

        # Weather icon (large)
        icon_size = 48
        renderer.draw_icon(
            draw,
            icon_name,
            (center_x - icon_size // 2, current_y),
            size=icon_size,
            color=COLOR_GOLD,
        )

        # Temperature
        temp_str = f"{temperature}°" if temperature != "--" else "--"
        renderer.draw_text(
            draw,
            temp_str,
            (center_x, current_y + icon_size + 15),
            font=renderer.font_xlarge,
            color=COLOR_WHITE,
            anchor="mm",
        )

        # Condition text
        renderer.draw_text(
            draw,
            condition.replace("-", " ").title(),
            (center_x, current_y + icon_size + 40),
            font=renderer.font_small,
            color=COLOR_GRAY,
            anchor="mm",
        )

        # Humidity
        if self.show_humidity:
            renderer.draw_icon(
                draw, "drop", (x1 + padding, current_y + icon_size + 55), size=12, color=COLOR_CYAN
            )
            renderer.draw_text(
                draw,
                f"{humidity}%",
                (x1 + padding + 16, current_y + icon_size + 61),
                font=renderer.font_tiny,
                color=COLOR_CYAN,
                anchor="lm",
            )

        # Forecast section
        if forecast and self.show_forecast:
            forecast_y = y2 - 45
            forecast_items = forecast[: self.forecast_days]
            if forecast_items:
                item_width = (width - padding * 2) // len(forecast_items)

                for i, day in enumerate(forecast_items):
                    fx = x1 + padding + i * item_width + item_width // 2
                    day_condition = day.get("condition", "sunny")
                    day_temp = day.get("temperature", "--")
                    day_name = day.get("datetime", "")[:3] if day.get("datetime") else f"D{i + 1}"

                    # Day name
                    renderer.draw_text(
                        draw,
                        day_name.upper(),
                        (fx, forecast_y),
                        font=renderer.font_tiny,
                        color=COLOR_GRAY,
                        anchor="mm",
                    )

                    # Small icon
                    day_icon = WEATHER_ICONS.get(day_condition, "sun")
                    renderer.draw_icon(
                        draw, day_icon, (fx - 8, forecast_y + 8), size=16, color=COLOR_GRAY
                    )

                    # Temperature
                    renderer.draw_text(
                        draw,
                        f"{day_temp}°",
                        (fx, forecast_y + 32),
                        font=renderer.font_tiny,
                        color=COLOR_WHITE,
                        anchor="mm",
                    )

    def _render_compact(
        self,
        renderer: Renderer,
        draw: ImageDraw.ImageDraw,
        rect: tuple[int, int, int, int],
        icon_name: str,
        temperature: Any,
        humidity: Any,
        condition: str,
        padding: int,
    ) -> None:
        """Render compact weather (for smaller slots)."""
        x1, y1, x2, y2 = rect
        height = y2 - y1
        center_y = y1 + height // 2

        # Icon on left, temp on right
        icon_size = min(32, height - 20)
        renderer.draw_icon(
            draw,
            icon_name,
            (x1 + padding, center_y - icon_size // 2),
            size=icon_size,
            color=COLOR_GOLD,
        )

        # Temperature
        temp_str = f"{temperature}°" if temperature != "--" else "--"
        renderer.draw_text(
            draw,
            temp_str,
            (x2 - padding, center_y - 5),
            font=renderer.font_large,
            color=COLOR_WHITE,
            anchor="rm",
        )

        # Humidity below temp
        if self.show_humidity:
            renderer.draw_text(
                draw,
                f"{humidity}%",
                (x2 - padding, center_y + 15),
                font=renderer.font_tiny,
                color=COLOR_CYAN,
                anchor="rm",
            )
