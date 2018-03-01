"""Driver for {{cookiecutter.driver_name}}"""

import threading
import sys
from device_base import deviceBase
from Channel import Channel, read_tag, write_tag
import persistence
from random import randint
from utilities import get_public_ip_address
import json
import time
import logging

_ = None

# LOGGING SETUP
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = './{{cookiecutter.driver_name}}.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=500*1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)
logger = logging.getLogger('{{cookiecutter.driver_name}}')
logger.setLevel(logging.INFO)
logger.addHandler(my_handler)

console_out = logging.StreamHandler(sys.stdout)
console_out.setFormatter(log_formatter)
logger.addHandler(console_out)

logger.info("{{cookiecutter.driver_name}} startup")

# GLOBAL VARIABLES
WATCHDOG_SEND_PERIOD = 3600  # Seconds, the longest amount of time before sending the watchdog status
PLC_IP_ADDRESS = "192.168.1.10"
CHANNELS = []

# PERSISTENCE FILE
persist = persistence.load()


class start(threading.Thread, deviceBase):
    """Start class required by Meshify."""

    def __init__(self, name=None, number=None, mac=None, Q=None, mcu=None, companyId=None, offset=None, mqtt=None, Nodes=None):
        """Initialize the driver."""
        threading.Thread.__init__(self)
        deviceBase.__init__(self, name=name, number=number, mac=mac, Q=Q, mcu=mcu, companyId=companyId, offset=offset, mqtt=mqtt, Nodes=Nodes)

        self.daemon = True
        self.version = "1"
        self.finished = threading.Event()
        self.forceSend = False
        threading.Thread.start(self)

    # this is a required function for all drivers, its goal is to upload some piece of data
    # about your device so it can be seen on the web
    def register(self):
        """Register the driver."""
        # self.sendtodb("log", "BOOM! Booted.", 0)
        pass

    def run(self):
        """Actually run the driver."""
        global persist
        wait_sec = 60
        for i in range(0, wait_sec):
            print("{{cookiecutter.driver_name}} driver will start in {} seconds".format(wait_sec - i))
            time.sleep(1)
        logger.info("BOOM! Starting {{cookiecutter.driver_name}} driver...")

        public_ip_address = get_public_ip_address()
        self.sendtodbDev(1, 'public_ip_address', public_ip_address, 0, '{{cookiecutter.driver_name}}')
        watchdog = self.{{cookiecutter.driver_name}}_watchdog()
        self.sendtodbDev(1, 'watchdog', watchdog, 0, '{{cookiecutter.driver_name}}')
        watchdog_send_timestamp = time.time()

        send_loops = 0
        watchdog_loops = 0
        watchdog_check_after = 5000
        while True:
            if self.forceSend:
                logger.warning("FORCE SEND: TRUE")

            for c in CHANNELS:
                v = c.read()
                if c.check(self.forceSend):
                    self.sendtodbDev(1, c.mesh_name, c.value, 0, '{{cookiecutter.driver_name}}')


            # print("{{cookiecutter.driver_name}} driver still alive...")
            if self.forceSend:
                if send_loops > 2:
                    logger.warning("Turning off forceSend")
                    self.forceSend = False
                    send_loops = 0
                else:
                    send_loops += 1

            watchdog_loops += 1
            if (watchdog_loops >= watchdog_check_after):
                test_watchdog = self.{{cookiecutter.driver_name}}_watchdog()
                if not test_watchdog == watchdog or (time.time() - watchdog_send_timestamp) > WATCHDOG_SEND_PERIOD:
                    self.sendtodbDev(1, 'watchdog', test_watchdog, 0, '{{cookiecutter.driver_name}}')
                    watchdog = test_watchdog

                test_public_ip = get_public_ip_address()
                if not test_public_ip == public_ip_address:
                    self.sendtodbDev(1, 'public_ip_address', test_public_ip, 0, '{{cookiecutter.driver_name}}')
                    public_ip_address = test_public_ip
                watchdog_loops = 0

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
        self.forceSend = True
        # self.sendtodb("log", "synced", 0)
        return True

    def {{cookiecutter.driver_name}}_writeplctag(self, name, value):
        """Write a value to the PLC."""
        new_val = json.loads(str(value).replace("'", '"'))
        tag_n = str(new_val['tag'])  # "cmd_Start"
        val_n = new_val['val']
        w = write_tag(str(PLC_IP_ADDRESS), tag_n, val_n)
        print("Result of {{cookiecutter.driver_name}}_writeplctag(self, {}, {}) = {}".format(name, value, w))
        if w is None:
            w = "Error writing to PLC..."
        return w
