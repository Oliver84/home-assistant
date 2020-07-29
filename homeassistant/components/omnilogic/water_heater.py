"""Support for the Omnilogic integration pool heaters."""

from datetime import timedelta
import logging

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, UNIT_PERCENTAGE
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.water_heater import WaterHeaterEntity, SUPPORT_OPERATION_MODE, STATE_OFF, STATE_ON

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS_HEATER = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE)

async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    heaters = []

    for backyard in coordinator.data:
        for bow in backyard["BOWS"]:
            heaters.append(OmnilogicHeater(coordinator, backyard, bow, bow["Heater"]["Operation"]["VirtualHeater"]))
    
    async_add_entities(heaters, update_before_add=True)

class OmnilogicHeater(WaterHeaterEntity):
    """Defines and Omnilogic Heater Entity"""

    def __init__(self, coordinator, backyard, bow, virtualheater):
        """Initialize the Heater"""

        sensorname = "omni_" + backyard["BackyardName"].replace(" ", "_") + "_" + bow["Name"].replace(" ", "_") + "_" + virtualheater["Name"].replace(" ", "_")
        self._name = virtualHeater["Name"]
        self.entity_id = ENTITY_ID_FORMAT.format(sensorname)
        self._icon = "mdi:water-boiler"
        self._support_flags = SUPPORT_FLAGS_HEATER
        self._target_temperature = None
        self._temperature_unit = TEMP_FAHRENHEIT
        self._operation_list = [STATE_ON, STATE_OFF]
        self._current_operation = None
        self._current_temperature = None
        self._max_temp = virtualheater["Max-Settable-Water-Temp"]
        self._min_temp = virtualheater["Min-Settable-Water-Temp"]
        self.attrs = {}
        self.attrs["MspSystemId"] = backyard["systemId"]
        self.attrs["SystemId"] = virtualheater["System_Id"]
        self.coordinator = coordinator
        self.bow = bow
        self.virtualheater = virtualheater

    @property
    def should_poll(self) -> bool:
        """Return the polling requirement of the entity."""
        return True

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        # need a more unique id
        return self._name

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def target_temperature(self):
        """Return the target temperature"""
        return self._target_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measure for target temp"""
        return self._temperature_unit

    @property
    def operation_list(self):
        """Return the available operating modes"""
        return self._operation_list

    @property
    def current_operation(self):
        """Return the current operation"""
        return self._current_operation

    @property
    def current_temperature(self):
        """Return the current temperature """
        return self._current_temperature

    @property
    def max_temp(self):
        """Return the max temperature """
        return self._max_temp

    @property
    def min_temp(self):
        """Return the min temperature """
        return self._min temp

    @property
    def supported_features(self):
        """Return the supported features """
        return self._support_flags

    @property
    def icon(self):
        """Return the icon for the entity."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the attributes."""
        
        return self.attrs

    @property
    def force_update(self):
        """Force update."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Update Omnilogic entity."""
        await self.coordinator.async_request_refresh()

        temp_return = float(self.bow.get("waterTemp"))
        unit_of_measurement = TEMP_FAHRENHEIT
        if self.coordinator.data[0]["Unit-of-Measurement"] == "Metric":
            temp_return = round((temp_return - 32) * 5 / 9, 1)
            unit_of_measurement = TEMP_CELSIUS

        self.attrs["hayward_temperature"] = temp_return
        self.attrs["hayward_unit_of_measure"] = unit_of_measurement
        
        self._state = STATE_OFF
        
        if self.virtualheater.get("Enabled") == "yes":
            self._state = STATE_ON

        self._current_operation = STATE_ON

        if self.bow["Heater"].get("heaterState") == "0":
            self._current_operation = STATE_OFF

        self._current_temperature = self.bow.get("waterTemp")

        self._target_temperature = self.virtualheater.get("Current-Set-Point")
    
