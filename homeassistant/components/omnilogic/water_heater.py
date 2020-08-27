"""Support for the Omnilogic integration pool heaters."""

import logging

from omnilogic import OmniLogic

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.water_heater import (
    STATE_OFF,
    STATE_ON,
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_PASSWORD,
    CONF_USERNAME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS_HEATER = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    is_metric = hass.config.units.is_metric
    heaters = []

    for backyard in coordinator.data:
        for bow in backyard["BOWS"]:
            if "Heater" in bow:
                heaters.append(
                    OmnilogicHeater(
                        coordinator,
                        backyard,
                        bow,
                        bow["Heater"]["Operation"]["VirtualHeater"],
                        username,
                        password,
                        is_metric,
                    )
                )

    async_add_entities(heaters, update_before_add=True)


class OmnilogicHeater(WaterHeaterEntity):
    """Defines and Omnilogic Heater Entity."""

    def __init__(
        self, coordinator, backyard, bow, virtualheater, username, password, is_metric
    ):
        """Initialize the Heater."""

        sensorname = (
            backyard["BackyardName"].replace(" ", "_")
            + "_"
            + bow["Name"].replace(" ", "_")
            + "_"
            + virtualheater["Name"].replace(" ", "_")
        )
        self._name = (
            backyard["BackyardName"]
            + " "
            + bow.get("Name")
            + " "
            + virtualheater.get("Name")
        )
        self.entity_id = ENTITY_ID_FORMAT.format(sensorname)
        self._icon = "mdi:water-boiler"
        self._support_flags = SUPPORT_FLAGS_HEATER
        self._target_temperature = None
        self._temperature_unit = TEMP_FAHRENHEIT
        self._operation_list = [STATE_ON, STATE_OFF]
        self._current_operation = None
        self._current_temperature = None
        self._max_temp = float(virtualheater["Max-Settable-Water-Temp"])
        self._min_temp = float(virtualheater["Min-Settable-Water-Temp"])
        self._mspsystemid = backyard["systemId"]
        self._poolid = bow["systemId"]
        self._equipmentid = virtualheater["systemId"]
        self._is_metric = is_metric
        self.attrs = {}
        self.attrs["MspSystemId"] = backyard["systemId"]
        self.attrs["PoolId"] = bow["systemId"]
        self.attrs["SystemId"] = virtualheater["systemId"]
        self.coordinator = coordinator
        self.backyard = backyard
        self.bow = bow
        self.virtualheater = virtualheater
        self.username = username
        self.password = password

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        # need a more unique id
        return self.entity_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Define the device as back yard/MSP System."""
        return {
            "identifiers": {(DOMAIN, self.backyard["systemId"])},
            "name": self.backyard.get("BackyardName"),
            "manufacturer": "Hayward",
            "model": "OmniLogic",
        }

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measure for target temp."""
        return self._temperature_unit

    @property
    def operation_list(self):
        """Return the available operating modes."""
        return self._operation_list

    @property
    def current_operation(self):
        """Return the current operation."""
        return self._current_operation

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def max_temp(self):
        """Return the max temperature."""
        return self._max_temp

    @property
    def min_temp(self):
        """Return the min temperature."""
        return self._min_temp

    @property
    def supported_features(self):
        """Return the supported features."""
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

        virtualheater = {}
        heater = {}
        this_bow = {}
        this_backyard = {}

        for backyard in self.coordinator.data:
            for bow in backyard.get("BOWS"):
                if (
                    bow["Heater"]["Operation"]["VirtualHeater"]["systemId"]
                    == self._equipmentid
                ):
                    heater = bow["Heater"]
                    virtualheater = bow["VirtualHeater"]
                    this_bow = bow
                    this_backyard = backyard

        temp_return = float(this_bow.get("waterTemp"))
        temp_check = temp_return

        unit_of_measurement = TEMP_FAHRENHEIT
        if this_backyard["Unit-of-Measurement"] == "Metric":
            temp_return = round((temp_return - 32) * 5 / 9, 1)
            unit_of_measurement = TEMP_CELSIUS

        if temp_check == -1:
            temp_return = None

        self.attrs["hayward_temperature"] = temp_return
        self.attrs["hayward_unit_of_measure"] = unit_of_measurement

        self._current_operation = STATE_OFF

        if virtualheater.get("enable") == "yes":
            self._current_operation = STATE_ON

        self._state = STATE_ON

        if heater.get("heaterState") == "0":
            self._state = STATE_OFF

        self._current_temperature = temp_return

        self._target_temperature = float(
            heater["Operation"]["VirtualHeater"]["Current-Set-Point"]
        )

    async def async_set_temperature(self, **kwargs):
        """Set the water heater temperature set-point."""
        target_temperature = kwargs.get(ATTR_TEMPERATURE)

        _LOGGER.info(f"Setting temperature to { target_temperature}")

        api_client = OmniLogic(self.username, self.password)

        _LOGGER.debug(
            f"{self._mspsystemid} {self._poolid} {self._equipmentid} {target_temperature}"
        )

        success = await api_client.set_heater_temperature(
            int(self._mspsystemid),
            int(self._poolid),
            int(self._equipmentid),
            int(target_temperature),
        )

        await api_client.close()

        _LOGGER.info(f"Temperature response: {success}")
        if success:
            self.async_schedule_update_ha_state()

    async def async_set_operation_mode(self, operation_mode):
        """Turn the heater on or off."""
        _LOGGER.info("Setting operation mode.")
        heaterEnable = True
        if operation_mode == "off":
            heaterEnable = False

        api_client = OmniLogic(self.username, self.password)

        success = await api_client.set_heater_onoff(
            int(self._mspsystemid),
            int(self._poolid),
            int(self._equipmentid),
            heaterEnable,
        )

        await api_client.close()

        if success:
            self.async_schedule_update_ha_state()
