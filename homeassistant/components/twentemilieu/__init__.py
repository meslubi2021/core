"""Support for Twente Milieu."""
from __future__ import annotations

from datetime import date, timedelta

from twentemilieu import TwenteMilieu, WasteType
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_HOUSE_LETTER, CONF_HOUSE_NUMBER, CONF_POST_CODE, DOMAIN, LOGGER

SCAN_INTERVAL = timedelta(seconds=3600)

SERVICE_UPDATE = "update"
SERVICE_SCHEMA = vol.Schema({vol.Optional(CONF_ID): cv.string})

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Twente Milieu from a config entry."""
    session = async_get_clientsession(hass)
    twentemilieu = TwenteMilieu(
        post_code=entry.data[CONF_POST_CODE],
        house_number=entry.data[CONF_HOUSE_NUMBER],
        house_letter=entry.data[CONF_HOUSE_LETTER],
        session=session,
    )

    coordinator: DataUpdateCoordinator[
        dict[WasteType, list[date]]
    ] = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
        update_interval=SCAN_INTERVAL,
        update_method=twentemilieu.update,
    )
    await coordinator.async_config_entry_first_refresh()

    # For backwards compat, set unique ID
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=str(entry.data[CONF_ID])
        )

    hass.data.setdefault(DOMAIN, {})[entry.data[CONF_ID]] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Twente Milieu config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN][entry.data[CONF_ID]]
    return unload_ok
