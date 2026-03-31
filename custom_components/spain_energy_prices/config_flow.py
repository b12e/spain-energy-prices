"""Config flow for Spain Energy Prices integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_ELECTRICITY_TAX,
    CONF_IVA,
    CONF_P1_POWER_KW,
    CONF_P1_POWER_PRICE,
    CONF_P1_PRICE,
    CONF_P2_POWER_KW,
    CONF_P2_POWER_PRICE,
    CONF_P2_PRICE,
    CONF_P3_PRICE,
    DEFAULT_ELECTRICITY_TAX,
    DEFAULT_IVA,
    DEFAULT_P1_POWER_KW,
    DEFAULT_P1_POWER_PRICE,
    DEFAULT_P1_PRICE,
    DEFAULT_P2_POWER_KW,
    DEFAULT_P2_POWER_PRICE,
    DEFAULT_P2_PRICE,
    DEFAULT_P3_PRICE,
    DOMAIN,
)

PRICE_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=0, step=0.000001, mode=NumberSelectorMode.BOX)
)
KW_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=0, step=0.01, mode=NumberSelectorMode.BOX)
)
TAX_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=0, max=100, step=0.01, mode=NumberSelectorMode.BOX)
)


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the voluptuous schema, seeding defaults from existing config."""
    d = defaults.get
    return vol.Schema(
        {
            vol.Required(CONF_P1_PRICE, default=d(CONF_P1_PRICE, DEFAULT_P1_PRICE)): PRICE_SELECTOR,
            vol.Required(CONF_P2_PRICE, default=d(CONF_P2_PRICE, DEFAULT_P2_PRICE)): PRICE_SELECTOR,
            vol.Required(CONF_P3_PRICE, default=d(CONF_P3_PRICE, DEFAULT_P3_PRICE)): PRICE_SELECTOR,
            vol.Required(CONF_P1_POWER_PRICE, default=d(CONF_P1_POWER_PRICE, DEFAULT_P1_POWER_PRICE)): PRICE_SELECTOR,
            vol.Required(CONF_P2_POWER_PRICE, default=d(CONF_P2_POWER_PRICE, DEFAULT_P2_POWER_PRICE)): PRICE_SELECTOR,
            vol.Required(CONF_P1_POWER_KW, default=d(CONF_P1_POWER_KW, DEFAULT_P1_POWER_KW)): KW_SELECTOR,
            vol.Required(CONF_P2_POWER_KW, default=d(CONF_P2_POWER_KW, DEFAULT_P2_POWER_KW)): KW_SELECTOR,
            vol.Required(CONF_ELECTRICITY_TAX, default=d(CONF_ELECTRICITY_TAX, DEFAULT_ELECTRICITY_TAX)): TAX_SELECTOR,
            vol.Required(CONF_IVA, default=d(CONF_IVA, DEFAULT_IVA)): TAX_SELECTOR,
        }
    )


class SpainEnergyPricesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spain Energy Prices."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Spain Energy Prices",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SpainEnergyPricesOptionsFlow:
        """Return the options flow handler."""
        return SpainEnergyPricesOptionsFlow()


class SpainEnergyPricesOptionsFlow(config_entries.OptionsFlow):
    """Handle the options flow for Spain Energy Prices."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Manage the options — edit existing prices."""
        current: dict = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(current),
        )
