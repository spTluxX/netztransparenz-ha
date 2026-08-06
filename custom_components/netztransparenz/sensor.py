"""Sensor platform for Netztransparenz Marktwerte."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PRICE_SOURCE,
    CONF_PRICE_UNIT,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_PRICE_UNIT,
    DOMAIN,
    METRICS,
    UNIT_CT,
    UNIT_EUR,
)
from .coordinator import NetztransparenzCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: NetztransparenzCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        MarketValueSensor(coordinator, entry, metric) for metric in METRICS
    ]
    entities.append(PriceSensor(coordinator, entry))
    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Netztransparenz Marktwerte",
        manufacturer="\u00dcbertragungsnetzbetreiber (netztransparenz.de)",
        entry_type=DeviceEntryType.SERVICE,
    )


class MarketValueSensor(CoordinatorEntity[NetztransparenzCoordinator], SensorEntity):
    """One raw market value in ct/kWh (as published)."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UNIT_CT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: NetztransparenzCoordinator,
        entry: ConfigEntry,
        metric: str,
    ) -> None:
        super().__init__(coordinator)
        self._metric = metric
        self._attr_name = METRICS[metric]["name"]
        self._attr_icon = METRICS[metric]["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{metric}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._metric)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        period = self.coordinator.data.get("period") if self.coordinator.data else None
        return {"period": period, "source": "netztransparenz.de (marketpremium)"}


class PriceSensor(CoordinatorEntity[NetztransparenzCoordinator], SensorEntity):
    """The user-selected value, converted to the chosen unit.

    This is the entity to plug into the Energy dashboard as the import/export
    price. Which metric and unit it reflects is set in the integration options.
    """

    _attr_has_entity_name = True
    _attr_name = "Price"
    _attr_icon = "mdi:cash"
    _attr_suggested_display_precision = 5

    def __init__(
        self, coordinator: NetztransparenzCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_price"
        self._attr_device_info = _device_info(entry)

    @property
    def _source(self) -> str:
        return self._entry.options.get(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE)

    @property
    def _unit(self) -> str:
        return self._entry.options.get(CONF_PRICE_UNIT, DEFAULT_PRICE_UNIT)

    @property
    def native_unit_of_measurement(self) -> str:
        return self._unit

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        value_ct = self.coordinator.data.get(self._source)
        if value_ct is None:
            return None
        if self._unit == UNIT_EUR:
            return round(value_ct / 100.0, 5)
        return round(value_ct, 3)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {
            "price_source": METRICS.get(self._source, {}).get("name", self._source),
            "period": data.get("period"),
            "source": "netztransparenz.de (marketpremium)",
        }
