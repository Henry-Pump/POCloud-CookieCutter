"""Driver for {{cookiecutter.driver_name}}"""

import threading
import json
import time
from random import randint

from device_base import deviceBase
from channel import Channel, read_tag, write_tag
import persistence
from utilities import get_public_ip_address
from file_logger import filelogger as log

_ = None

log.info("{{cookiecutter.driver_name}} startup")

# GLOBAL VARIABLES
WAIT_FOR_CONNECTION_SECONDS = 60
IP_CHECK_PERIOD = 60
WATCHDOG_ENABLE = True
WATCHDOG_CHECK_PERIOD = 60
WATCHDOG_SEND_PERIOD = 3600  # Seconds, the longest amount of time before sending the watchdog status
PLC_IP_ADDRESS = "192.168.1.10"
CHANNELS = []

# PERSISTENCE FILE
PERSIST = persistence.load()


class start(threading.Thread, deviceBase):
    """Start class required by Meshify."""

    def __init__(self, name=None, number=None, mac=None, Q=None, mcu=None,
                 companyId=None, offset=None, mqtt=None, Nodes=None):
        """Initialize the driver."""
        threading.Thread.__init__(self)
        deviceBase.__init__(self, name=name, number=number, mac=mac, Q=Q,
                            mcu=mcu, companyId=companyId, offset=offset,
                            mqtt=mqtt, Nodes=Nodes)

        self.daemon = True
        self.version = "1"
        self.finished = threading.Event()
        self.force_send = False
        self.public_ip_address = ""
        self.public_ip_address_last_checked = 0
        self.watchdog = False
        self.watchdog_last_checked = 0
        self.watchdog_last_sent = 0
        threading.Thread.start(self)

    # this is a required function for all drivers, its goal is to upload some piece of data
    # about your device so it can be seen on the web
    def register(self):
        """Register the driver."""
        # self.sendtodb("log", "BOOM! Booted.", 0)
        pass

    def run(self):
        """Actually run the driver."""
        for i in range(0, WAIT_FOR_CONNECTION_SECONDS):
            print("{{cookiecutter.driver_name}} driver will start in {} seconds".format(WAIT_FOR_CONNECTION_SECONDS - i))
            time.sleep(1)
        log.info("BOOM! Starting {{cookiecutter.driver_name}} driver...")

        self._check_watchdog()
        self._check_ip_address()

        self.nodes["{{cookiecutter.driver_name}}_0199"] = self

        send_loops = 0

        while True:
            now = time.time()
            if self.force_send:
                log.warning("FORCE SEND: TRUE")

            for chan in CHANNELS:
                val = chan.read()
                if chan.check(val, self.force_send):
                    self.sendtodbDev(1, chan.mesh_name, chan.value, 0, '{{cookiecutter.driver_name}}')

            # print("{{cookiecutter.driver_name}} driver still alive...")
            if self.force_send:
                if send_loops > 2:
                    log.warning("Turning off force_send")
                    self.force_send = False
                    send_loops = 0
                else:
                    send_loops += 1

            if WATCHDOG_ENABLE:
                if (now - self.watchdog_last_checked) > WATCHDOG_CHECK_PERIOD:
                    self._check_watchdog()

            if (now - self.public_ip_address_last_checked) > IP_CHECK_PERIOD:
                self._check_ip_address()

    def _check_watchdog(self):
        """Check the watchdog and send to Meshify if changed or stale."""
        test_watchdog = self.{{cookiecutter.driver_name}}_watchdog()
        now = time.time()
        self.watchdog_last_checked = now
        if test_watchdog != self.watchdog or (now - self.watchdog_last_sent) > WATCHDOG_SEND_PERIOD:
            self.sendtodbDev(1, 'watchdog', test_watchdog, 0, '{{cookiecutter.driver_name}}')
            self.watchdog = test_watchdog
            self.watchdog_last_sent = now


    def _check_ip_address(self):
        """Check the public IP address and send to Meshify if changed."""
        self.public_ip_address_last_checked = time.time()
        test_public_ip = get_public_ip_address()
        if not test_public_ip == self.public_ip_address:
            self.sendtodbDev(1, 'public_ip_address', test_public_ip, 0, '{{cookiecutter.driver_name}}')
            self.public_ip_address = test_public_ip

    def {{cookiecutter.driver_name}}_watchdog(self):
        """Write a random integer to the PLC and then 1 seconds later check that it has been decremented by 1."""
        randval = randint(0, 32767)
        write_tag(str(PLC_IP_ADDRESS), 'watchdog_INT', randval)
        time.sleep(1)
        watchdog_val = read_tag(str(PLC_IP_ADDRESS), 'watchdog_INT')
        try:
            return (randval - 1) == watchdog_val[0]
        except (KeyError, TypeError):
            return False

    def {{cookiecutter.driver_name}}_sync(self, name, value):
        """Sync all data from the driver."""
        self.force_send = True
        # self.sendtodb("log", "synced", 0)
        return True

    def {{cookiecutter.driver_name}}_writeplctag(self, name, value):
        """Write a value to the PLC."""
        new_val = json.loads(str(value).replace("'", '"'))
        tag_n = str(new_val['tag'])  # "cmd_Start"
        val_n = new_val['val']
        write_res = write_tag(str(PLC_IP_ADDRESS), tag_n, val_n)
        print("Result of {{cookiecutter.driver_name}}_writeplctag(self, {}, {}) = {}".format(name, value, write_res))
        if write_res is None:
            write_res = "Error writing to PLC..."
        return write_res
