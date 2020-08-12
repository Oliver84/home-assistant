"""Platform for light integration."""
import logging

from omnilogic import LightEffect, OmniLogic, OmniLogicException
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    SUPPORT_EFFECT,
    PLATFORM_SCHEMA,
    LightEntity,
)
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, entry: ConfigEntry, async_add_entities, discovery_info=None
):
    """Set up the OmniLogic Light platform."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    lights = []
    _LOGGER.info("Setting up Light platform")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"COORDINATOR: {coordinator.data}")
    for backyard in coordinator.data:
        systemId = backyard.get("systemId")
        for bow in backyard["BOWS"]:
            if bow.get("Lights"):
                lightId = int(bow.get("Lights")[0].get("systemId"))
                lightState = int(bow.get("Lights")[0].get("lightState"))
                lightEffect = int(bow.get("Lights")[0].get("currentShow"))
                lightName = bow.get("Lights")[0].get("Name")
                _LOGGER.info(
                    f"Light: {lightId}, State: {lightState}, Effect: {lightEffect}"
                )
                lights += [
                    OmnilogicLight(
                        coordinator,
                        systemId,
                        lightId,
                        lightState,
                        lightEffect,
                        lightName,
                        backyard,
                        bow,
                        username,
                        password,
                    )
                ]

    # Add devices
    # async_add_entities(OmnilogicLight(light, backyard, bow) for light, backyard, bow in lights
    async_add_entities(lights)


class OmnilogicLight(LightEntity):
    """Representation of an OmniLogic Light."""

    def __init__(
        self,
        coordinator,
        systemId,
        light,
        state,
        effect,
        lightname,
        backyard,
        bow,
        username,
        password,
    ):
        """Initialize an OmniLogic Light."""
        self._coordinator = coordinator
        self._systemid = systemId
        self._light = light
        self._backyard = backyard
        self._backyardName = backyard["BackyardName"]
        self._bow = bow
        self._name = bow["Name"]
        self._state = state
        self._effect = effect
        self._lightname = lightname
        self._brightness = None
        self._id = int(light)
        self._username = username
        self._password = password

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name + "_" + self._lightname

    # @property
    # def device_info(self):
    #     return {
    #         "identifiers": {
    #             # Serial numbers are unique identifiers within a specific domain
    #             (OmniLogic.DOMAIN, self._id)
    #         },
    #         "name": self._name,
    #         "effect": self._effect,
    #     }

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def effect(self):
        """ Return int that represents the light effect"""
        return self._effect

    @property
    def effect_list(self):
        """Return supported light effects."""
        return list(LightEffect.__members__)

    @property
    def supported_features(self) -> int:
        """Return the list of features supported by the light."""

        return SUPPORT_EFFECT

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        # self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self.async_turn_on()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self.async_turn_off()

    async def async_update(self):
        """Update Omnilogic entity."""
        await self._coordinator.async_request_refresh()

        for backyard in self._coordinator.data:
            systemId = backyard.get("systemId")
            for bow in backyard["BOWS"]:
                if bow.get("Lights"):
                    if self._id == int(bow.get("Lights")[0].get("systemId")):
                        self._state = int(bow.get("Lights")[0].get("lightState"))
                        self._effect = int(bow.get("Lights")[0].get("currentShow"))

    async def async_set_effect(self, effect):
        """Set the switch status."""

        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            # _LOGGER.info("#####CHANGING LIGHT EFFECT")
            success = await omni.set_lightshow(self._systemid, 1, self._id, effect)
            # self._state = 1
            self._effect = effect
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)

    async def async_turn_on(self, **kwargs):
        """Set the switch status."""

        effect = kwargs.get(ATTR_EFFECT)
        _LOGGER.info(f"Effect Name: {effect}")
        if effect:
            effect = LightEffect[effect].value
            if effect != self._effect:
                await self.async_set_effect(effect)
            _LOGGER.info(f"Effect Value: {effect}")

        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            # _LOGGER.info("#####TURNING ON LIGHT")
            success = await omni.set_relay_valve(
                self._systemid, 1, self._id, 1
            )  ##Need to pull pool id
            self._state = 1
            self._effect = effect
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)

    async def async_turn_off(self):
        """Set the switch status."""

        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            # _LOGGER.info("#####TURNING OFF LIGHT")
            success = await omni.set_relay_valve(self._systemid, 1, self._id, 0)
            self._state = 0
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)
