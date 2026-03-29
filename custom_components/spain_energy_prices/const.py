"""Constants for the Spain Energy Prices integration."""

DOMAIN = "spain_energy_prices"

# Config/options keys
CONF_P1_PRICE = "p1_price"
CONF_P2_PRICE = "p2_price"
CONF_P3_PRICE = "p3_price"
CONF_P1_POWER_PRICE = "p1_power_price"
CONF_P2_POWER_PRICE = "p2_power_price"
CONF_P1_POWER_KW = "p1_power_kw"
CONF_P2_POWER_KW = "p2_power_kw"
CONF_ELECTRICITY_TAX = "electricity_tax"
CONF_IVA = "iva"

# Defaults
DEFAULT_P1_PRICE = 0.0
DEFAULT_P2_PRICE = 0.0
DEFAULT_P3_PRICE = 0.0
DEFAULT_P1_POWER_PRICE = 0.0
DEFAULT_P2_POWER_PRICE = 0.0
DEFAULT_P1_POWER_KW = 0.0
DEFAULT_P2_POWER_KW = 0.0
DEFAULT_ELECTRICITY_TAX = 5.11
DEFAULT_IVA = 21.0

# Period names
PERIOD_P1 = "P1"
PERIOD_P2 = "P2"
PERIOD_P3 = "P3"

# Sensor types (used in unique_id construction)
SENSOR_ENERGY_COST = "energy_cost"
SENSOR_ENERGY_PERIOD = "energy_period"
SENSOR_POWER_COST_DAILY = "power_cost_daily"

# Platform
PLATFORM_SENSOR = "sensor"

# Update interval in seconds (safety-net polling)
UPDATE_INTERVAL_SECONDS = 60

# Period boundaries as (hour, minute) in local time.
# These are the moments when the 2.0TD period changes.
PERIOD_BOUNDARIES = [
    (0, 0),
    (8, 0),
    (10, 0),
    (14, 0),
    (18, 0),
    (22, 0),
]
