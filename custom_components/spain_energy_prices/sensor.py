"""Sensors for Spain Energy Prices integration."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import holidays
from homeassistant import config_entries
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time, async_track_time_interval
from homeassistant.util import dt as dt_util

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
    DOMAIN,
    PERIOD_BOUNDARIES,
    PERIOD_P1,
    PERIOD_P2,
    PERIOD_P3,
    SENSOR_ENERGY_COST,
    SENSOR_ENERGY_PERIOD,
    SENSOR_POWER_COST_DAILY,
    UPDATE_INTERVAL_SECONDS,
)


# ---------------------------------------------------------------------------
# Pure calculation helpers
# ---------------------------------------------------------------------------


def get_spanish_holidays(year: int) -> set[date]:
    """Return Spanish national + Valencian public holidays for the given year."""
    return set(holidays.Spain(subdiv="VC", years=year).keys())


def get_current_period(dt: datetime, holiday_cache: dict[int, set[date]]) -> str:
    """Determine the current 2.0TD tariff period (P1 / P2 / P3).

    dt must be a timezone-aware datetime in local (Europe/Madrid) time.
    holiday_cache maps year -> set[date] and is populated lazily.
    """
    today = dt.date()
    year = today.year

    if year not in holiday_cache:
        holiday_cache[year] = get_spanish_holidays(year)

    weekday = dt.weekday()  # 0 = Monday, 6 = Sunday
    hour = dt.hour

    is_weekend = weekday >= 5
    is_holiday = today in holiday_cache[year]

    if is_weekend or is_holiday:
        return PERIOD_P3

    # Weekday (Mon–Fri), non-holiday
    if hour < 8:
        return PERIOD_P3
    if hour < 10:
        return PERIOD_P2
    if hour < 14:
        return PERIOD_P1
    if hour < 18:
        return PERIOD_P2
    if hour < 22:
        return PERIOD_P1
    return PERIOD_P2  # 22:00–00:00


def calculate_price_with_tax(
    base_price: float,
    electricity_tax_pct: float,
    iva_pct: float,
) -> dict[str, float]:
    """Apply Spanish electricity taxes to a base energy price (€/kWh).

    Formula: final = base × (1 + elec_tax/100) × (1 + iva/100)
    Returns a dict with intermediate values for use as sensor attributes.
    """
    after_electricity_tax = base_price * (1 + electricity_tax_pct / 100)
    final_price = after_electricity_tax * (1 + iva_pct / 100)
    return {
        "base_price": round(base_price, 6),
        "after_electricity_tax": round(after_electricity_tax, 6),
        "final_price": round(final_price, 6),
    }


def calculate_daily_power_cost(
    p1_power_price: float,
    p2_power_price: float,
    p1_power_kw: float,
    p2_power_kw: float,
    electricity_tax_pct: float,
    iva_pct: float,
) -> float:
    """Calculate the total daily fixed power cost including taxes (€/day).

    Formula: (P1_price × P1_kW + P2_price × P2_kW) × (1 + elec_tax/100) × (1 + iva/100)
    """
    base_daily = p1_power_price * p1_power_kw + p2_power_price * p2_power_kw
    taxed = base_daily * (1 + electricity_tax_pct / 100) * (1 + iva_pct / 100)
    return round(taxed, 6)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Spain Energy Prices sensors from a config entry."""
    config: dict = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        SpainEnergyCostSensor(hass, entry, config),
        SpainEnergyPeriodSensor(hass, entry, config),
        SpainPowerCostDailySensor(hass, entry, config),
    ]
    async_add_entities(entities, update_before_add=True)


# ---------------------------------------------------------------------------
# Base sensor
# ---------------------------------------------------------------------------


class SpainEnergyBaseSensor(SensorEntity):
    """Base class for Spain Energy Prices sensors.

    Registers two update mechanisms:
    1. A 60-second safety-net poll via async_track_time_interval.
    2. Precise one-shot callbacks at each 2.0TD period boundary via
       async_track_point_in_time (self-rescheduling after each fire).
    """

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry,
        config: dict,
        sensor_type: str,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._config = config
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_has_entity_name = True
        self._holiday_cache: dict[int, set[date]] = {}
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Spain Energy Prices",
            "manufacturer": "Custom",
            "model": "2.0TD Tariff Calculator",
        }

    async def async_added_to_hass(self) -> None:
        """Register time-tracking callbacks when the entity is added."""
        self.async_on_remove(
            async_track_time_interval(
                self._hass,
                self._handle_interval_update,
                timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            )
        )
        self._schedule_next_boundary()

    @callback
    def _handle_interval_update(self, _now: datetime | None = None) -> None:
        """Triggered by the 60-second interval tracker."""
        self.async_write_ha_state()

    @callback
    def _schedule_next_boundary(self) -> None:
        """Schedule a one-shot callback at the next period boundary."""
        now = dt_util.now()
        next_boundary = self._get_next_boundary(now)

        @callback
        def _boundary_fired(_point_in_time: datetime) -> None:
            self.async_write_ha_state()
            self._schedule_next_boundary()

        self.async_on_remove(
            async_track_point_in_time(
                self._hass,
                _boundary_fired,
                next_boundary,
            )
        )

    def _get_next_boundary(self, now: datetime) -> datetime:
        """Return the next period-boundary datetime strictly after now."""
        today = now.date()
        for hour, minute in PERIOD_BOUNDARIES:
            candidate = dt_util.as_local(
                datetime(
                    today.year,
                    today.month,
                    today.day,
                    hour,
                    minute,
                    1,  # +1 second to avoid firing exactly on the boundary
                    tzinfo=dt_util.DEFAULT_TIME_ZONE,
                )
            )
            if candidate > now:
                return candidate
        # All boundaries today have passed; first one tomorrow is 00:00:01
        tomorrow = today + timedelta(days=1)
        return dt_util.as_local(
            datetime(
                tomorrow.year,
                tomorrow.month,
                tomorrow.day,
                0,
                0,
                1,
                tzinfo=dt_util.DEFAULT_TIME_ZONE,
            )
        )

    def _get_current_period(self) -> str:
        return get_current_period(dt_util.now(), self._holiday_cache)

    def _get_base_price_for_period(self, period: str) -> float:
        return {
            PERIOD_P1: self._config[CONF_P1_PRICE],
            PERIOD_P2: self._config[CONF_P2_PRICE],
            PERIOD_P3: self._config[CONF_P3_PRICE],
        }[period]


# ---------------------------------------------------------------------------
# Energy cost sensor  (€/kWh including taxes)
# ---------------------------------------------------------------------------


class SpainEnergyCostSensor(SpainEnergyBaseSensor):
    """Current energy cost in €/kWh including all Spanish taxes."""

    _attr_icon = "mdi:currency-eur"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: config_entries.ConfigEntry, config: dict) -> None:
        super().__init__(hass, entry, config, SENSOR_ENERGY_COST)
        self._attr_name = "Energy Cost"
        self._attr_native_unit_of_measurement = "€/kWh"

    @property
    def native_value(self) -> float:
        """Return the current energy price including taxes."""
        period = self._get_current_period()
        base = self._get_base_price_for_period(period)
        return calculate_price_with_tax(
            base,
            self._config[CONF_ELECTRICITY_TAX],
            self._config[CONF_IVA],
        )["final_price"]

    @property
    def extra_state_attributes(self) -> dict:
        period = self._get_current_period()
        base = self._get_base_price_for_period(period)
        result = calculate_price_with_tax(
            base,
            self._config[CONF_ELECTRICITY_TAX],
            self._config[CONF_IVA],
        )
        return {
            "current_period": period,
            "base_price": result["base_price"],
            "price_after_electricity_tax": result["after_electricity_tax"],
            "electricity_tax_rate_pct": self._config[CONF_ELECTRICITY_TAX],
            "iva_rate_pct": self._config[CONF_IVA],
            "attribution": "Spanish 2.0TD tariff calculation",
        }


# ---------------------------------------------------------------------------
# Energy period sensor  (P1 / P2 / P3)
# ---------------------------------------------------------------------------


class SpainEnergyPeriodSensor(SpainEnergyBaseSensor):
    """Current 2.0TD tariff period name (P1 / P2 / P3)."""

    _attr_icon = "mdi:clock-time-four-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["P1", "P2", "P3"]

    def __init__(self, hass: HomeAssistant, entry: config_entries.ConfigEntry, config: dict) -> None:
        super().__init__(hass, entry, config, SENSOR_ENERGY_PERIOD)
        self._attr_name = "Energy Period"

    @property
    def native_value(self) -> str:
        return self._get_current_period()

    @property
    def extra_state_attributes(self) -> dict:
        elec_tax = self._config[CONF_ELECTRICITY_TAX]
        iva = self._config[CONF_IVA]
        return {
            "p1_price_with_tax": calculate_price_with_tax(
                self._config[CONF_P1_PRICE], elec_tax, iva
            )["final_price"],
            "p2_price_with_tax": calculate_price_with_tax(
                self._config[CONF_P2_PRICE], elec_tax, iva
            )["final_price"],
            "p3_price_with_tax": calculate_price_with_tax(
                self._config[CONF_P3_PRICE], elec_tax, iva
            )["final_price"],
        }


# ---------------------------------------------------------------------------
# Daily power cost sensor  (€/day including taxes)
# ---------------------------------------------------------------------------


class SpainPowerCostDailySensor(SpainEnergyBaseSensor):
    """Fixed daily contracted power cost in €/day including all taxes."""

    _attr_icon = "mdi:transmission-tower"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: config_entries.ConfigEntry, config: dict) -> None:
        super().__init__(hass, entry, config, SENSOR_POWER_COST_DAILY)
        self._attr_name = "Power Cost Daily"
        self._attr_native_unit_of_measurement = "€/day"

    @property
    def native_value(self) -> float:
        return calculate_daily_power_cost(
            self._config[CONF_P1_POWER_PRICE],
            self._config[CONF_P2_POWER_PRICE],
            self._config[CONF_P1_POWER_KW],
            self._config[CONF_P2_POWER_KW],
            self._config[CONF_ELECTRICITY_TAX],
            self._config[CONF_IVA],
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "p1_power_kw": self._config[CONF_P1_POWER_KW],
            "p2_power_kw": self._config[CONF_P2_POWER_KW],
            "p1_power_price_per_kw_day": self._config[CONF_P1_POWER_PRICE],
            "p2_power_price_per_kw_day": self._config[CONF_P2_POWER_PRICE],
            "electricity_tax_rate_pct": self._config[CONF_ELECTRICITY_TAX],
            "iva_rate_pct": self._config[CONF_IVA],
        }
