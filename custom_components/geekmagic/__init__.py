"""GeekMagic Display integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_LAYOUT,
    CONF_SCREENS,
    CONF_WIDGETS,
    DOMAIN,
    LAYOUT_GRID_2X2,
)
from .coordinator import GeekMagicCoordinator
from .device import GeekMagicDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.BUTTON,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GeekMagic from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup successful
    """
    host = entry.data[CONF_HOST]
    _LOGGER.debug("Setting up GeekMagic integration for %s", host)

    session = async_get_clientsession(hass)
    device = GeekMagicDevice(host, session=session)

    # Test connection
    if not await device.test_connection():
        _LOGGER.error("Could not connect to GeekMagic device at %s", host)
        return False

    _LOGGER.debug("Successfully connected to GeekMagic device at %s", host)

    # Create coordinator
    coordinator = GeekMagicCoordinator(
        hass=hass,
        device=device,
        options=dict(entry.options),
        config_entry=entry,
    )

    # Do first refresh
    _LOGGER.debug("Performing first refresh for %s", host)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_options_update_listener))

    # Register services
    await async_setup_services(hass)

    # Set up platforms (camera)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("GeekMagic integration successfully set up for %s", host)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload successful
    """
    host = entry.data.get(CONF_HOST, "unknown")
    _LOGGER.debug("Unloading GeekMagic integration for %s", host)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        del hass.data[DOMAIN][entry.entry_id]
        _LOGGER.debug("GeekMagic integration unloaded for %s", host)

    return unload_ok


async def async_options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    host = entry.data.get(CONF_HOST, "unknown")
    _LOGGER.debug("Options updated for GeekMagic device %s", host)
    coordinator: GeekMagicCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.update_options(dict(entry.options))
    # Trigger immediate refresh so device displays updated config
    await coordinator.async_request_refresh()


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up GeekMagic services.

    Args:
        hass: Home Assistant instance
    """
    # Skip if already registered
    if hass.services.has_service(DOMAIN, "refresh"):
        return

    async def handle_refresh(call: ServiceCall) -> None:
        """Handle refresh service call."""
        entry_id = call.data.get("entry_id")

        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator:
                await coordinator.async_refresh_display()
        else:
            # Refresh all displays
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_refresh_display()

    async def handle_brightness(call: ServiceCall) -> None:
        """Handle brightness service call."""
        entry_id = call.data.get("entry_id")
        brightness = call.data.get("brightness", 50)

        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator:
                await coordinator.async_set_brightness(brightness)
        else:
            # Set brightness on all displays
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_set_brightness(brightness)

    async def handle_set_screen(call: ServiceCall) -> None:
        """Handle set_screen service call."""
        entry_id = call.data.get("entry_id")
        screen_index = call.data.get("screen_index", 0)

        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator:
                await coordinator.async_set_screen(screen_index)
        else:
            # Set screen on all displays
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_set_screen(screen_index)

    async def handle_next_screen(call: ServiceCall) -> None:
        """Handle next_screen service call."""
        entry_id = call.data.get("entry_id")

        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator:
                await coordinator.async_next_screen()
        else:
            # Next screen on all displays
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_next_screen()

    async def handle_previous_screen(call: ServiceCall) -> None:
        """Handle previous_screen service call."""
        entry_id = call.data.get("entry_id")

        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator:
                await coordinator.async_previous_screen()
        else:
            # Previous screen on all displays
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_previous_screen()

    async def handle_configure_screen(call: ServiceCall) -> None:
        """Handle configure_screen service call.

        Allows programmatic screen configuration via automations.
        """
        entry_id = call.data.get("entry_id")
        screen_index = call.data.get("screen", 1) - 1  # Convert to 0-based
        template = call.data.get("template")
        layout = call.data.get("layout")
        name = call.data.get("name")

        coordinator = hass.data[DOMAIN].get(entry_id)
        if not coordinator or not coordinator.config_entry:
            _LOGGER.warning("configure_screen: entry_id %s not found", entry_id)
            return

        entry = coordinator.config_entry
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        # Ensure screen exists
        while len(screens) <= screen_index:
            screens.append(
                {
                    "name": f"Screen {len(screens) + 1}",
                    CONF_LAYOUT: LAYOUT_GRID_2X2,
                    CONF_WIDGETS: [],
                }
            )

        screens[screen_index] = dict(screens[screen_index])

        # Apply template if specified
        if template:
            from .templates import apply_template

            await apply_template(hass, entry, screen_index, template)
            return  # Template applies everything

        # Apply individual settings
        if name:
            screens[screen_index]["name"] = name
        if layout:
            screens[screen_index][CONF_LAYOUT] = layout

        new_options[CONF_SCREENS] = screens
        hass.config_entries.async_update_entry(entry, options=new_options)

    async def handle_configure_widget(call: ServiceCall) -> None:
        """Handle configure_widget service call.

        Allows programmatic widget configuration via automations.
        """
        entry_id = call.data.get("entry_id")
        screen_index = call.data.get("screen", 1) - 1  # Convert to 0-based
        slot_index = call.data.get("slot", 1) - 1  # Convert to 0-based
        widget_type = call.data.get("widget_type")
        entity_id = call.data.get("entity_id")
        label = call.data.get("label")
        options = call.data.get("options", {})

        coordinator = hass.data[DOMAIN].get(entry_id)
        if not coordinator or not coordinator.config_entry:
            _LOGGER.warning("configure_widget: entry_id %s not found", entry_id)
            return

        entry = coordinator.config_entry
        new_options = dict(entry.options)
        screens = list(new_options.get(CONF_SCREENS, []))

        if screen_index >= len(screens):
            _LOGGER.warning("configure_widget: screen %d not found", screen_index + 1)
            return

        screens[screen_index] = dict(screens[screen_index])
        widgets = list(screens[screen_index].get(CONF_WIDGETS, []))

        # Find or create widget for this slot
        found = False
        for i, widget in enumerate(widgets):
            if widget.get("slot") == slot_index:
                if widget_type == "empty":
                    widgets.pop(i)
                else:
                    widgets[i] = dict(widget)
                    if widget_type:
                        widgets[i]["type"] = widget_type
                    if entity_id:
                        widgets[i]["entity_id"] = entity_id
                    if label:
                        widgets[i]["label"] = label
                    if options:
                        widgets[i]["options"] = {
                            **widgets[i].get("options", {}),
                            **options,
                        }
                found = True
                break

        if not found and widget_type and widget_type != "empty":
            new_widget: dict = {"type": widget_type, "slot": slot_index}
            if entity_id:
                new_widget["entity_id"] = entity_id
            if label:
                new_widget["label"] = label
            if options:
                new_widget["options"] = options
            widgets.append(new_widget)

        screens[screen_index][CONF_WIDGETS] = widgets
        new_options[CONF_SCREENS] = screens
        hass.config_entries.async_update_entry(entry, options=new_options)

    hass.services.async_register(DOMAIN, "refresh", handle_refresh)
    hass.services.async_register(DOMAIN, "brightness", handle_brightness)
    hass.services.async_register(DOMAIN, "set_screen", handle_set_screen)
    hass.services.async_register(DOMAIN, "next_screen", handle_next_screen)
    hass.services.async_register(DOMAIN, "previous_screen", handle_previous_screen)
    hass.services.async_register(DOMAIN, "configure_screen", handle_configure_screen)
    hass.services.async_register(DOMAIN, "configure_widget", handle_configure_widget)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry being removed
    """
    # Clean up any resources if needed
