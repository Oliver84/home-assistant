"""Platform for light integration."""
import logging

from omnilogic import LightEffect, OmniLogic, OmniLogicException

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    PLATFORM_SCHEMA,
    LightEntity,
)
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# def setup_platform(hass, config, async_add_entities, discovery_info=None):
async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the OmniLogic Light platform."""
    lights = []
    _LOGGER.info("Setting up Light platform")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    # _LOGGER.info(f"COORDINATOR: {coordinator.data}")
    for backyard in coordinator.data:
        # _LOGGER.info(backyard)
        for bow in backyard["BOWS"]:
            # _LOGGER.info(bow)
            if bow.get("Lights"):
                lightId = int(bow.get("Lights")[0].get("systemId"))
                lightState = int(bow.get("Lights")[0].get("lightState"))
                lightEffect = int(bow.get("Lights")[0].get("currentShow"))
                _LOGGER.info(
                    f"Light: {lightId}, State: {lightState}, Effect: {lightEffect}"
                )
                lights += [
                    OmnilogicLight(lightId, lightState, lightEffect, backyard, bow)
                ]
    # _LOGGER.info(f"######Lights: {lights}")

    # Add devices
    # async_add_entities(OmnilogicLight(light, backyard, bow) for light, backyard, bow in lights
    async_add_entities(lights)


class OmnilogicLight(LightEntity):
    """Representation of an OmniLogic Light."""

    def __init__(self, light, state, effect, backyard, bow):
        """Initialize an OmniLogic Light."""
        self._light = light
        self._backyard = backyard
        self._backyardName = backyard["BackyardName"]
        self._bow = bow
        self._name = bow["Name"]
        self._state = state
        self._effect = effect
        self._brightness = None
        self._id = int(light)

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

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

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        # self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self._light.turn_on()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._light.turn_off()

    # def update(self):
    #     """Fetch new state data for this light.
    #     This is the only method that should fetch new data for Home Assistant.
    #     """
    #     self._light.update()
    #     self._state = self._light.is_on()
    #     self._brightness = self._light.brightness

    # async def async_turn_on(self, status):
    #     """Set the switch status."""

    #     try:
    #         omni = OmniLogic(username, password)
    #         await omni.connect()
    #         _LOGGER.info("#####TURNING ON LIGHT")
    #         success = await omni.set_relay_valve(40051, 1, self._id, 1)
    #     except OmniLogicException as error:
    #         _LOGGER.error("Setting status to %s: %r", self.name, error)
