import sys
import hid
import time

VID = 0x046D
PID = 0xC54F


def open_mouse():
    info = next((x for x in hid.enumerate(VID, PID)
                 if x.get("usage_page") == 0xFF43 and x.get("usage") == 0x0302), None)
    if info is None:
        raise RuntimeError("X3 not found")
    d = hid.device()
    d.open_path(info["path"])
    d.set_nonblocking(True)
    return d


def flush(d):
    while d.read(64):
        pass


def tx(d, feature, function, params=None, timeout=1.0):
    params = params or []
    flush(d)
    data = [0x11, 0x01, feature, function] + params
    data += [0x00] * (20 - len(data))
    written = d.write(bytes(data))
    if written != 20:
        raise RuntimeError(f"HID write error: {written}")
    end = time.time() + timeout
    while time.time() < end:
        r = d.read(64)
        if not r:
            time.sleep(0.005)
            continue
        if len(r) < 4 or r[0] != 0x11 or r[1] != 0x01:
            continue
        if r[2] != feature or r[3] != function:
            continue
        return r
    raise RuntimeError(f"No matching HID++ response ({feature:02X}/{function:02X})")


def feature_index(d, feature_id):
    r = tx(d, 0x00, 0x0D, [(feature_id >> 8) & 0xFF, feature_id & 0xFF])
    if len(r) < 5 or r[4] == 0:
        raise RuntimeError(f"HID++ feature {feature_id:04X} not found")
    return r[4]


def read_profile(d, profiles):
    r = tx(d, profiles, 0x4D)
    if len(r) < 6:
        raise RuntimeError("Profile response too short")
    slot = (r[4] << 8) | r[5]
    if slot in (1, 2):
        return slot
    raise RuntimeError(f"Unexpected profile slot: {slot}")


def read_battery(d, battery_feature):
    r = tx(d, battery_feature, 0x1D)
    if len(r) < 5:
        raise RuntimeError("Battery response too short")
    percent = r[4]
    if percent > 100:
        raise RuntimeError(f"Invalid battery value: {percent}")
    return percent


def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if command not in ("status", "battery", "toggle"):
        raise RuntimeError("Command: status, battery or toggle")
    d = open_mouse()
    try:
        profiles = feature_index(d, 0x8100)
        battery_feature = feature_index(d, 0x1004)
        slot = read_profile(d, profiles)
        if command == "toggle":
            target = 2 if slot == 1 else 1
            tx(d, profiles, 0x3D, [0x00, target])
            time.sleep(0.05)
            slot = read_profile(d, profiles)
            if slot != target:
                raise RuntimeError(f"Profile switch not confirmed (wanted {target}, got {slot})")
        battery = read_battery(d, battery_feature)
        print(battery if command == "battery" else f"{slot}|{battery}")
    finally:
        d.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR|{e}")
        sys.exit(1)
