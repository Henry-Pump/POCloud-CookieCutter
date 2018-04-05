"""Data persistance functions."""
# if more advanced persistence is needed, use a sqlite database
import json


def load(filename="persist.json"):
    """Load persisted settings from the specified file."""
    try:
        with open(filename, 'r') as persist_file:
            return json.load(persist_file)
    except Exception:
        return False


def store(persist_obj, filename="persist.json"):
    """Store the persisting settings into the specified file."""
    try:
        with open(filename, 'w') as persist_file:
            return json.dump(persist_obj, persist_file, indent=4)
    except Exception:
        return False
