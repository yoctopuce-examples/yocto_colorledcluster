"""Platform for Text integration."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Hub, HubConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HubConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yoctopuce Color LEDs from a config entry."""
    hub = config_entry.runtime_data

    new_devices = []
    for hwid in hub.disp:
        new_devices.append(YoctoDisplayText(hub, hwid))
    if new_devices:
        async_add_entities(new_devices)

    return True


class YoctoDisplayText(TextEntity):
    # Implement one of these methods.

    def __init__(self, hub: Hub, hwid: str) -> None:
        self._hub = hub
        self._name = hwid
        self.unique_id = hwid
        self.native_value = "Yoctopuce"

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        await self._hub.set_text(self._name, value)
        self.native_value = value
