"""Config flow for Yoctopuce ColorLedCluster Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from yoctolib.yocto_api_aio import YAPI, YAPIContext, YHub, YRefParam

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(DOMAIN)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
    }
)


async def validate_config(url: str) -> dict:
    _LOGGER.info("Use Yoctolib version %s" % YAPI.GetAPIVersion())
    yctx = YAPIContext()

    errmsg = YRefParam()
    _LOGGER.debug("Register hub %s", url)
    yres = await yctx.TestHub(url, 5000, errmsg)
    if yres != YAPI.SUCCESS:
        return {"error": errmsg.value}

    yres = await yctx.RegisterHub(url, errmsg)
    if yres != YAPI.SUCCESS:
        return {"error": errmsg.value}

    hub = YHub.FirstHubInUseInContext(yctx)
    while hub is not None:
        if await hub.get_registeredUrl() == url:
            serial = await hub.get_serialNumber()
            return {"hub": serial}
        hub = hub.nextHubInUse()
    return {"error": "No YHub matching " + url}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for yoctopuce."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                res = await validate_config(user_input[CONF_URL])
                if "error" in res:
                    errors["base"] = res["error"]
                else:
                    await self.async_set_unique_id(res["hub"])
                    # Abort the flow if a config entry with the same unique ID exists
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Hub " + res["hub"], data=user_input
                    )
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
