"""Define Meshify channel class."""
from pycomm.ab_comm.clx import Driver as ClxDriver
from pycomm.cip.cip_base import CommError, DataError
import time


def binarray(intval):
    """Split an integer into its bits."""
    bin_string = '{0:08b}'.format(intval)
    bin_arr = [i for i in bin_string]
    bin_arr.reverse()
    return bin_arr


def read_tag(addr, tag):
    """Read a tag from the PLC."""
    c = ClxDriver()
    try:
        if c.open(addr):
            try:
                v = c.read_tag(tag)
                return v
            except DataError:
                c.close()
                print("Data Error during readTag({}, {})".format(addr, tag))
    except CommError:
        # err = c.get_status()
        c.close()
        print("Could not connect during readTag({}, {})".format(addr, tag))
        # print err
    except AttributeError as e:
        c.close()
        print("AttributeError during readTag({}, {}): \n{}".format(addr, tag, e))
    c.close()
    return False


def read_array(addr, tag, start, end):
    """Read an array from the PLC."""
    c = ClxDriver()
    if c.open(addr):
        arr_vals = []
        try:
            for i in range(start, end):
                tag_w_index = tag + "[{}]".format(i)
                v = c.read_tag(tag_w_index)
                # print('{} - {}'.format(tag_w_index, v))
                arr_vals.append(round(v[0], 4))
            # print(v)
            if len(arr_vals) > 0:
                return arr_vals
            else:
                print("No length for {}".format(addr))
                return False
        except Exception:
            print("Error during readArray({}, {}, {}, {})".format(addr, tag, start, end))
            err = c.get_status()
            c.close()
            print err
            pass
        c.close()


def write_tag(addr, tag, val):
    """Write a tag value to the PLC."""
    c = ClxDriver()
    if c.open(addr):
        try:
            cv = c.read_tag(tag)
            wt = c.write_tag(tag, val, cv[1])
            return wt
        except Exception:
            print("Error during writeTag({}, {}, {})".format(addr, tag, val))
            err = c.get_status()
            c.close()
            print err
        c.close()


class Channel(object):
    """Holds the configuration for a Meshify channel."""

    def __init__(self, mesh_name, data_type, chg_threshold, guarantee_sec, map_=False, write_enabled=False):
        """Initialize the channel."""
        self.mesh_name = mesh_name
        self.data_type = data_type
        self.last_value = None
        self.value = None
        self.last_send_time = 0
        self.chg_threshold = chg_threshold
        self.guarantee_sec = guarantee_sec
        self.map_ = map_
        self.write_enabled = write_enabled

    def __str__(self):
        """Create a string for the channel."""
        return "{}\nvalue: {},  last_send_time: {}".format(self.mesh_name, self.value, self.last_send_time)

    def check(self, new_value, force_send=False):
        """Check to see if the new_value needs to be stored."""
        send_needed = False
        send_reason = ""
        if self.data_type == 'BOOL' or self.data_type == 'STRING':
            if self.last_send_time == 0:
                send_needed = True
                send_reason = "no send time"
            elif self.value is None:
                send_needed = True
                send_reason = "no value"
            elif not (self.value == new_value):
                if self.map_:
                    if not self.value == self.map_[new_value]:
                        send_needed = True
                        send_reason = "value change"
                else:
                    send_needed = True
                    send_reason = "value change"
            elif (time.time() - self.last_send_time) > self.guarantee_sec:
                send_needed = True
                send_reason = "guarantee sec"
            elif force_send:
                send_needed = True
                send_reason = "forced"
        else:
            if self.last_send_time == 0:
                send_needed = True
                send_reason = "no send time"
            elif self.value is None:
                send_needed = True
                send_reason = "no value"
            elif abs(self.value - new_value) > self.chg_threshold:
                send_needed = True
                send_reason = "change threshold"
            elif (time.time() - self.last_send_time) > self.guarantee_sec:
                send_needed = True
                send_reason = "guarantee sec"
            elif force_send:
                send_needed = True
                send_reason = "forced"
        if send_needed:
            self.last_value = self.value
            if self.map_:
                try:
                    self.value = self.map_[new_value]
                except KeyError:
                    print("Cannot find a map value for {} in {} for {}".format(new_value, self.map_, self.mesh_name))
                    self.value = new_value
            else:
                self.value = new_value
            self.last_send_time = time.time()
            print("Sending {} for {} - {}".format(self.value, self.mesh_name, send_reason))
        return send_needed

    def read(self):
        """Read the value."""
        pass


def identity(sent):
    """Return exactly what was sent to it."""
    return sent


class ModbusChannel(Channel):
    """Modbus channel object."""

    def __init__(self, mesh_name, register_number, data_type, chg_threshold, guarantee_sec, channel_size=1, map_=False, write_enabled=False, transformFn=identity):
        """Initialize the channel."""
        super(ModbusChannel, self).__init__(mesh_name, data_type, chg_threshold, guarantee_sec, map_, write_enabled)
        self.mesh_name = mesh_name
        self.register_number = register_number
        self.channel_size = channel_size
        self.data_type = data_type
        self.last_value = None
        self.value = None
        self.last_send_time = 0
        self.chg_threshold = chg_threshold
        self.guarantee_sec = guarantee_sec
        self.map_ = map_
        self.write_enabled = write_enabled
        self.transformFn = transformFn

    def read(self, mbsvalue):
        """Return the transformed read value."""
        return self.transformFn(mbsvalue)


class PLCChannel(Channel):
    """PLC Channel Object."""

    def __init__(self, ip, mesh_name, plc_tag, data_type, chg_threshold, guarantee_sec, map_=False, write_enabled=False):
        """Initialize the channel."""
        super(PLCChannel, self).__init__(mesh_name, data_type, chg_threshold, guarantee_sec, map_, write_enabled)
        self.plc_ip = ip
        self.mesh_name = mesh_name
        self.plc_tag = plc_tag
        self.data_type = data_type
        self.last_value = None
        self.value = None
        self.last_send_time = 0
        self.chg_threshold = chg_threshold
        self.guarantee_sec = guarantee_sec
        self.map_ = map_
        self.write_enabled = write_enabled

    def read(self):
        """Read the value."""
        plc_value = None
        if self.plc_tag and self.plc_ip:
            read_value = read_tag(self.plc_ip, self.plc_tag)
            if read_value:
                plc_value = read_value[0]

        return plc_value


class BoolArrayChannels(Channel):
    """Hold the configuration for a set of boolean array channels."""

    def __init__(self, ip, mesh_name, plc_tag, data_type, chg_threshold, guarantee_sec, map_=False, write_enabled=False):
        """Initialize the channel."""
        self.plc_ip = ip
        self.mesh_name = mesh_name
        self.plc_tag = plc_tag
        self.data_type = data_type
        self.last_value = None
        self.value = None
        self.last_send_time = 0
        self.chg_threshold = chg_threshold
        self.guarantee_sec = guarantee_sec
        self.map_ = map_
        self.write_enabled = write_enabled

    def compare_values(self, new_val_dict):
        """Compare new values to old values to see if the values need storing."""
        send = False
        for idx in new_val_dict:
            try:
                if new_val_dict[idx] != self.last_value[idx]:
                    send = True
            except KeyError:
                print("Key Error in self.compare_values for index {}".format(idx))
                send = True
        return send

    def read(self, force_send=False):
        """Read the value and check to see if needs to be stored."""
        send_needed = False
        send_reason = ""
        if self.plc_tag:
            v = read_tag(self.plc_ip, self.plc_tag)
            if v:
                bool_arr = binarray(v[0])
                new_val = {}
                for idx in self.map_:
                    try:
                        new_val[self.map_[idx]] = bool_arr[idx]
                    except KeyError:
                        print("Not able to get value for index {}".format(idx))

                if self.last_send_time == 0:
                    send_needed = True
                    send_reason = "no send time"
                elif self.value is None:
                    send_needed = True
                    send_reason = "no value"
                elif self.compare_values(new_val):
                    send_needed = True
                    send_reason = "value change"
                elif (time.time() - self.last_send_time) > self.guarantee_sec:
                    send_needed = True
                    send_reason = "guarantee sec"
                elif force_send:
                    send_needed = True
                    send_reason = "forced"

                if send_needed:
                    self.value = new_val
                    self.last_value = self.value
                    self.last_send_time = time.time()
                    print("Sending {} for {} - {}".format(self.value, self.mesh_name, send_reason))
        return send_needed
