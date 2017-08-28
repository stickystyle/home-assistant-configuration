"""Tracking for Sleep Cycle devices."""
import logging
import time

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_point_in_utc_time
from homeassistant.components.device_tracker import (
    YAML_DEVICES, CONF_TRACK_NEW, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
    load_config, PLATFORM_SCHEMA, DEFAULT_TRACK_NEW)
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['zeroconf==0.19.0']

SS_PREFIX = 'SS_'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_TRACK_NEW): cv.boolean
})


class SleepCycleHosts(object):
   
    def __init__(self):
        self.found_services = set()

    def add_service(self, zc, type_, name):
        name = name.split('.')[0]
        self.found_services.add(name)

    def remove_service(self, zc, type_, name):
        pass

    @classmethod
    def find(cls, timeout=2):
        import zeroconf
        # Monkey patch to deal with underscore in service name
        zeroconf.service_type_name = lambda type_: u'_sleepcycle_ald._tcp.local.'
        
        local_zc = zeroconf.Zeroconf(interfaces=zeroconf.InterfaceChoice.All)
        listener = cls()
        browser = zeroconf.ServiceBrowser(
            local_zc, '_sleepcycle_ald._tcp.local.', listener=listener)

        # wait for responses
        time.sleep(timeout)

        # close down anything we opened
        local_zc.close()

        return tuple(sorted(listener.found_services))


def setup_scanner(hass, config, see, discovery_info=None):
    """Setup the Sleep Cycle Scanner."""
    # pylint: disable=import-error
    

    def see_device(device):
        """Mark a device as seen."""
        see(mac=SS_PREFIX
         + device[0], host_name=device[1])

    def discover_devices():
        """Discover bluetooth devices."""
        result = SleepCycleHosts.find()
        _LOGGER.debug("Sleep Cycle discovered = " + str(len(result)))
        return list(result)

    yaml_path = hass.config.path(YAML_DEVICES)
    devs_to_track = []
    devs_donot_track = []

    # Load all known devices.
    # We just need the devices so set consider_home and home range
    # to 0
    for device in load_config(yaml_path, hass, 0):
        # check if device is a valid bluetooth device
        if device.mac and device.mac[:3].upper() == SS_PREFIX:
            if device.track:
                devs_to_track.append(device.mac[3:])
            else:
                devs_donot_track.append(device.mac[3:])

    # if track new devices is true discover new devices on startup.
    track_new = config.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)
    if track_new:
        for dev in discover_devices():
            if dev[0] not in devs_to_track and \
               dev[0] not in devs_donot_track:
                devs_to_track.append(dev[0])
                see_device(dev)

    interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    def update_sleepcycle(now):
        """Look for Sleep Cycle hosts and update status."""
        if track_new:
            for dev in discover_devices():
                if dev[0] not in devs_to_track and \
                   dev[0] not in devs_donot_track:
                    devs_to_track.append(dev[0])
        for mac in devs_to_track:
            _LOGGER.debug("Scanning " + mac)
            result = bluetooth.lookup_name(mac, timeout=5)
            if not result:
                # Could not lookup device name
                continue
            see_device((mac, result))

        track_point_in_utc_time(
            hass, update_bluetooth, dt_util.utcnow() + interval)

    update_sleepcycle(dt_util.utcnow())

    return True