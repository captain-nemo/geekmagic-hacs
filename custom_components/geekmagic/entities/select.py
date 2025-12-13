"""Select entities for GeekMagic integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    CONF_LAYOUT,
    CONF_SCREENS,
    CONF_WIDGETS,
    DOMAIN,
    LAYOUT_GRID_2X2,
    LAYOUT_GRID_2X3,
    LAYOUT_HERO,
    LAYOUT_SLOT_COUNTS,
    LAYOUT_SPLIT,
    LAYOUT_THREE_COLUMN,
    WIDGET_TYPE_NAMES,
)
from .entity import GeekMagicEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator

LAYOUT_OPTIONS = {
    LAYOUT_GRID_2X2: "Grid 2x2 (4 slots)",
    LAYOUT_GRID_2X3: "Grid 2x3 (6 slots)",
    LAYOUT_HERO: "Hero (4 slots)",
    LAYOUT_SPLIT: "Split (2 slots)",
    LAYOUT_THREE_COLUMN: "Three Column (3 slots)",
}

WIDGET_OPTIONS = {
    "empty": "Empty",
    **WIDGET_TYPE_NAMES,
}

TEMPLATE_OPTIONS = {
    "custom": "Custom",
    "system_monitor": "System Monitor",
    "smart_home": "Smart Home",
    "weather": "Weather Dashboard",
    "media_player": "Media Player",
    "clock": "Clock Dashboard",
    "energy": "Energy Monitor",
    "security": "Security",
}


@dataclass(frozen=True, kw_only=True)
class GeekMagicSelectEntityDescription(SelectEntityDescription):
    """Describes a GeekMagic select entity."""

    screen_index: int | None = None
    slot_index: int | None = None
    select_type: str = ""  # "current_screen", "layout", "template", "widget_type"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic select entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track created entity IDs to avoid duplicates
    current_entity_ids: set[str] = set()

    @callback
    def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        entities_to_add: list[GeekMagicSelectEntity] = []

        # Current screen selector (always exists)
        current_screen_key = "current_screen"
        if current_screen_key not in current_entity_ids:
            current_entity_ids.add(current_screen_key)
            entities_to_add.append(
                GeekMagicCurrentScreenSelect(
                    coordinator,
                    GeekMagicSelectEntityDescription(
                        key=current_screen_key,
                        translation_key="current_screen",
                        icon="mdi:monitor",
                        entity_category=EntityCategory.CONFIG,
                        select_type="current_screen",
                    ),
                )
            )

        # Per-screen entities
        screens = coordinator.options.get(CONF_SCREENS, [])
        for screen_idx, screen_config in enumerate(screens):
            # Screen template selector
            template_key = f"screen_{screen_idx + 1}_template"
            if template_key not in current_entity_ids:
                current_entity_ids.add(template_key)
                entities_to_add.append(
                    GeekMagicScreenTemplateSelect(
                        coordinator,
                        GeekMagicSelectEntityDescription(
                            key=template_key,
                            translation_key="screen_template",
                            icon="mdi:view-dashboard",
                            entity_category=EntityCategory.CONFIG,
                            select_type="template",
                            screen_index=screen_idx,
                        ),
                    )
                )

            # Screen layout selector
            layout_key = f"screen_{screen_idx + 1}_layout"
            if layout_key not in current_entity_ids:
                current_entity_ids.add(layout_key)
                entities_to_add.append(
                    GeekMagicScreenLayoutSelect(
                        coordinator,
                        GeekMagicSelectEntityDescription(
                            key=layout_key,
                            translation_key="screen_layout",
                            icon="mdi:view-grid",
                            entity_category=EntityCategory.CONFIG,
                            select_type="layout",
                            screen_index=screen_idx,
                        ),
                    )
                )

            # Per-slot widget type and entity selectors
            layout_type = screen_config.get(CONF_LAYOUT, LAYOUT_GRID_2X2)
            slot_count = LAYOUT_SLOT_COUNTS.get(layout_type, 4)

            for slot_idx in range(slot_count):
                # Widget type selector
                widget_key = f"screen_{screen_idx + 1}_slot_{slot_idx + 1}_widget"
                if widget_key not in current_entity_ids:
                    current_entity_ids.add(widget_key)
                    entities_to_add.append(
                        GeekMagicSlotWidgetSelect(
                            coordinator,
                            GeekMagicSelectEntityDescription(
                                key=widget_key,
                                translation_key="slot_widget",
                                icon="mdi:widgets",
                                entity_category=EntityCategory.CONFIG,
                                select_type="widget_type",
                                screen_index=screen_idx,
                                slot_index=slot_idx,
                            ),
                        )
                    )

                # Entity selector (dropdown with all available entities)
                entity_key = f"screen_{screen_idx + 1}_slot_{slot_idx + 1}_entity"
                if entity_key not in current_entity_ids:
                    current_entity_ids.add(entity_key)
                    entities_to_add.append(
                        GeekMagicSlotEntitySelect(
                            coordinator,
                            hass,
                            GeekMagicSelectEntityDescription(
                                key=entity_key,
                                translation_key="slot_entity",
                                icon="mdi:identifier",
                                entity_category=EntityCategory.CONFIG,
                                select_type="entity",
                                screen_index=screen_idx,
                                slot_index=slot_idx,
                            ),
                        )
                    )

        if entities_to_add:
            async_add_entities(entities_to_add)

    # Initial setup
    async_update_entities()

    # Listen for coordinator updates to add new entities
    entry.async_on_unload(coordinator.async_add_listener(async_update_entities))


class GeekMagicSelectEntity(GeekMagicEntity, SelectEntity):
    """Base class for GeekMagic select entities."""

    entity_description: GeekMagicSelectEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, description)


class GeekMagicCurrentScreenSelect(GeekMagicSelectEntity):
    """Select entity for current screen."""

    @property
    def options(self) -> list[str]:
        """Return available options."""
        screens = self.coordinator.options.get(CONF_SCREENS, [])
        return [screen.get("name", f"Screen {i + 1}") for i, screen in enumerate(screens)] or [
            "Screen 1"
        ]

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self.coordinator.current_screen_name

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        screens = self.coordinator.options.get(CONF_SCREENS, [])
        for i, screen in enumerate(screens):
            if screen.get("name", f"Screen {i + 1}") == option:
                await self.coordinator.async_set_screen(i)
                break


class GeekMagicScreenTemplateSelect(GeekMagicSelectEntity):
    """Select entity for screen template."""

    @property
    def options(self) -> list[str]:
        """Return available template options."""
        return list(TEMPLATE_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        """Return the current template (always 'Custom' since we don't track this)."""
        return "Custom"

    async def async_select_option(self, option: str) -> None:
        """Apply a template to the screen."""
        from ..templates import apply_template

        screen_idx = self.entity_description.screen_index
        if screen_idx is None:
            return

        # Find template key from display name
        template_key = None
        for key, name in TEMPLATE_OPTIONS.items():
            if name == option:
                template_key = key
                break

        if template_key and template_key != "custom":
            entry = self._get_config_entry()
            await apply_template(
                self.hass,
                entry,
                screen_idx,
                template_key,
            )

    @property
    def name(self) -> str:
        """Return entity name with screen context."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is not None:
            # "Apply" sorts before "Layout" and "Name"
            return f"Screen {screen_idx + 1} Apply Template"
        return "Apply Template"


class GeekMagicScreenLayoutSelect(GeekMagicSelectEntity):
    """Select entity for screen layout."""

    @property
    def options(self) -> list[str]:
        """Return available layout options."""
        return list(LAYOUT_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        """Return the current layout."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is None:
            return None

        screens = self.coordinator.options.get(CONF_SCREENS, [])
        if screen_idx < len(screens):
            layout = screens[screen_idx].get(CONF_LAYOUT, LAYOUT_GRID_2X2)
            return LAYOUT_OPTIONS.get(layout, "Grid 2x2 (4 slots)")
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the screen layout."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is None:
            return

        # Find layout key from display name
        layout_key = None
        for key, name in LAYOUT_OPTIONS.items():
            if name == option:
                layout_key = key
                break

        if layout_key:
            entry = self._get_config_entry()
            new_options = dict(entry.options)
            screens = list(new_options.get(CONF_SCREENS, []))

            if screen_idx < len(screens):
                screens[screen_idx] = dict(screens[screen_idx])
                screens[screen_idx][CONF_LAYOUT] = layout_key
                new_options[CONF_SCREENS] = screens

                self.hass.config_entries.async_update_entry(
                    entry,
                    options=new_options,
                )

    @property
    def name(self) -> str:
        """Return entity name with screen context."""
        screen_idx = self.entity_description.screen_index
        if screen_idx is not None:
            return f"Screen {screen_idx + 1} Layout"
        return "Layout"


class GeekMagicSlotWidgetSelect(GeekMagicSelectEntity):
    """Select entity for slot widget type."""

    @property
    def options(self) -> list[str]:
        """Return available widget options."""
        return list(WIDGET_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        """Return the current widget type."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        if screen_idx is None or slot_idx is None:
            return None

        screens = self.coordinator.options.get(CONF_SCREENS, [])
        if screen_idx < len(screens):
            widgets = screens[screen_idx].get(CONF_WIDGETS, [])
            for widget in widgets:
                if widget.get("slot") == slot_idx:
                    widget_type = widget.get("type", "empty")
                    return WIDGET_OPTIONS.get(widget_type, "Empty")
        return "Empty"

    async def async_select_option(self, option: str) -> None:
        """Change the slot widget type."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        if screen_idx is None or slot_idx is None:
            return

        # Find widget type key from display name
        widget_type = None
        for key, name in WIDGET_OPTIONS.items():
            if name == option:
                widget_type = key
                break

        if widget_type is None:
            return

        entry = self._get_config_entry()
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        if screen_idx < len(screens):
            screens[screen_idx] = dict(screens[screen_idx])
            widgets = list(screens[screen_idx].get(CONF_WIDGETS, []))

            # Find existing widget for this slot
            found = False
            for i, widget in enumerate(widgets):
                if widget.get("slot") == slot_idx:
                    if widget_type == "empty":
                        # Remove the widget
                        widgets.pop(i)
                    else:
                        # Update the widget type
                        widgets[i] = dict(widget)
                        widgets[i]["type"] = widget_type
                    found = True
                    break

            if not found and widget_type != "empty":
                # Add new widget
                widgets.append({"type": widget_type, "slot": slot_idx})

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
            # "Display" sorts before "Entity" and "Label"
            return f"Screen {screen_idx + 1} Slot {slot_idx + 1} Display"
        return "Display"


# Domain filters for each widget type
# Only show entities from these domains when the widget type is set
WIDGET_DOMAIN_FILTERS: dict[str, list[str]] = {
    "camera": ["camera"],
    "weather": ["weather"],
    "media": ["media_player"],
    "entity": ["sensor", "binary_sensor", "input_number", "input_boolean", "counter"],
    "gauge": ["sensor", "input_number", "counter", "number"],
    "chart": ["sensor", "input_number", "counter", "number"],
    "progress": ["sensor", "input_number", "counter", "number"],
    "status": ["binary_sensor", "switch", "light", "lock", "device_tracker", "input_boolean"],
    "text": ["sensor", "input_text", "input_number"],
    # clock and empty don't need entities
}


class GeekMagicSlotEntitySelect(GeekMagicSelectEntity):
    """Select entity for slot entity_id with dropdown picker.

    This provides a filtered dropdown of Home Assistant entities
    based on the widget type for easier selection.
    """

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        hass: HomeAssistant,
        description: GeekMagicSelectEntityDescription,
    ) -> None:
        """Initialize the entity selector."""
        super().__init__(coordinator, description)
        self._hass_ref = hass

    def _get_widget_config(self) -> dict | None:
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

    def _get_widget_type(self) -> str | None:
        """Get the current widget type for this slot."""
        widget = self._get_widget_config()
        if widget:
            return widget.get("type")
        return None

    @property
    def options(self) -> list[str]:
        """Return available entity options filtered by widget type.

        Returns a list of entity IDs relevant to the current widget type.
        """
        widget_type = self._get_widget_type()

        # Get domain filter for this widget type
        allowed_domains = WIDGET_DOMAIN_FILTERS.get(widget_type) if widget_type else None

        if allowed_domains:
            # Filter entities by domain
            entity_ids = [
                eid
                for eid in self._hass_ref.states.async_entity_ids()
                if eid.split(".")[0] in allowed_domains
            ]
        else:
            # No filter - show common sensor-like entities
            common_domains = ["sensor", "binary_sensor", "input_number", "input_boolean"]
            entity_ids = [
                eid
                for eid in self._hass_ref.states.async_entity_ids()
                if eid.split(".")[0] in common_domains
            ]

        # Sort for consistency
        entity_ids = sorted(entity_ids)

        # Add "None" option at the start to allow clearing
        return ["(none)", *entity_ids]

    @property
    def current_option(self) -> str | None:
        """Return the current entity_id."""
        widget = self._get_widget_config()
        if widget:
            entity_id = widget.get("entity_id", "")
            if entity_id:
                return entity_id
        return "(none)"

    async def async_select_option(self, option: str) -> None:
        """Set the entity_id."""
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

        # Determine entity_id value (empty if "(none)")
        entity_id = "" if option == "(none)" else option

        # Find or update widget for this slot
        found = False
        for i, widget in enumerate(widgets):
            if widget.get("slot") == slot_idx:
                widgets[i] = dict(widget)
                if entity_id:
                    widgets[i]["entity_id"] = entity_id
                elif "entity_id" in widgets[i]:
                    del widgets[i]["entity_id"]
                found = True
                break

        if not found and entity_id:
            # Widget doesn't exist yet - can't set entity_id without type
            return

        screens[screen_idx][CONF_WIDGETS] = widgets
        new_options[CONF_SCREENS] = screens

        self._hass_ref.config_entries.async_update_entry(
            entry,
            options=new_options,
        )

    @property
    def name(self) -> str:
        """Return entity name with screen and slot context."""
        screen_idx = self.entity_description.screen_index
        slot_idx = self.entity_description.slot_index
        if screen_idx is not None and slot_idx is not None:
            return f"Screen {screen_idx + 1} Slot {slot_idx + 1} Entity"
        return "Entity"
