"""Weather widget for GeekMagic displays."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..const import (
    COLOR_CYAN,
    COLOR_GOLD,
)
from .base import Widget, WidgetConfig
from .components import (
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    Column,
    Component,
    Icon,
    Padding,
    Row,
    Stack,
    Text,
)

if TYPE_CHECKING:
    from ..render_context import RenderContext
    from .state import WidgetState


WEATHER_ICONS = {
    "sunny": "weather-sunny",
    "clear-night": "weather-night",
    "partlycloudy": "weather-partly-cloudy",
    "cloudy": "weather-cloudy",
    "rainy": "weather-rainy",
    "pouring": "weather-pouring",
    "snowy": "weather-snowy",
    "snowy-rainy": "weather-snowy-rainy",
    "fog": "weather-fog",
    "hail": "weather-hail",
    "windy": "weather-windy",
    "windy-variant": "weather-windy-variant",
    "lightning": "weather-lightning",
    "lightning-rainy": "weather-lightning-rainy",
    "exceptional": "alert-circle",
}


@dataclass
class WeatherDisplay(Component):
    """Weather display component."""

    temperature: Any = "--"
    humidity: Any = "--"
    condition: str = "sunny"
    forecast: list[dict] = field(default_factory=list)
    show_forecast: bool = True
    show_humidity: bool = True
    show_high_low: bool = True
    forecast_days: int = 3

    def measure(self, ctx: RenderContext, max_width: int, max_height: int) -> tuple[int, int]:
        return (max_width, max_height)

    def render(self, ctx: RenderContext, x: int, y: int, width: int, height: int) -> None:
        """Render weather."""
        icon_name = WEATHER_ICONS.get(self.condition, "weather-sunny")

        if height > 120 and self.show_forecast:
            component = self._build_full(ctx, width, height, icon_name)
        else:
            component = self._build_compact(ctx, width, height, icon_name)

        component.render(ctx, x, y, width, height)

    def _build_full(
        self,
        ctx: RenderContext,
        width: int,
        height: int,
        icon_name: str,
    ) -> Component:
        """Build full weather layout with forecast."""
        padding = int(width * 0.04)
        icon_size = max(24, int(height * 0.25))

        # Main weather display (icon, temp, condition)
        temp_str = f"{self.temperature}°" if self.temperature != "--" else "--"

        main_weather = Column(
            children=[
                Icon(icon_name, size=icon_size, color=COLOR_GOLD),
                Text(temp_str, font="xlarge", color=THEME_TEXT_PRIMARY),
                Text(
                    self.condition.replace("-", " ").title(),
                    font="small",
                    color=THEME_TEXT_SECONDARY,
                ),
            ],
            gap=int(height * 0.04),
            align="center",
            justify="start",
            padding=padding,
        )

        # Humidity indicator (if enabled)
        humidity_row = None
        if self.show_humidity:
            humidity_icon_size = max(8, int(height * 0.07))
            humidity_row = Row(
                children=[
                    Icon("water-percent", size=humidity_icon_size, color=COLOR_CYAN),
                    Text(f"{self.humidity}%", font="tiny", color=COLOR_CYAN, align="start"),
                ],
                gap=4,
                align="center",
                justify="start",
                padding=padding,
            )

        # Forecast items
        forecast_component = None
        if self.forecast and self.show_forecast:
            forecast_items = self.forecast[: self.forecast_days]
            if forecast_items:
                forecast_icon_size = max(10, int(height * 0.10))
                forecast_columns = []

                for i, day in enumerate(forecast_items):
                    day_condition = day.get("condition", "sunny")
                    day_temp = day.get("temperature", "--")
                    day_temp_low = day.get("templow")
                    day_name = day.get("datetime", "")[:3] if day.get("datetime") else f"D{i + 1}"
                    day_icon = WEATHER_ICONS.get(day_condition, "weather-sunny")

                    if self.show_high_low and day_temp_low is not None:
                        temp_str = f"{day_temp}°/{day_temp_low}°"
                    else:
                        temp_str = f"{day_temp}°"

                    forecast_columns.append(
                        Column(
                            children=[
                                Text(day_name.upper(), font="tiny", color=THEME_TEXT_SECONDARY),
                                Icon(day_icon, size=forecast_icon_size, color=THEME_TEXT_SECONDARY),
                                Text(temp_str, font="tiny", color=THEME_TEXT_PRIMARY),
                            ],
                            gap=int(height * 0.02),
                            align="center",
                            justify="center",
                        )
                    )

                forecast_component = Row(
                    children=forecast_columns,
                    gap=0,
                    align="center",
                    justify="space-around",
                    padding=padding,
                )

        # Build the final layout
        if humidity_row and forecast_component:
            # All three sections - use absolute positioning via Stack
            return Stack(
                children=[
                    main_weather,
                    # Position humidity slightly below center
                    Padding(
                        child=humidity_row,
                        top=int(height * 0.35),
                    ),
                    # Position forecast at bottom
                    Padding(
                        child=forecast_component,
                        top=int(height * 0.72),
                    ),
                ]
            )
        if humidity_row:
            # Just main + humidity
            return Column(
                children=[main_weather, humidity_row],
                gap=int(height * 0.05),
                align="start",
                justify="start",
            )
        if forecast_component:
            # Just main + forecast
            return Column(
                children=[main_weather, forecast_component],
                gap=int(height * 0.10),
                align="center",
                justify="space-between",
            )
        # Just main weather
        return main_weather

    def _build_compact(
        self,
        ctx: RenderContext,
        width: int,
        height: int,
        icon_name: str,
    ) -> Component:
        """Build compact weather layout."""
        padding = int(width * 0.04)
        icon_size = max(16, min(32, int(height * 0.40)))
        temp_str = f"{self.temperature}°" if self.temperature != "--" else "--"

        # Left side: icon
        left_side = Icon(icon_name, size=icon_size, color=COLOR_GOLD)

        # Right side: temperature and optionally humidity
        right_children = [Text(temp_str, font="large", color=THEME_TEXT_PRIMARY, align="end")]

        if self.show_humidity:
            right_children.append(
                Text(f"{self.humidity}%", font="tiny", color=COLOR_CYAN, align="end")
            )

        right_side = Column(
            children=right_children,
            gap=int(height * 0.08),
            align="end",
            justify="center",
        )

        return Row(
            children=[left_side, right_side],
            gap=padding,
            align="center",
            justify="space-between",
            padding=padding,
        )


def _weather_placeholder() -> Component:
    """Create placeholder component when no weather data."""
    return Column(
        children=[
            Icon("weather-cloudy", color=THEME_TEXT_SECONDARY, max_size=48),
            Text("No Weather Data", font="small", color=THEME_TEXT_SECONDARY),
        ],
        gap=8,
        align="center",
        justify="center",
    )


class WeatherWidget(Widget):
    """Widget that displays weather information."""

    def __init__(self, config: WidgetConfig) -> None:
        """Initialize the weather widget."""
        super().__init__(config)
        self.show_forecast = config.options.get("show_forecast", True)
        self.forecast_days = config.options.get("forecast_days", 3)
        self.show_humidity = config.options.get("show_humidity", True)
        self.show_wind = config.options.get("show_wind", False)
        self.show_high_low = config.options.get("show_high_low", True)

    def render(self, ctx: RenderContext, state: WidgetState) -> Component:
        """Render the weather widget."""
        entity = state.entity

        if entity is None:
            return _weather_placeholder()

        return WeatherDisplay(
            temperature=entity.get("temperature", "--"),
            humidity=entity.get("humidity", "--"),
            condition=entity.state,
            forecast=entity.get("forecast", []),
            show_forecast=self.show_forecast,
            show_humidity=self.show_humidity,
            show_high_low=self.show_high_low,
            forecast_days=self.forecast_days,
        )
