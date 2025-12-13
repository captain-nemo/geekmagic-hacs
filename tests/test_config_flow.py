"""Tests for GeekMagic config flow."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from homeassistant.data_entry_flow import FlowResultType

from custom_components.geekmagic.config_flow import (
    GeekMagicConfigFlow,
    GeekMagicOptionsFlow,
)
from custom_components.geekmagic.const import (
    CONF_LAYOUT,
    CONF_REFRESH_INTERVAL,
    CONF_SCREEN_CYCLE_INTERVAL,
    CONF_SCREENS,
    CONF_WIDGETS,
    DEFAULT_REFRESH_INTERVAL,
    DEFAULT_SCREEN_CYCLE_INTERVAL,
    DOMAIN,
    LAYOUT_GRID_2X2,
)


class TestConfigFlowImports:
    """Test that config flow can be imported without errors."""

    def test_import_config_flow(self):
        """Test config flow module imports successfully."""
        from custom_components.geekmagic import config_flow

        assert config_flow.GeekMagicConfigFlow is not None
        assert config_flow.GeekMagicOptionsFlow is not None

    def test_config_flow_class_attributes(self):
        """Test GeekMagicConfigFlow has required attributes."""
        assert hasattr(GeekMagicConfigFlow, "VERSION")
        assert hasattr(GeekMagicConfigFlow, "async_step_user")
        assert hasattr(GeekMagicConfigFlow, "async_get_options_flow")


class TestConfigFlowUser:
    """Test user config flow step using hass fixture."""

    @pytest.mark.asyncio
    async def test_user_flow_shows_form(self, hass):
        """Test that user flow shows the configuration form."""
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert "host" in result["data_schema"].schema

    @pytest.mark.asyncio
    async def test_user_flow_connection_failure(self, hass):
        """Test user flow handles connection failure."""
        with (
            patch(
                "custom_components.geekmagic.config_flow.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.geekmagic.config_flow.GeekMagicDevice") as mock_device_class,
        ):
            mock_get_session.return_value = AsyncMock()
            mock_device = mock_device_class.return_value
            mock_device.test_connection = AsyncMock(return_value=False)

            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={"host": "192.168.1.100", "name": "Test Display"},
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

        await hass.async_block_till_done()

    @pytest.mark.asyncio
    async def test_user_flow_success(self, hass):
        """Test successful user flow creates entry."""
        with (
            patch(
                "custom_components.geekmagic.config_flow.async_get_clientsession"
            ) as mock_get_session,
            patch("custom_components.geekmagic.config_flow.GeekMagicDevice") as mock_device_class,
            # Mock the integration setup to prevent actual device connection
            patch(
                "custom_components.geekmagic.async_setup_entry",
                return_value=True,
            ),
        ):
            mock_get_session.return_value = AsyncMock()
            mock_device = mock_device_class.return_value
            mock_device.test_connection = AsyncMock(return_value=True)

            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={"host": "192.168.1.100", "name": "Test Display"},
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "Test Display"
            assert result["data"]["host"] == "192.168.1.100"

            # Check default options were created
            assert CONF_SCREENS in result["options"]
            assert CONF_REFRESH_INTERVAL in result["options"]
            assert CONF_SCREEN_CYCLE_INTERVAL in result["options"]

        await hass.async_block_till_done()


class TestOptionsFlowInit:
    """Test options flow initialization."""

    def test_options_flow_init(self):
        """Test GeekMagicOptionsFlow can be instantiated."""
        flow = GeekMagicOptionsFlow()
        assert flow is not None


class TestDefaultOptions:
    """Test default options generation."""

    def test_get_default_options(self):
        """Test default options are properly structured."""
        flow = GeekMagicConfigFlow()
        defaults = flow._get_default_options()

        assert CONF_REFRESH_INTERVAL in defaults
        assert defaults[CONF_REFRESH_INTERVAL] == DEFAULT_REFRESH_INTERVAL
        assert CONF_SCREEN_CYCLE_INTERVAL in defaults
        assert defaults[CONF_SCREEN_CYCLE_INTERVAL] == DEFAULT_SCREEN_CYCLE_INTERVAL
        assert CONF_SCREENS in defaults
        assert len(defaults[CONF_SCREENS]) == 1
        assert defaults[CONF_SCREENS][0]["name"] == "Screen 1"
        assert defaults[CONF_SCREENS][0][CONF_LAYOUT] == LAYOUT_GRID_2X2
        assert len(defaults[CONF_SCREENS][0][CONF_WIDGETS]) == 1
        assert defaults[CONF_SCREENS][0][CONF_WIDGETS][0]["type"] == "clock"
