"""Preview rendering for GeekMagic configuration flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from .const import (
    CONF_LAYOUT,
    CONF_WIDGETS,
    LAYOUT_GRID_2X2,
    LAYOUT_GRID_2X3,
    LAYOUT_GRID_3X2,
    LAYOUT_GRID_3X3,
    LAYOUT_HERO,
    LAYOUT_SPLIT_H,
    LAYOUT_SPLIT_H_1_2,
    LAYOUT_SPLIT_H_2_1,
    LAYOUT_SPLIT_V,
    LAYOUT_THREE_COLUMN,
    LAYOUT_THREE_ROW,
)
from .layouts.grid import Grid2x2, Grid2x3, Grid3x2, Grid3x3
from .layouts.hero import HeroLayout
from .layouts.split import (
    SplitHorizontal,
    SplitHorizontal1To2,
    SplitHorizontal2To1,
    SplitVertical,
    ThreeColumnLayout,
    ThreeRowLayout,
)
from .renderer import Renderer
from .widgets.base import WidgetConfig
from .widgets.chart import ChartWidget
from .widgets.clock import ClockWidget
from .widgets.entity import EntityWidget
from .widgets.gauge import GaugeWidget
from .widgets.media import MediaWidget
from .widgets.progress import MultiProgressWidget, ProgressWidget
from .widgets.status import StatusListWidget, StatusWidget
from .widgets.text import TextWidget
from .widgets.weather import WeatherWidget

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

LAYOUT_CLASSES = {
    LAYOUT_GRID_2X2: Grid2x2,
    LAYOUT_GRID_2X3: Grid2x3,
    LAYOUT_GRID_3X2: Grid3x2,
    LAYOUT_GRID_3X3: Grid3x3,
    LAYOUT_HERO: HeroLayout,
    LAYOUT_SPLIT_H: SplitHorizontal,
    LAYOUT_SPLIT_H_1_2: SplitHorizontal1To2,
    LAYOUT_SPLIT_H_2_1: SplitHorizontal2To1,
    LAYOUT_SPLIT_V: SplitVertical,
    LAYOUT_THREE_COLUMN: ThreeColumnLayout,
    LAYOUT_THREE_ROW: ThreeRowLayout,
}

WIDGET_CLASSES = {
    "clock": ClockWidget,
    "entity": EntityWidget,
    "media": MediaWidget,
    "chart": ChartWidget,
    "text": TextWidget,
    "gauge": GaugeWidget,
    "progress": ProgressWidget,
    "multi_progress": MultiProgressWidget,
    "status": StatusWidget,
    "status_list": StatusListWidget,
    "weather": WeatherWidget,
}


@dataclass
class MockState:
    """Mock entity state for preview rendering."""

    entity_id: str
    state: str
    attributes: dict[str, Any] = field(default_factory=dict)


class MockStates:
    """Mock states registry for preview rendering."""

    def __init__(self) -> None:
        """Initialize the mock states registry."""
        self._states: dict[str, MockState] = {}

    def set(self, entity_id: str, state: str, attributes: dict[str, Any] | None = None) -> None:
        """Set a mock entity state."""
        self._states[entity_id] = MockState(
            entity_id=entity_id,
            state=state,
            attributes=attributes or {},
        )

    def get(self, entity_id: str) -> MockState | None:
        """Get a mock entity state."""
        return self._states.get(entity_id)


class MockConfig:
    """Mock Home Assistant config."""

    time_zone_obj = None


class MockHass:
    """Mock Home Assistant instance for preview rendering."""

    def __init__(self) -> None:
        """Initialize the mock Home Assistant."""
        self.states = MockStates()
        self.config = MockConfig()


def _set_mock_state_for_widget(mock: MockHass, widget_config: dict[str, Any]) -> None:
    """Set mock state for a widget based on its type.

    Args:
        mock: MockHass instance
        widget_config: Widget configuration dictionary
    """
    widget_type = widget_config.get("type", "")
    entity_id = widget_config.get("entity_id")

    if not entity_id:
        return

    # Set appropriate mock state based on widget type
    if widget_type == "entity":
        mock.states.set(
            entity_id,
            "42",
            {"unit_of_measurement": "", "friendly_name": widget_config.get("label", "Entity")},
        )
    elif widget_type == "gauge":
        mock.states.set(
            entity_id,
            "65",
            {"unit_of_measurement": "%", "friendly_name": widget_config.get("label", "Gauge")},
        )
    elif widget_type == "progress":
        mock.states.set(
            entity_id,
            "75",
            {"unit_of_measurement": "", "friendly_name": widget_config.get("label", "Progress")},
        )
    elif widget_type == "status":
        mock.states.set(
            entity_id,
            "on",
            {"friendly_name": widget_config.get("label", "Status")},
        )
    elif widget_type == "media":
        mock.states.set(
            entity_id,
            "playing",
            {
                "friendly_name": "Media Player",
                "media_title": "Sample Track",
                "media_artist": "Sample Artist",
                "media_position": 120,
                "media_duration": 300,
            },
        )
    elif widget_type == "chart":
        mock.states.set(
            entity_id,
            "23",
            {"unit_of_measurement": "°C", "friendly_name": widget_config.get("label", "Chart")},
        )
    elif widget_type == "weather":
        mock.states.set(
            entity_id,
            "sunny",
            {
                "temperature": 24,
                "humidity": 45,
                "friendly_name": "Weather",
                "forecast": [
                    {"datetime": "Mon", "condition": "sunny", "temperature": 26},
                    {"datetime": "Tue", "condition": "cloudy", "temperature": 22},
                    {"datetime": "Wed", "condition": "rainy", "temperature": 18},
                ],
            },
        )
    elif widget_type == "text" and entity_id:
        mock.states.set(
            entity_id,
            widget_config.get("options", {}).get("text", "Sample"),
            {"friendly_name": widget_config.get("label", "Text")},
        )

    # Handle list-based widgets
    options = widget_config.get("options", {})

    if widget_type == "multi_progress":
        items = options.get("items", [])
        for item in items:
            item_entity = item.get("entity_id")
            if item_entity:
                mock.states.set(
                    item_entity,
                    "50",
                    {"unit_of_measurement": "", "friendly_name": item.get("label", "Item")},
                )

    elif widget_type == "status_list":
        entities = options.get("entities", [])
        for entry in entities:
            ent_id = entry[0] if isinstance(entry, list | tuple) else entry
            if ent_id:
                friendly = (
                    entry[1] if isinstance(entry, list | tuple) and len(entry) > 1 else ent_id
                )
                mock.states.set(ent_id, "on", {"friendly_name": friendly})


def render_preview(
    layout_type: str,
    widgets_config: list[dict[str, Any]],
    hass: HomeAssistant | None = None,
) -> bytes:
    """Render a preview image for the given configuration.

    Args:
        layout_type: Layout type string (grid_2x2, grid_2x3, hero, split)
        widgets_config: List of widget configuration dictionaries
        hass: Optional Home Assistant instance (uses mock if None)

    Returns:
        PNG image bytes
    """
    # Use mock hass if no real one provided
    # Cast to Any to satisfy type checker since MockHass mimics HomeAssistant interface
    if hass is None:
        mock = MockHass()
        for widget_config in widgets_config:
            _set_mock_state_for_widget(mock, widget_config)
        render_hass: Any = cast("Any", mock)
    else:
        render_hass = cast("Any", hass)

    # Create renderer and layout
    renderer = Renderer()
    layout_class = LAYOUT_CLASSES.get(layout_type, Grid2x2)
    layout = layout_class()

    # Create and assign widgets
    for widget_config in widgets_config:
        widget_type = str(widget_config.get("type", "text"))
        slot = int(widget_config.get("slot", 0))

        if slot >= layout.get_slot_count():
            continue

        widget_class = WIDGET_CLASSES.get(widget_type)
        if widget_class is None:
            continue

        entity_id = widget_config.get("entity_id")
        label = widget_config.get("label")
        raw_color = widget_config.get("color")
        widget_options = widget_config.get("options") or {}

        # Parse color
        parsed_color: tuple[int, int, int] | None = None
        if isinstance(raw_color, list | tuple) and len(raw_color) == 3:
            parsed_color = (int(raw_color[0]), int(raw_color[1]), int(raw_color[2]))

        config = WidgetConfig(
            widget_type=widget_type,
            slot=slot,
            entity_id=str(entity_id) if entity_id is not None else None,
            label=str(label) if label is not None else None,
            color=parsed_color,
            options=cast("dict[str, Any]", widget_options),
        )

        widget = widget_class(config)
        layout.set_widget(slot, widget)

    # Render to image
    img, draw = renderer.create_canvas()
    layout.render(renderer, draw, render_hass)

    return renderer.to_png(img)


def render_screen_preview(
    screen_config: dict[str, Any], hass: HomeAssistant | None = None
) -> bytes:
    """Render a preview for a complete screen configuration.

    Args:
        screen_config: Screen configuration with layout and widgets
        hass: Optional Home Assistant instance

    Returns:
        PNG image bytes
    """
    layout_type = screen_config.get(CONF_LAYOUT, LAYOUT_GRID_2X2)
    widgets_config = screen_config.get(CONF_WIDGETS, [])

    return render_preview(layout_type, widgets_config, hass)
