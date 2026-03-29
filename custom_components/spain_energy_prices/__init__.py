"""Spain Energy Prices — Home Assistant custom integration.

Calculates real electricity costs for the Spanish 2.0TD tariff by applying
Impuesto Eléctrico and IVA to user-supplied base prices for P1/P2/P3 periods
and contracted power.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORM_SENSOR

PLATFORMS = [PLATFORM_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spain Energy Prices from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Merge initial config data with any options (options take precedence)
    hass.data[DOMAIN][entry.entry_id] = {**entry.data, **entry.options}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry whenever the user saves new prices via the options flow
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so sensors pick up the updated prices immediately."""
    await hass.config_entries.async_reload(entry.entry_id)
