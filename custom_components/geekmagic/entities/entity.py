"""Base entity class for GeekMagic integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ..coordinator import GeekMagicCoordinator


@dataclass(frozen=True, kw_only=True)
class GeekMagicEntityDescription(EntityDescription):
    """Base description for GeekMagic entities."""

    # Additional fields can be added in subclasses


class GeekMagicEntity(CoordinatorEntity["GeekMagicCoordinator"]):
    """Base class for GeekMagic entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GeekMagicCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: GeekMagic coordinator
            description: Entity description
        """
        super().__init__(coordinator)
        self.entity_description = description
        # Config entry is always set when entities are created
        entry = self._get_config_entry()
        # Use host as unique ID base to match image entity
        host = entry.data[CONF_HOST]
        self._attr_unique_id = f"{host}_{description.key}"

    def _get_config_entry(self) -> ConfigEntry:
        """Get the config entry, asserting it exists.

        Returns:
            The config entry

        Raises:
            AssertionError: If config_entry is None (should never happen)
        """
        entry = self.coordinator.config_entry
        assert entry is not None, "Config entry must be set"
        return entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        entry = self._get_config_entry()
        # Use host as identifier to match image entity
        host = entry.data[CONF_HOST]
        return DeviceInfo(
            identifiers={(DOMAIN, host)},
            name=entry.data.get(CONF_NAME, "GeekMagic Display"),
            manufacturer="GeekMagic",
            model="SmallTV Pro",
            sw_version=self.coordinator.device_version,
            configuration_url=f"http://{host}",
        )

    async def _async_update_options(self, key: str, value: Any) -> None:
        """Update a single option in the config entry.

        Args:
            key: Option key to update
            value: New value
        """
        entry = self._get_config_entry()
        new_options = dict(entry.options)
        new_options[key] = value
        self.hass.config_entries.async_update_entry(
            entry,
            options=new_options,
        )
