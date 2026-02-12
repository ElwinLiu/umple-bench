from importlib import util
from pathlib import Path


DOOR_MODULE_PATH = Path("/app/Door.py")


def load_door_class():
    if not DOOR_MODULE_PATH.exists():
        raise FileNotFoundError(f"Expected {DOOR_MODULE_PATH} to exist")

    spec = util.spec_from_file_location("Door", DOOR_MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.Door


def assert_state(door, expected):
    actual = door.getSm()
    assert actual == expected, f"Expected state {expected}, got {actual}"


def main():
    Door = load_door_class()
    door = Door()

    assert_state(door, Door.Sm.Closed)

    assert door.open() is True
    assert_state(door, Door.Sm.Open)

    assert door.lock() is False
    assert_state(door, Door.Sm.Open)

    assert door.close() is True
    assert_state(door, Door.Sm.Closed)

    assert door.lock() is True
    assert_state(door, Door.Sm.Locked)

    assert door.open() is False
    assert_state(door, Door.Sm.Locked)

    assert door.unlock() is True
    assert_state(door, Door.Sm.Closed)


if __name__ == "__main__":
    main()
