"""Text entities for GeekMagic integration.

Text entities are used for:
- Screen names (user-defined labels)
- Slot labels (custom widget labels)

Note: Entity ID selection is handled by select entities for better UX.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.text import TextEntity, TextEntityDescription
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


@dataclass(frozen=True, kw_only=True)
class GeekMagicTextEntityDescription(TextEntityDescription):
    """Describes a GeekMagic text entity."""

    screen_index: int | None = None
    slot_index: int | None = None
    text_type: str = ""  # "screen_name", "slot_label"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic text entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track created entity IDs
    current_entity_ids: set[str] = set()

    @callback
    def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        entities_to_add: list[GeekMagicTextEntity] = []

        screens = coordinator.options.get(CONF_SCREENS, [])
        for screen_idx, screen_config in enumerate(screens):
            # Screen name text entity
            name_key = f"screen_{screen_idx + 1}_name"
            if name_key not in current_entity_ids:
                current_entity_ids.add(name_key)
                entities_to_add.append(
                    GeekMagicScreenNameText(
                        coordinator,
                        GeekMagicTextEntityDescription(
                            key=name_key,
                            translation_key="screen_name",
                            icon="mdi:rename",
                            entity_category=EntityCategory.CONFIG,
                            screen_index=screen_idx,
                            text_type="screen_name",
                        ),
                    )
                )

            # Per-slot label text entities
            layout_type = screen_config.get(CONF_LAYOUT, LAYOUT_GRID_2X2)
            slot_count = LAYOUT_SLOT_COUNTS.get(layout_type, 4)

            for slot_idx in range(slot_count):
                # Label text
                label_key = f"screen_{screen_idx + 1}_slot_{slot_idx + 1}_label"
                if label_key not in current_entity_ids:
                    current_entity_ids.add(label_key)
                    entities_to_add.append(
                        GeekMagicSlotLabelText(
                            coordinator,
                            GeekMagicTextEntityDescription(
                                key=label_key,
                                translation_key="slot_label",
                                icon="mdi:label",
                                entity_category=EntityCategory.CONFIG,
                                screen_index=screen_idx,
                                slot_index=slot_idx,
                                text_type="slot_label",
                            ),
                        )
                    )

        if entities_to_add:
            async_add_entities(entities_to_add)

    # Initial setup
    async_update_entities()

    # Listen for coordinator updates
    entry.async_on_unload(coordinator.async_add_listener(async_update_entities))


class GeekMagicTextEntity(GeekMagicEntity, TextEntity):
    """Base class for GeekMagic text entities."""

    entity_description: GeekMagicTextEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicTextEntityDescription,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator, description)


class GeekMagicScreenNameText(GeekMagicTextEntity):
    """Text entity for screen name."""

    @property
    def native_value(self) -> str | None:
        """Return the current screen name."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is None:
            return None

        screens = self.coordinator.options.get(CONF_SCREENS, [])
        if screen_idx < len(screens):
            return screens[screen_idx].get("name", f"Screen {screen_idx + 1}")
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the screen name."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is None:
            return

        entry = self._get_config_entry()
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        if screen_idx < len(screens):
            screens[screen_idx] = dict(screens[screen_idx])
            screens[screen_idx]["name"] = value
            new_options[CONF_SCREENS] = screens

            self.hass.config_entries.async_update_entry(
                entry,
                options=new_options,
            )

    @property
    def name(self) -> str:
        """Return entity name."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is not None:
            return f"Screen {screen_idx + 1} Name"
        return "Screen Name"


class GeekMagicSlotLabelText(GeekMagicTextEntity):
    """Text entity for slot label."""

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
    def native_value(self) -> str | None:
        """Return the current label."""
        widget = self._get_widget_config()
        if widget:
            return widget.get("label", "")
        return ""

    async def async_set_value(self, value: str) -> None:
        """Set the label."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index

        if screen_idx is None or slot_idx is None:
            return

        entry = self._get_config_entry()
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        if screen_idx >= len(screens):
            return

        screens[screen_idx] = dict(screens[screen_idx])
        widgets = list(screens[screen_idx].get(CONF_WIDGETS, []))

        # Find widget for this slot
        found = False
        for i, widget in enumerate(widgets):
            if widget.get("slot") == slot_idx:
                widgets[i] = dict(widget)
                if value:
                    widgets[i]["label"] = value
                elif "label" in widgets[i]:
                    del widgets[i]["label"]
                found = True
                break

        if not found:
            return

        screens[screen_idx][CONF_WIDGETS] = widgets
        new_options[CONF_SCREENS] = screens

        self.hass.config_entries.async_update_entry(
            entry,
            options=new_options,
        )

    @property
    def name(self) -> str:
        """Return entity name with screen and slot context."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        if screen_idx is not None and slot_idx is not None:
            return f"Screen {screen_idx + 1} Slot {slot_idx + 1} Label"
        return "Slot Label"
