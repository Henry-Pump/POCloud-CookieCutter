"""Holds map values for {{cookiecutter.driver_name}}."""

{{cookiecutter.driver_name}}_map = {}

def reverse_map(value, map_):
    """Perform the opposite of mapping to an object."""
    for x in map_:
        if map_[x] == value:
            return x
    return None
