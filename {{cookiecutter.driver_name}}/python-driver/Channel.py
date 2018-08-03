"""Define Meshify channel class."""
import time
from pycomm.ab_comm.clx import Driver as ClxDriver
from pycomm.cip.cip_base import CommError, DataError
from file_logger import filelogger as log



TAG_DATAERROR_SLEEPTIME = 5

def binarray(intval):
    """Split an integer into its bits."""
    bin_string = '{0:08b}'.format(intval)
    bin_arr = [i for i in bin_string]
    bin_arr.reverse()
    return bin_arr


def read_tag(addr, tag, plc_type="CLX"):
    """Read a tag from the PLC."""
    direct = plc_type == "Micro800"
    clx = ClxDriver()
    try:
        if clx.open(addr, direct_connection=direct):
            try:
                val = clx.read_tag(tag)
                return val
            except DataError as err:
                clx.close()
                time.sleep(TAG_DATAERROR_SLEEPTIME)
                log.error("Data Error during readTag({}, {}): {}".format(addr, tag, err))
    except CommError:
        # err = c.get_status()
        clx.close()
        log.error("Could not connect during readTag({}, {})".format(addr, tag))
    except AttributeError as err:
        clx.close()
        log.error("AttributeError during readTag({}, {}): \n{}".format(addr, tag, err))
    clx.close()
    return False


def read_array(addr, tag, start, end, plc_type="CLX"):
    """Read an array from the PLC."""
    direct = plc_type == "Micro800"
    clx = ClxDriver()
    if clx.open(addr, direct_connection=direct):
        arr_vals = []
        try:
            for i in range(start, end):
                tag_w_index = tag + "[{}]".format(i)
                val = clx.read_tag(tag_w_index)
                arr_vals.append(round(val[0], 4))
            if arr_vals:
                return arr_vals
            else:
                log.error("No length for {}".format(addr))
                return False
        except Exception:
            log.error("Error during readArray({}, {}, {}, {})".format(addr, tag, start, end))
            err = clx.get_status()
            clx.close()
            log.error(err)
        clx.close()


def write_tag(addr, tag, val, plc_type="CLX"):
    """Write a tag value to the PLC."""
    direct = plc_type == "Micro800"
    clx = ClxDriver()
    try:
        if clx.open(addr, direct_connection=direct):
            try:
                initial_val = clx.read_tag(tag)
                write_status = clx.write_tag(tag, val, initial_val[1])
                return write_status
            except DataError as err:
                clx_err = clx.get_status()
                clx.close()
                log.error("--\nDataError during writeTag({}, {}, {}, plc_type={}) -- {}\n{}\n".format(addr, tag, val, plc_type, err, clx_err))

    except CommError as err:
        clx_err = clx.get_status()
        log.error("--\nCommError during write_tag({}, {}, {}, plc_type={})\n{}\n--".format(addr, tag, val, plc_type, err))
        clx.close()
    return False


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
            elif self.value != new_value:
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
                    log.error("Cannot find a map value for {} in {} for {}".format(new_value, self.map_, self.mesh_name))
                    self.value = new_value
            else:
                self.value = new_value
            self.last_send_time = time.time()
            log.info("Sending {} for {} - {}".format(self.value, self.mesh_name, send_reason))
        return send_needed

    def read(self):
        """Read the value."""
        pass


def identity(sent):
    """Return exactly what was sent to it."""
    return sent


class ModbusChannel(Channel):
    """Modbus channel object."""

    def __init__(self, mesh_name, register_number, data_type, chg_threshold, guarantee_sec, channel_size=1, map_=False, write_enabled=False, transform_fn=identity):
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
        self.transform_fn = transform_fn

    def read(self, mbsvalue):
        """Return the transformed read value."""
        return self.transform_fn(mbsvalue)


class PLCChannel(Channel):
    """PLC Channel Object."""

    def __init__(self, ip, mesh_name, plc_tag, data_type, chg_threshold, guarantee_sec, map_=False, write_enabled=False, plc_type='CLX'):
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
        self.plc_type = plc_type

    def read(self):
        """Read the value."""
        plc_value = None
        if self.plc_tag and self.plc_ip:
            read_value = read_tag(self.plc_ip, self.plc_tag, plc_type=self.plc_type)
            if read_value:
                plc_value = read_value[0]

        return plc_value


class BoolArrayChannels(Channel):
    """Hold the configuration for a set of boolean array channels."""

    def __init__(self, ip, mesh_name, plc_tag, data_type, chg_threshold, guarantee_sec, map_=False, write_enabled=False):
        """Initialize the channel."""
        super(BoolArrayChannels, self).__init__(mesh_name, data_type, chg_threshold, guarantee_sec, map_, write_enabled)
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
                log.error("Key Error in self.compare_values for index {}".format(idx))
                send = True
        return send

    def read(self, force_send=False):
        """Read the value and check to see if needs to be stored."""
        send_needed = False
        send_reason = ""
        if self.plc_tag:
            val = read_tag(self.plc_ip, self.plc_tag)
            if val:
                bool_arr = binarray(val[0])
                new_val = {}
                for idx in self.map_:
                    try:
                        new_val[self.map_[idx]] = bool_arr[idx]
                    except KeyError:
                        log.error("Not able to get value for index {}".format(idx))

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
                    log.info("Sending {} for {} - {}".format(self.value, self.mesh_name, send_reason))
        return send_needed
