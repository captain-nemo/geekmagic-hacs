"""Switch entities for GeekMagic integration (boolean widget options)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    CONF_LAYOUT,
    CONF_SCREENS,
    CONF_WIDGETS,
    DOMAIN,
    LAYOUT_GRID_2X2,
    LAYOUT_SLOT_COUNTS,
)
from .entity import GeekMagicEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator


# Widget option definitions: widget_type -> list of (option_key, display_name, default, icon)
WIDGET_BOOLEAN_OPTIONS: dict[str, list[tuple[str, str, bool, str]]] = {
    "clock": [
        ("show_seconds", "Show Seconds", False, "mdi:clock-outline"),
        ("show_date", "Show Date", True, "mdi:calendar"),
    ],
    "entity": [
        ("show_name", "Show Name", True, "mdi:label"),
        ("show_unit", "Show Unit", True, "mdi:ruler"),
        ("show_panel", "Show Panel", False, "mdi:card"),
    ],
    "chart": [
        ("show_value", "Show Value", True, "mdi:numeric"),
        ("show_range", "Show Range", True, "mdi:arrow-expand-vertical"),
    ],
    "media": [
        ("show_artist", "Show Artist", True, "mdi:account-music"),
        ("show_album", "Show Album", False, "mdi:album"),
        ("show_progress", "Show Progress", True, "mdi:progress-clock"),
    ],
    "weather": [
        ("show_forecast", "Show Forecast", True, "mdi:weather-partly-cloudy"),
        ("show_humidity", "Show Humidity", True, "mdi:water-percent"),
        ("show_wind", "Show Wind", False, "mdi:weather-windy"),
    ],
    "progress": [
        ("show_target", "Show Target", True, "mdi:target"),
    ],
    "camera": [
        ("show_label", "Show Label", False, "mdi:label"),
    ],
}


@dataclass(frozen=True, kw_only=True)
class GeekMagicSwitchEntityDescription(SwitchEntityDescription):
    """Describes a GeekMagic switch entity."""

    screen_index: int | None = None
    slot_index: int | None = None
    option_key: str = ""
    default_value: bool = False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic switch entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track created entity IDs
    current_entity_ids: set[str] = set()

    @callback
    def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        entities_to_add: list[GeekMagicWidgetOptionSwitch] = []

        screens = coordinator.options.get(CONF_SCREENS, [])
        for screen_idx, screen_config in enumerate(screens):
            layout_type = screen_config.get(CONF_LAYOUT, LAYOUT_GRID_2X2)
            slot_count = LAYOUT_SLOT_COUNTS.get(layout_type, 4)
            widgets = screen_config.get(CONF_WIDGETS, [])

            # Build widget map for quick lookup
            widget_map: dict[int, dict[str, Any]] = {}
            for widget in widgets:
                slot = widget.get("slot")
                if slot is not None:
                    widget_map[slot] = widget

            for slot_idx in range(slot_count):
                widget = widget_map.get(slot_idx, {})
                widget_type = widget.get("type")

                if widget_type and widget_type in WIDGET_BOOLEAN_OPTIONS:
                    bool_opts = WIDGET_BOOLEAN_OPTIONS[widget_type]
                    for option_key, display_name, default, icon in bool_opts:
                        entity_key = f"screen_{screen_idx + 1}_slot_{slot_idx + 1}_{option_key}"

                        if entity_key not in current_entity_ids:
                            current_entity_ids.add(entity_key)
                            # "Opt:" prefix sorts after Display, Entity, Label
                            name = (
                                f"Screen {screen_idx + 1} Slot {slot_idx + 1} Opt: {display_name}"
                            )
                            entities_to_add.append(
                                GeekMagicWidgetOptionSwitch(
                                    coordinator,
                                    GeekMagicSwitchEntityDescription(
                                        key=entity_key,
                                        name=name,
                                        icon=icon,
                                        entity_category=EntityCategory.CONFIG,
                                        screen_index=screen_idx,
                                        slot_index=slot_idx,
                                        option_key=option_key,
                                        default_value=default,
                                    ),
                                )
                            )

        if entities_to_add:
            async_add_entities(entities_to_add)

    # Initial setup
    async_update_entities()

    # Listen for coordinator updates
    entry.async_on_unload(coordinator.async_add_listener(async_update_entities))


class GeekMagicWidgetOptionSwitch(GeekMagicEntity, SwitchEntity):
    """Switch entity for a widget boolean option."""

    entity_description: GeekMagicSwitchEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicSwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, description)

    def _get_widget_config(self) -> dict[str, Any] | None:
        """Get the widget configuration for this slot."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        if screen_idx is None or slot_idx is None:
            return None

        screens = self.coordinator.options.get(CONF_SCREENS, [])
        if screen_idx >= len(screens):
            return None

        widgets = screens[screen_idx].get(CONF_WIDGETS, [])
        for widget in widgets:
            if widget.get("slot") == slot_idx:
                return widget
        return None

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        widget = self._get_widget_config()
        if widget is None:
            return self.entity_description.default_value

        options = widget.get("options", {})
        return options.get(
            self.entity_description.option_key,
            self.entity_description.default_value,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Only available if the widget exists and has this option
        widget = self._get_widget_config()
        if widget is None:
            return False

        widget_type = widget.get("type")
        if widget_type not in WIDGET_BOOLEAN_OPTIONS:
            return False

        # Check if this option applies to this widget type
        option_keys = [opt[0] for opt in WIDGET_BOOLEAN_OPTIONS.get(widget_type, [])]
        return self.entity_description.option_key in option_keys

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_option(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_option(False)

    async def _async_set_option(self, value: bool) -> None:
        """Set the widget option value."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        option_key = self.entity_description.option_key

        if screen_idx is None or slot_idx is None:
            return

        entry = self._get_config_entry()
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        if screen_idx >= len(screens):
            return

        screens[screen_idx] = dict(screens[screen_idx])
        widgets = list(screens[screen_idx].get(CONF_WIDGETS, []))

        # Find the widget for this slot
        found = False
        for i, widget in enumerate(widgets):
            if widget.get("slot") == slot_idx:
                widgets[i] = dict(widget)
                widget_options = dict(widgets[i].get("options", {}))
                widget_options[option_key] = value
                widgets[i]["options"] = widget_options
                found = True
                break

        if found:
            screens[screen_idx][CONF_WIDGETS] = widgets
            new_options[CONF_SCREENS] = screens

            self.hass.config_entries.async_update_entry(
                entry,
                options=new_options,
            )
