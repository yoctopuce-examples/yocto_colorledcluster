from __future__ import annotations

import logging

from yoctolib.yocto_api_aio import YAPI, YAPIContext, YRefParam
from yoctolib.yocto_colorledcluster_aio import YColorLedCluster
from yoctolib.yocto_display_aio import YDisplay, YDisplayLayer
from yoctolib.yocto_network_aio import YNetwork

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(DOMAIN)


def debugLog(line: str) -> None:
    _LOGGER.debug(line.rstrip())


class Hub:
    """Dummy hub for Hello World example."""

    manufacturer = "Yoctopuce"
    _url: str
    _hass: HomeAssistant
    leds: list[str]
    disp: list[str]
    online: bool
    hub_serial: str
    yctx: YAPIContext

    def __init__(self, hass: HomeAssistant, url: str) -> None:
        """Init dummy hub."""
        self._url = url
        self._hass = hass
        self.leds = []
        self.disp = []
        self.online = True
        self.hub_serial = ""
        self.yctx = YAPIContext()

    async def test_connection(self) -> bool:
        return await self.setupYLib()

    async def stop_connection(self) -> None:
        await self.yctx.FreeAPI()

    async def setupYLib(self) -> bool:
        _LOGGER.info("Use Yoctolib version %s" % self.yctx.GetAPIVersion())  # noqa: G002, UP031
        errmsg = YRefParam()
        _LOGGER.debug("Register hub %s", self._url)
        self.yctx.RegisterLogFunction(debugLog)
        res = await self.yctx.RegisterHub(self._url, errmsg)
        if res == YAPI.DOUBLE_ACCES:
            _LOGGER.warning("RegisterHub warning :" + errmsg.value)
        elif res != YAPI.SUCCESS:
            _LOGGER.error("RegisterHub error" + errmsg.value)
            return False
        ynet: YNetwork = YNetwork.FirstNetworkInContext(self.yctx)
        self.hub_serial = await ynet.get_serialNumber()

        l: YColorLedCluster | None = YColorLedCluster.FirstColorLedClusterInContext(
            self.yctx
        )
        while l is not None:
            hwid = await l.get_hardwareId()
            self.leds.append(hwid)
            l = l.nextColorLedCluster()

        d: YDisplay | None = YDisplay.FirstDisplayInContext(self.yctx)
        while d is not None:
            hwid = await d.get_hardwareId()
            await d.resetAll()
            self.disp.append(hwid)
            d = d.nextDisplay()
        self.online = True
        return True

    async def set_color(self, hwid: str, rgb_color) -> None:
        yled = YColorLedCluster.FindColorLedClusterInContext(self.yctx, hwid)
        if await yled.isOnline():
            nbled = await yled.get_activeLedCount()
            _LOGGER.debug("Set %s to color 0x%x" % (hwid, rgb_color))
            await yled.rgb_move(0, nbled, rgb_color, 1000)
        else:
            _LOGGER.warning("Module %s is offline" % hwid)

    async def set_hsl_color(self, hwid: str, hsl_color) -> None:
        yled = YColorLedCluster.FindColorLedClusterInContext(self.yctx, hwid)
        if await yled.isOnline():
            nbled = await yled.get_activeLedCount()
            _LOGGER.debug("Set %s to color 0x%x" % (hwid, hsl_color))
            await yled.hsl_move(0, nbled, hsl_color, 1000)
        else:
            _LOGGER.warning("Module %s is offline" % hwid)

    async def set_text(self, hwid: str, text: str) -> None:
        disp: YDisplay = YDisplay.FindDisplayInContext(self.yctx, hwid)
        if await disp.isOnline():
            # display clean up
            # retrieve the display size
            w: int = await disp.get_displayWidth()
            h: int = await disp.get_displayHeight()
            # retrieve the first layer
            l1: YDisplayLayer = await disp.get_displayLayer(1)
            await l1.clear()
            await l1.hide()
            if len(text) < 8:
                await l1.selectFont("Large.yfm")
            else:
                await l1.selectFont("Medium.yfm")
            # display a text in the middle of the screen
            _LOGGER.debug("Set %s to %s" % (hwid, text))
            await l1.drawText(w // 2, h // 2, YDisplayLayer.ALIGN.CENTER, text)
            await disp.swapLayerContent(1, 2)
        else:
            _LOGGER.warning("Module %s is offline" % hwid)

