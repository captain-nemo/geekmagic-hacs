"""Button entities for GeekMagic integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from .entity import GeekMagicEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator


@dataclass(frozen=True, kw_only=True)
class GeekMagicButtonEntityDescription(ButtonEntityDescription):
    """Describes a GeekMagic button entity."""

    action: str = ""


DEVICE_BUTTONS: tuple[GeekMagicButtonEntityDescription, ...] = (
    GeekMagicButtonEntityDescription(
        key="refresh_now",
        translation_key="refresh_now",
        icon="mdi:refresh",
        entity_category=EntityCategory.CONFIG,
        action="refresh",
    ),
    GeekMagicButtonEntityDescription(
        key="next_screen",
        translation_key="next_screen",
        icon="mdi:chevron-right",
        entity_category=EntityCategory.CONFIG,
        action="next_screen",
    ),
    GeekMagicButtonEntityDescription(
        key="previous_screen",
        translation_key="previous_screen",
        icon="mdi:chevron-left",
        entity_category=EntityCategory.CONFIG,
        action="previous_screen",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GeekMagic button entities."""
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[GeekMagicButtonEntity] = [
        GeekMagicButtonEntity(coordinator, description) for description in DEVICE_BUTTONS
    ]

    async_add_entities(entities)


class GeekMagicButtonEntity(GeekMagicEntity, ButtonEntity):
    """A GeekMagic button entity."""

    entity_description: GeekMagicButtonEntityDescription

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: GeekMagicButtonEntityDescription,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, description)

    async def async_press(self) -> None:
        """Handle the button press."""
        action = self.entity_description.action

        if action == "refresh":
            await self.coordinator.async_refresh_display()
        elif action == "next_screen":
            await self.coordinator.async_next_screen()
        elif action == "previous_screen":
            await self.coordinator.async_previous_screen()
