"""Number entities for GeekMagic integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    CONF_REFRESH_INTERVAL,
    CONF_SCREEN_CYCLE_INTERVAL,
    CONF_SCREENS,
    DEFAULT_REFRESH_INTERVAL,
    DEFAULT_SCREEN_CYCLE_INTERVAL,
    DOMAIN,
)
from .entity import GeekMagicEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator


@dataclass(frozen=True, kw_only=True)
class GeekMagicNumberEntityDescription(NumberEntityDescription):
    """Describes a GeekMagic number entity."""

    option_key: str | None = None


DEVICE_NUMBERS: tuple[GeekMagicNumberEntityDescription, ...] = (
    GeekMagicNumberEntityDescription(
        key="brightness",
        translation_key="brightness",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:brightness-6",
        option_key="brightness",
    ),
    GeekMagicNumberEntityDescription(
        key="refresh_interval",
        translation_key="refresh_interval",
        native_min_value=5,
        native_max_value=300,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:refresh",
        option_key=CONF_REFRESH_INTERVAL,
    ),
    GeekMagicNumberEntityDescription(
        key="screen_cycle_interval",
        translation_key="screen_cycle_interval",
        native_min_value=0,
        native_max_value=300,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:timer-outline",
        option_key=CONF_SCREEN_CYCLE_INTERVAL,
    ),
    GeekMagicNumberEntityDescription(
        key="screen_count",
        translation_key="screen_count",
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:monitor-multiple",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic number entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[GeekMagicNumberEntity] = [
        GeekMagicNumberEntity(coordinator, description) for description in DEVICE_NUMBERS
    ]

    async_add_entities(entities)


class GeekMagicNumberEntity(GeekMagicEntity, NumberEntity):
    """A GeekMagic number entity."""

    entity_description: GeekMagicNumberEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        key = self.entity_description.key

        if key == "brightness":
            return self.coordinator.brightness
        if key == "refresh_interval":
            return self.coordinator.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
        if key == "screen_cycle_interval":
            return self.coordinator.options.get(
                CONF_SCREEN_CYCLE_INTERVAL, DEFAULT_SCREEN_CYCLE_INTERVAL
            )
        if key == "screen_count":
            screens = self.coordinator.options.get(CONF_SCREENS, [])
            return len(screens) if screens else 1

        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        key = self.entity_description.key
        int_value = int(value)

        if key == "brightness":
            await self.coordinator.async_set_brightness(int_value)
            await self._async_update_options("brightness", int_value)
        elif key == "refresh_interval":
            await self._async_update_options(CONF_REFRESH_INTERVAL, int_value)
        elif key == "screen_cycle_interval":
            await self._async_update_options(CONF_SCREEN_CYCLE_INTERVAL, int_value)
        elif key == "screen_count":
            await self._update_screen_count(int_value)

    async def _update_screen_count(self, count: int) -> None:
        """Update the number of screens."""
        entry = self._get_config_entry()
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        current_count = len(screens)

        if count > current_count:
            # Add new screens with default config
            screens.extend(
                {
                    "name": f"Screen {i + 1}",
                    "layout": "grid_2x2",
                    "widgets": [{"type": "clock", "slot": 0}],
                }
                for i in range(current_count, count)
            )
        elif count < current_count:
            # Remove screens from the end
            screens = screens[:count]

        new_options[CONF_SCREENS] = screens
        self.hass.config_entries.async_update_entry(
            entry,
            options=new_options,
        )
