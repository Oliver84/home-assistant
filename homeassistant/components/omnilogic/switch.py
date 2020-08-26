"""Platform for switch integration."""
import logging

from omnilogic import OmniLogic, OmniLogicException
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import config_validation as cv, entity_platform

from .const import COORDINATOR, DOMAIN, OMNI_API

_LOGGER = logging.getLogger(__name__)
SERVICE_SET_SPEED = "set_pump_speed"


async def async_setup_entry(
    hass, entry: ConfigEntry, async_add_entities, discovery_info=None
):
    """Set up the OmniLogic Switch platform."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    switches = []
    _LOGGER.info("Setting up Switch platform")
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    _LOGGER.debug(f"COORDINATOR: {coordinator.data}")
    for backyard in coordinator.data:
        systemId = int(backyard.get("systemId"))
        poolId = None
        bow = None
        if len(backyard.get("Relays")) > 0:
            for switch in backyard.get("Relays"):
                switches += [
                    OmnilogicSwitch(
                        coordinator,
                        systemId,
                        poolId,
                        switch,
                        backyard,
                        bow,
                        username,
                        password,
                    )
                ]
        # if backyard.get("Pumps") and len(backyard.get("Pumps")) > 0:
        #     for switch in backyard.get("Pumps"):
        #         # switchSpeed = None
        #         # switchId = int(switch.get("systemId"))
        #         # switchState = int(switch.get("relayState"))
        #         # switchFunction = switch.get("Function")
        #         # switchName = switch.get("Name")
        #         switches += [
        #             OmnilogicSwitch(
        #                 coordinator,
        #                 systemId,
        #                 poolId,
        #                 switch,
        #                 backyard,
        #                 bow,
        #                 username,
        #                 password,
        #             )
        #         ]
        for bow in backyard["BOWS"]:
            poolId = int(bow.get("systemId"))
            if len(bow.get("Relays")) > 0:
                for switch in bow.get("Relays"):
                    switches += [
                        OmnilogicSwitch(
                            coordinator,
                            systemId,
                            poolId,
                            switch,
                            backyard,
                            bow,
                            username,
                            password,
                        )
                    ]
            if len(bow.get("Pumps")) > 0:
                for switch in bow.get("Pumps"):
                    switches += [
                        OmnilogicSwitch(
                            coordinator,
                            systemId,
                            poolId,
                            switch,
                            backyard,
                            bow,
                            username,
                            password,
                        )
                    ]
            if bow.get("Filter"):
                switches += [
                    OmnilogicSwitch(
                        coordinator,
                        systemId,
                        poolId,
                        bow.get("Filter"),
                        backyard,
                        bow,
                        username,
                        password,
                    )
                ]

    # Add devices
    async_add_entities(switches, update_before_add=True)

    # register service
    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_SET_SPEED, {vol.Required("speed"): cv.positive_int}, "async_set_speed",
    )


class OmnilogicSwitch(SwitchEntity):
    """Representation of an OmniLogic Switch."""

    def __init__(
        self, coordinator, systemId, poolId, switch, backyard, bow, username, password,
    ):
        """Initialize an OmniLogic Switch."""
        self._coordinator = coordinator
        self._systemid = systemId
        if poolId is not None:
            self._poolid = poolId
        else:
            self._poolid = 0
        self._switch = switch
        self._backyard = backyard
        self._backyardName = backyard["BackyardName"]
        self._bow = bow
        if self._bow:
            self._name = bow["Name"]
        else:
            self._name = ""
        self._username = username
        self._password = password
        self._lastSpeed = None
        self._switchId = int(switch.get("systemId"))
        self._switchName = switch.get("Name")
        self._switchState = None
        self._maxSpeed = None
        self._minSpeed = None
        self._switchFunction = None

    @property
    def name(self):
        """Return the display name of this switch."""

        return self._backyardName + " " + self._name + " " + self._switchName

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""

        return (
            self._backyardName
            + "_"
            + self._name
            + "_"
            + self._switchName
            + "_"
            + str(self._switchId)
        )

    @property
    def device_info(self):
        """Define the device as back yard/MSP System."""
        return {
            "identifiers": {(DOMAIN, self._backyard["systemId"])},
            "name": self._backyard.get("BackyardName"),
            "manufacturer": "Hayward",
            "model": "OmniLogic",
        }

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self._switchState == 7:
            return 0
        return self._switchState

    async def async_update(self):
        """Update Omnilogic entity."""
        await self._coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of switches.")
        for backyard in self._coordinator.data:
            if self._systemid == int(backyard.get("systemId")):
                if len(backyard.get("Relays")) > 0:
                    for switch in backyard.get("Relays"):
                        if int(switch.get("systemId")) == self._switchId:
                            self._switchSpeed = None
                            self._switchState = int(switch.get("relayState"))
                            self._switchFunction = switch.get("Type")
                            _LOGGER.debug(
                                f"Backyard Speed: {self._switchSpeed} State: {self._switchState} Function: {self._switchFunction}"
                            )

                for bow in backyard["BOWS"]:
                    # poolId = bow.get("systemId")
                    if len(bow.get("Relays")) > 0:
                        for switch in bow.get("Relays"):
                            if int(switch.get("systemId")) == self._switchId:
                                self._switchSpeed = None
                                self._switchState = int(switch.get("relayState"))
                                self._switchFunction = switch.get("Type")
                                _LOGGER.debug(
                                    f"Speed: {self._switchSpeed} State: {self._switchState} Function: {self._switchFunction}"
                                )

                    if len(bow.get("Pumps")) > 0:
                        for switch in bow.get("Pumps"):
                            id = switch.get("systemId")
                            _LOGGER.debug(f"##### Pump: {switch} ID: {id}")
                            if int(switch.get("systemId")) == self._switchId:
                                self._switchSpeed = None
                                self._switchState = int(switch.get("pumpState"))
                                self._switchFunction = switch.get("Type")
                                _LOGGER.debug(
                                    f"Speed: {self._switchSpeed} State: {self._switchState} Function: {self._switchFunction}"
                                )

                    if (
                        bow.get("Filter")
                        and int(bow.get("Filter").get("systemId")) == self._switchId
                    ):
                        self._switchSpeed = int(bow.get("Filter").get("filterSpeed"))
                        self._switchFunction = bow.get("Filter").get("Filter-Type")
                        self._switchState = int(bow.get("Filter").get("filterState"))
                        self._maxSpeed = int(bow.get("Filter").get("Max-Pump-Speed"))
                        self._minSpeed = int(bow.get("Filter").get("Min-Pump-Speed"))
                        _LOGGER.debug(
                            f"Speed: {self._switchSpeed} State: {self._switchState} Function: {self._switchFunction}"
                        )

    async def async_turn_on(self, **kwargs):
        """Set the switch status."""
        _LOGGER.debug(f"FUNCTION: {self._switchFunction}")
        if "RLY" in self._switchFunction:
            onValue = 1
        elif "PMP_SINGLE_SPEED" in self._switchFunction or not self._lastSpeed:
            onValue = 100
        elif self._lastSpeed:
            onValue = self._lastSpeed
        else:
            onValue = 100

        _LOGGER.debug(f"{self._systemid} {self._poolid} {self._switchId} {onValue}")
        try:
            omni = OmniLogic(self._username, self._password)
            # await omni.connect()
            await omni.set_relay_valve(
                self._systemid, self._poolid, self._switchId, onValue
            )
            self._state = 1
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)

    async def async_turn_off(self):
        """Set the switch status."""
        _LOGGER.debug(f"Current speed: {self._switchSpeed}")
        if self._switchSpeed:
            self._lastSpeed = self._switchSpeed
        try:
            omni = OmniLogic(self._username, self._password)
            # await omni.connect()
            await omni.set_relay_valve(self._systemid, self._poolid, self._switchId, 0)
            self._state = 0
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)

    async def async_set_speed(self, speed):
        """Set the switch speed."""
        _LOGGER.debug(f"FUNCTION: {self._switchFunction}")
        if "VARIABLE" in self._switchFunction:
            if speed >= self._minSpeed and speed <= self._maxSpeed:
                onValue = speed
            else:
                raise OmniLogicException("Cannot set speed. Speed is outside pump.")
        else:
            raise OmniLogicException("Cannot set speed on non-VSP pump.")
        # elif "RLY" in self._switchFunction:
        #     onValue = 1
        # elif "PMP_SINGLE_SPEED" in self._switchFunction:
        #     onValue = 100
        # elif self._lastSpeed:
        #     onValue = self._lastSpeed
        # else:
        #     onValue = 85

        _LOGGER.debug(f"{self._systemid} {self._poolid} {self._switchId} {onValue}")
        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            await omni.set_relay_valve(
                self._systemid, self._poolid, self._switchId, onValue
            )
            self._state = 1
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)
