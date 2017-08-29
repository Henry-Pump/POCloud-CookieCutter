"""Driver for {{cookiecutter.driver_name}}"""

import threading
from device_base import deviceBase
from Channel import Channel, write_tag, BoolArrayChannels
from Maps import {{cookiecutter.driver_name}}_map as maps
import json
import time

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


channels = []


class start(threading.Thread, deviceBase):
    """Start class required by Meshify."""

    def __init__(self, name=None, number=None, mac=None, Q=None, mcu=None, companyId=None, offset=None, mqtt=None, Nodes=None):
        """Initialize the driver."""
        threading.Thread.__init__(self)
        deviceBase.__init__(self, name=name, number=number, mac=mac, Q=Q, mcu=mcu, companyId=companyId, offset=offset, mqtt=mqtt, Nodes=Nodes)

        self.daemon = True
        self.version = "3"
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
        # after its booted up assuming that M1 is now reading modbus data
        # we can replace the reference made to this device name to the M1 driver with this
        # driver. The 01 in the 0199 below is the device number you referenced in the modbus wizard
        self.nodes["{{cookiecutter.driver_name}}_0199"] = self
        send_loops = 0
        while True:
            if self.forceSend:
                print "FORCE SEND: TRUE"

            for c in channels:
                if c.read(self.forceSend):
                    self.sendtodb(c.mesh_name, c.value, 0)


            # print("{{cookiecutter.driver_name}} driver still alive...")
            if self.forceSend:
                if send_loops > 2:
                    print("Turning off forceSend")
                    self.forceSend = False
                    send_loops = 0
                else:
                    send_loops += 1

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
