"""Utility functions for the driver."""
import socket


def get_public_ip_address():
    """Find the public IP Address of the host device."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
