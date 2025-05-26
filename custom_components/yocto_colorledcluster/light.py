"""Platform for light integration."""

from __future__ import annotations

import logging
from pprint import pformat

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import HubConfigEntry
from .hub import Hub
from .const import DOMAIN
from yoctolib.yocto_api_aio import *
from yoctolib.yocto_colorledcluster_aio import *

_LOGGER = logging.getLogger(DOMAIN)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_URL): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HubConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yoctopuce Color LEDs from a config entry."""
    hub = config_entry.runtime_data

    new_devices = []
    for hwid in hub.leds:
        new_devices.append(YoctoColorLedLight(hub, hwid))
    if new_devices:
        async_add_entities(new_devices)

    return True


class YoctoColorLedLight(LightEntity):
    """Representation of an Yocto-Color-V2 Light."""

    def __init__(self, hub: Hub, hwid: str) -> None:
        self._hub = hub
        self._name = hwid
        self._is_on = False
        self._color_mode = ColorMode.HS
        self._hs_color = (0, 0)
        self._rgb_color = (0, 0, 0)
        self.unique_id = hwid
        self._brightness = 0

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._is_on

    @property
    def color_mode(self):
        return self._color_mode

    @property
    def rgb_color(self):
        return self._rgb_color

    @property
    def brightness(self):
        return self._brightness

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def supported_color_modes(self):
        return [ColorMode.HS]

    @property
    def is_on(self):
        return self._is_on

    async def set_on_off(self) -> None:
        if self._is_on:
            if self._color_mode == ColorMode.HS:
                _LOGGER.debug(self._hs_color)
                hue = int(self._hs_color[0] * 255 / 360)
                sat = int(self._hs_color[1] * 255 / 100)
                lum = int(self._brightness / 2)
                color = (hue << 16) + (sat << 8) + lum
                await self._hub.set_hsl_color(self._name, color)
                self._is_on = True
            else:
                _LOGGER.debug(self._rgb_color)

                color = (
                    (self._rgb_color[0] << 16)
                    + (self._rgb_color[1] << 8)
                    + self._rgb_color[2]
                )
                await self._hub.set_color(self._name, color)
                self._is_on = True
        else:
            await self._hub.set_color(self._name, 0)
            self._is_on = False

    def update_state_dbg(self) -> None:
        _LOGGER.info("update led status")
        if self._leds is not None and self._leds.isOnline():
            leds = self._leds.get_rgbColorArray(0, 1)
            if leds[0] != 0:
                self._is_on = True
            r = leds[0] >> 16
            g = (leds[0] >> 8) & 0xFF
            b = leds[0] & 0xFF
            self._rgb_color = (r, g, b)
            _LOGGER.info("update led status %x  to (%x %x %x)" % (leds[0], r, g, b))
        else:
            _LOGGER.warning("Module not connected (check identification and USB cable)")

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._is_on = True
        if ATTR_RGB_COLOR in kwargs:
            self._rgb_color = kwargs[ATTR_RGB_COLOR]
        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]
            _LOGGER.info(
                "Target is H=%f S=%f (l=%x)"
                % (self._hs_color[0], self._hs_color[1], self._brightness)
            )
        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.info(
                "Target is (H=%f S=%f) l=%x"
                % (self._hs_color[0], self._hs_color[1], self._brightness)
            )
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        await self.set_on_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._is_on = False
        await self.set_on_off()
