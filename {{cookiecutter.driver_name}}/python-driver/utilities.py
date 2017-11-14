"""Utility functions for the driver."""
import socket


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

    sign = -1 ** int(bin_rep[0])
    exponent = int(bin_rep[1:6], 2)
    fraction = int(bin_rep[7:17], 2)

    return sign * 2 ** (exponent - 15) * float("1.{}".format(fraction))



def degf_to_degc(temp_f):
    """Convert deg F to deg C."""
    return (temp_f - 32.0) * (5.0/9.0)


def degc_to_degf(temp_c):
    """Convert deg C to deg F."""
    return temp_c * 1.8 + 32.0
