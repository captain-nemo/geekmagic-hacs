"""Sensor entities for GeekMagic integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_LAYOUT,
    CONF_SCREENS,
    DOMAIN,
    LAYOUT_GRID_2X2,
    LAYOUT_SLOT_COUNTS,
)
from .entity import GeekMagicEntity

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator


# Divider line character for visual separation
DIVIDER_LINE = "─" * 12


@dataclass(frozen=True, kw_only=True)
class GeekMagicSensorEntityDescription(SensorEntityDescription):
    """Describes a GeekMagic sensor entity."""

    screen_index: int | None = None
    slot_index: int | None = None
    is_divider: bool = False


DEVICE_SENSORS: tuple[GeekMagicSensorEntityDescription, ...] = (
    GeekMagicSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:monitor-eye",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GeekMagicSensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    GeekMagicSensorEntityDescription(
        key="current_screen_name",
        translation_key="current_screen_name",
        icon="mdi:monitor",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic sensor entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Fixed device sensors
    entities: list[SensorEntity] = [
        GeekMagicSensorEntity(coordinator, description) for description in DEVICE_SENSORS
    ]

    async_add_entities(entities)

    # Track created divider IDs
    current_divider_ids: set[str] = set()

    @callback
    def async_update_dividers() -> None:
        """Create divider entities for screens and slots."""
        dividers_to_add: list[GeekMagicDividerEntity] = []

        screens = coordinator.options.get(CONF_SCREENS, [])
        for screen_idx, screen_config in enumerate(screens):
            # Screen header divider - "(" sorts before "A" (Apply Template)
            screen_divider_key = f"screen_{screen_idx + 1}_divider"
            if screen_divider_key not in current_divider_ids:
                current_divider_ids.add(screen_divider_key)
                dividers_to_add.append(
                    GeekMagicDividerEntity(
                        coordinator,
                        GeekMagicSensorEntityDescription(
                            key=screen_divider_key,
                            icon="mdi:page-layout-header",
                            entity_category=EntityCategory.CONFIG,
                            screen_index=screen_idx,
                            is_divider=True,
                        ),
                        # Use "(" prefix to sort before "Apply Template"
                        name=f"Screen {screen_idx + 1} (────────────)",
                    )
                )

            # Slot dividers
            layout_type = screen_config.get(CONF_LAYOUT, LAYOUT_GRID_2X2)
            slot_count = LAYOUT_SLOT_COUNTS.get(layout_type, 4)

            for slot_idx in range(slot_count):
                # Slot header divider - "(" sorts before "D" (Display)
                slot_divider_key = f"screen_{screen_idx + 1}_slot_{slot_idx + 1}_divider"
                if slot_divider_key not in current_divider_ids:
                    current_divider_ids.add(slot_divider_key)
                    dividers_to_add.append(
                        GeekMagicDividerEntity(
                            coordinator,
                            GeekMagicSensorEntityDescription(
                                key=slot_divider_key,
                                icon="mdi:widgets-outline",
                                entity_category=EntityCategory.CONFIG,
                                screen_index=screen_idx,
                                slot_index=slot_idx,
                                is_divider=True,
                            ),
                            # Use "(" prefix to sort before "Display"
                            name=f"Screen {screen_idx + 1} Slot {slot_idx + 1} (────────)",
                        )
                    )

        if dividers_to_add:
            async_add_entities(dividers_to_add)

    # Initial setup
    async_update_dividers()

    # Listen for coordinator updates
    entry.async_on_unload(coordinator.async_add_listener(async_update_dividers))


class GeekMagicSensorEntity(GeekMagicEntity, SensorEntity):
    """A GeekMagic sensor entity."""

    entity_description: GeekMagicSensorEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicSensorEntityDescription,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> str | datetime | None:
        """Return the sensor value."""
        key = self.entity_description.key

        if key == "status":
            if self.coordinator.last_update_success:
                return "connected"
            return "disconnected"
        if key == "last_update":
            if self.coordinator.last_update_time:
                return dt_util.utc_from_timestamp(self.coordinator.last_update_time)
            return None
        if key == "current_screen_name":
            return self.coordinator.current_screen_name

        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int] | None:
        """Return additional state attributes."""
        key = self.entity_description.key

        if key == "status":
            return {
                "host": self.coordinator.device.host,
                "screen_count": self.coordinator.screen_count,
                "current_screen": self.coordinator.current_screen,
            }
        if key == "current_screen_name":
            return {
                "screen_index": self.coordinator.current_screen,
                "total_screens": self.coordinator.screen_count,
            }

        return None


class GeekMagicDividerEntity(GeekMagicEntity, SensorEntity):
    """A visual divider entity for organizing config sections."""

    entity_description: GeekMagicSensorEntityDescription
    _attr_entity_registry_enabled_default = False  # Disabled by default

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicSensorEntityDescription,
        name: str,
    ) -> None:
        """Initialize the divider entity."""
        super().__init__(coordinator, description)
        self._divider_name = name

    @property
    def native_value(self) -> str:
        """Return a divider line."""
        return DIVIDER_LINE

    @property
    def name(self) -> str:
        """Return the divider name."""
        return self._divider_name
