"""Driver for {{cookiecutter.driver_name}}"""

import threading
from device_base import deviceBase
from Channel import Channel, write_tag, BoolArrayChannels
from Maps import {{cookiecutter.driver_name}}_map as maps
import json
import time
import socket

_ = None

try:
    with open("persist.json", 'r') as persist_file:
        persist = json.load(persist_file)
except Exception:
    persist = {}

plc_ip_address = "192.168.1.10"


def reverse_map(value, map_):
    """Perform the opposite of mapping to an object."""
    for x in map_:
        if map_[x] == value:
            return x
    return None

def get_public_ip_address():
    """Find the public IP Address of the host device."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

channels = []


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
        print("BOOM! Starting {{cookiecutter.driver_name}} driver...")

        public_ip_address = get_public_ip_address()
        self.sendtodbDev(1, 'public_ip_address', public_ip_address, 0, '{{cookiecutter.driver_name}}')
        watchdog = self.rigpump_watchdog()
        self.sendtodbDev(1, 'watchdog', watchdog, 0, '{{cookiecutter.driver_name}}')

        send_loops = 0
        watchdog_loops = 0
        watchdog_check_after = 5000
        while True:
            if self.forceSend:
                print "FORCE SEND: TRUE"

            for c in channels:
                if c.read(self.forceSend):
                    self.sendtodbDev(1, c.mesh_name, c.value, 0, '{{cookiecutter.driver_name}}')


            # print("{{cookiecutter.driver_name}} driver still alive...")
            if self.forceSend:
                if send_loops > 2:
                    print("Turning off forceSend")
                    self.forceSend = False
                    send_loops = 0
                else:
                    send_loops += 1

            watchdog_loops += 1
            if (watchdog_loops >= watchdog_check_after):
                test_watchdog = self.rigpump_watchdog()
                if not test_watchdog == watchdog:
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
        w = write_tag(str(plc_ip_address), tag_n, val_n)
        print("Result of {{cookiecutter.driver_name}}_writeplctag(self, {}, {}) = {}".format(name, value, w))
        if w is None:
            w = "Error writing to PLC..."
        return w
