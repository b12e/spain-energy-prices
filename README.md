# Spain Energy Prices

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that calculates the real cost of electricity in Spain under the **2.0TD tariff**, including all applicable taxes.

Enter your base energy prices from your electricity contract, and the integration creates sensors showing the actual price you pay at any moment — automatically switching between P1, P2, and P3 periods.

---

## Sensors

| Entity | Unit | Description |
|---|---|---|
| `sensor.spain_energy_cost` | €/kWh | Current energy price including all taxes |
| `sensor.spain_energy_period` | — | Current tariff period: P1, P2, or P3 |
| `sensor.spain_power_cost_daily` | €/day | Fixed daily contracted power cost including all taxes |

### Sensor attributes

**`sensor.spain_energy_cost`** includes:
- `current_period` — active period (P1/P2/P3)
- `base_price` — your contract price before taxes
- `price_after_electricity_tax` — price after Impuesto Eléctrico
- `electricity_tax_rate_pct` / `iva_rate_pct` — configured tax rates

**`sensor.spain_energy_period`** includes all three taxed prices as attributes (`p1_price_with_tax`, `p2_price_with_tax`, `p3_price_with_tax`), making it easy to drive automations or display cards.

---

## 2.0TD Period Schedule

| Period | Hours | Days |
|---|---|---|
| **P1** (Peak) | 10:00–14:00, 18:00–22:00 | Mon–Fri (non-holiday) |
| **P2** (Standard) | 08:00–10:00, 14:00–18:00, 22:00–00:00 | Mon–Fri (non-holiday) |
| **P3** (Off-peak) | 00:00–08:00 | Mon–Fri (non-holiday) |
| **P3** (Off-peak) | All day | Weekends & public holidays |

> Public holidays include Spanish national holidays and **Valencian Community** regional holidays. The integration assumes Home Assistant is configured with `homeassistant: time_zone: Europe/Madrid`.

Period transitions happen within 1 second of the boundary time.

---

## Tax Formula

```
final_price = base_price × (1 + electricity_tax / 100) × (1 + IVA / 100)
```

Default tax rates (configurable):
- **Impuesto Eléctrico**: 5.11%
- **IVA**: 21%

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/b12e/spain-energy-prices` with category **Integration**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/spain_energy_prices/` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Spain Energy Prices**
3. Fill in your tariff prices (all prices are **before taxes**):

| Field | Description |
|---|---|
| P1 Energy Price (€/kWh) | Your peak rate from the contract |
| P2 Energy Price (€/kWh) | Your standard rate |
| P3 Energy Price (€/kWh) | Your off-peak rate |
| P1 Contracted Power Price (€/kW/day) | Power term rate for P1 |
| P2 Contracted Power Price (€/kW/day) | Power term rate for P2 |
| P1 Contracted Power (kW) | Your contracted kW for P1 |
| P2 Contracted Power (kW) | Your contracted kW for P2 |
| Electricity Tax (%) | Impuesto Eléctrico, default 5.11% |
| IVA (%) | VAT, default 21% |

To update prices later: **Settings → Devices & Services → Spain Energy Prices → Configure**.

---

## Where to find your prices

Your base prices (before taxes) are on your electricity bill or contract:
- **Término de energía** — energy prices for P1/P2/P3
- **Término de potencia** — power prices for P1/P2 (€/kW/day)
- **Potencia contratada** — contracted power in kW for P1/P2

---

## Requirements

- Home Assistant 2024.1.0 or newer
- Python package `holidays>=0.46` (installed automatically)
