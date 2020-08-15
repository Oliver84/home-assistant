"""Platform for light integration."""
import logging

from omnilogic import LightEffect, OmniLogic, OmniLogicException

# Import the device class from the component that you want to support
from homeassistant.components.light import ATTR_EFFECT, SUPPORT_EFFECT, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
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
            poolId = bow.get("systemId")
            if len(bow.get("Lights")) > 0:
                for light in bow.get("Lights"):
                    lights += [
                        OmnilogicLight(
                            coordinator,
                            light,
                            systemId,
                            poolId,
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
        self, coordinator, light, systemId, poolId, backyard, bow, username, password,
    ):
        """Initialize an OmniLogic Light."""
        self._coordinator = coordinator
        self._systemid = systemId
        self._poolid = poolId
        self._light = light
        self._backyard = backyard
        self._backyardName = backyard["BackyardName"]
        self._bow = bow
        self._name = bow["Name"]
        self._state = int(self._light.get("lightState"))
        self._effect = int(self._light.get("currentShow"))
        self._lightname = self._light.get("Name")
        self._lightId = int(self._light.get("systemId"))
        self._brightness = None
        self._username = username
        self._password = password

    @property
    def name(self):
        """Return the display name of this light."""

        return self._backyardName + "_" + self._name + "_" + self._lightname

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""

        return self._backyardName + "_" + self._name + "_" + self._lightname

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
        """Return int that represents the light effect."""
        return self._effect

    @property
    def effect_list(self):
        """Return supported light effects."""
        return list(LightEffect.__members__)

    @property
    def supported_features(self) -> int:
        """Return the list of features supported by the light."""

        return SUPPORT_EFFECT

    async def async_update(self):
        """Update Omnilogic entity."""
        await self._coordinator.async_request_refresh()

        for backyard in self._coordinator.data:
            if self._systemid == backyard.get("systemId"):
                for bow in backyard["BOWS"]:
                    if len(bow.get("Lights")) > 0:
                        for light in bow.get("Lights"):
                            if self._lightId == int(light.get("systemId")):
                                _LOGGER.debug(
                                    f"Updating state of light {self._lightId}"
                                )
                                self._state = int(
                                    bow.get("Lights")[0].get("lightState")
                                )
                                self._effect = int(
                                    bow.get("Lights")[0].get("currentShow")
                                )

    async def async_set_effect(self, effect):
        """Set the light show effect."""

        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            await omni.set_lightshow(
                self._systemid, self._poolid, self._lightId, effect
            )
            self._effect = effect
            await omni.close()
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
            await omni.set_relay_valve(self._systemid, self._poolid, self._lightId, 1)
            self._state = 1
            self._effect = effect
            await omni.close()
            await self._coordinator.async_request_refresh()
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)

    async def async_turn_off(self):
        """Set the switch status."""

        try:
            omni = OmniLogic(self._username, self._password)
            await omni.connect()
            await omni.set_relay_valve(self._systemid, self._poolid, self._lightId, 0)
            self._state = 0
            await omni.close()
            await self._coordinator.async_request_refresh()
        except OmniLogicException as error:
            _LOGGER.error("Setting status to %s: %r", self.name, error)
