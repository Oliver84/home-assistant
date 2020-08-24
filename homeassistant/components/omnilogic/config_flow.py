"""Config flow for Omnilogic integration."""
import logging

from omnilogic import LoginException, OmniLogic
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

<<<<<<< HEAD
from .const import DOMAIN, POLL_INTERVAL  # pylint:disable=unused-import
=======
from .const import (
    DOMAIN,
    POLL_INTERVAL,
    DEFAULT_PUMP_SPEED,
)  # pylint:disable=unused-import
>>>>>>> 061f4c31fe4687c8bba07442a4d10c1cc81b139e

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omnilogic."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        config_entry = self.hass.config_entries.async_entries(DOMAIN)
        if config_entry:
            return self.async_abort(reason="already_setup")

        if user_input is not None:

            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                omni = OmniLogic(username, password)
                await omni.connect()
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Omnilogic", data=user_input)
            except LoginException:
                errors["base"] = "conn_err"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(POLL_INTERVAL, default=6): vol.Coerce(int),
                }
            ),
            errors=errors,
        )
