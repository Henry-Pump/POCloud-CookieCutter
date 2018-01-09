"""Utility functions for the driver."""
import socket
import struct


def get_public_ip_address():
    """Find the public IP Address of the host device."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def int_to_float16(int_to_convert):
    """Convert integer into float16 representation."""
    bin_rep = ('0' * 16 + '{0:b}'.format(int_to_convert))[-16:]
    sign = 1.0
    if int(bin_rep[0]) == 1:
        sign = -1.0
    exponent = float(int(bin_rep[1:6], 2))
    if exponent == 30:
        fraction = float(int("1" + bin_rep[7:17], 2))
    else:
        fraction = float(int(bin_rep[7:17], 2))

    if exponent == float(0b00000):
        return sign * 2 ** -14 * fraction / (2.0 ** 10.0)
    elif exponent == float(0b11111):
        if fraction == 0:
            return sign * float("inf")
        else:
            return float("NaN")
    else:
        frac_part = 1.0 + fraction / (2.0 ** 10.0)
        return sign * (2 ** (exponent - 15)) * frac_part


def ints_to_float(int1, int2):
    """Convert 2 registers into a floating point number."""
    mypack = struct.pack('>HH', int1, int2)
    f = struct.unpack('>f', mypack)
    print("[{}, {}] >> {}".format(int1, int2, f[0]))
    return f[0]


def degf_to_degc(temp_f):
    """Convert deg F to deg C."""
    return (temp_f - 32.0) * (5.0/9.0)


def degc_to_degf(temp_c):
    """Convert deg C to deg F."""
    return temp_c * 1.8 + 32.0
