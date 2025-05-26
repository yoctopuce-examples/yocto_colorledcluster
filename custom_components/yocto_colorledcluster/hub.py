from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from yoctolib.yocto_api_aio import YAPI, YRefParam
from yoctolib.yocto_colorledcluster_aio import YColorLedCluster

_LOGGER = logging.getLogger(DOMAIN)


class Hub:
    """Dummy hub for Hello World example."""

    manufacturer = "Yoctopuce"

    def __init__(self, hass: HomeAssistant, url: str) -> None:
        """Init dummy hub."""
        self._url = url
        self._hass = hass
        self.leds = []
        self.online = True

    async def test_connection(self) -> bool:
        return await self.setupYLib()

    async def setupYLib(self) -> bool:
        _LOGGER.info("Use Yoctolib version %s" % YAPI.GetAPIVersion())
        errmsg = YRefParam()
        _LOGGER.debug("Register hub %s", self._url)

        res = await YAPI.RegisterHub(self._url, errmsg)
        if res == YAPI.DOUBLE_ACCES:
            _LOGGER.warning("RegisterHub warning :" + errmsg.value)
        elif res != YAPI.SUCCESS:
            _LOGGER.error("RegisterHub error" + errmsg.value)
            return False
        l: YColorLedCluster | None = YColorLedCluster.FirstColorLedCluster()
        while l is not None:
            hwid = await l.get_hardwareId()
            self.leds.append(hwid)
            l = l.nextColorLedCluster()
        self.online = True
        return True

    async def set_color(self, hwid: str, rgb_color) -> None:
        yled = YColorLedCluster.FindColorLedCluster(hwid)
        if await yled.isOnline():
            nbled = await yled.get_activeLedCount()
            _LOGGER.debug("Set %s to color 0x%x" % (hwid, rgb_color))
            await yled.rgb_move(0, nbled, rgb_color, 1000)
        else:
            _LOGGER.warning("Module %s not offline" % hwid)

    async def set_hsl_color(self, hwid: str, hsl_color) -> None:
        yled = YColorLedCluster.FindColorLedCluster(hwid)
        if await yled.isOnline():
            nbled = await yled.get_activeLedCount()
            _LOGGER.debug("Set %s to color 0x%x" % (hwid, hsl_color))
            await yled.hsl_move(0, nbled, hsl_color, 1000)
        else:
            _LOGGER.warning("Module %s not offline" % hwid)
