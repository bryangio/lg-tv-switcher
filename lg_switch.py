#!/usr/bin/env python3
"""Switch LG TV input via WebSocket SSAP protocol."""

import json
import os
import sys
import ssl
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
DEFAULT_INPUT = "HDMI_2"
TIMEOUT = 5
PAIRING_TIMEOUT = 60

REGISTRATION_PAYLOAD = {
    "type": "register",
    "id": "register_0",
    "payload": {
        "forcePairing": False,
        "pairingType": "PROMPT",
        "manifest": {
            "manifestVersion": 1,
            "appVersion": "1.1",
            "signed": {
                "created": "20140509",
                "appId": "com.lge.test",
                "vendorId": "com.lge",
                "localizedAppNames": {
                    "": "LG Remote App",
                    "ko-KR": "\ub9ac\ubaa8\ucee8 \uc571",
                    "zxx-XX": "\u041b\u0413 R\u044d\u043c\u043et\u044d A\u041f\u041f"
                },
                "localizedVendorNames": {
                    "": "LG Electronics"
                },
                "permissions": [
                    "TEST_SECURE",
                    "CONTROL_INPUT_TEXT",
                    "CONTROL_MOUSE_AND_KEYBOARD",
                    "READ_INSTALLED_APPS",
                    "READ_LGE_SDX",
                    "READ_NOTIFICATIONS",
                    "SEARCH",
                    "WRITE_SETTINGS",
                    "WRITE_NOTIFICATION_ALERT",
                    "CONTROL_POWER",
                    "READ_CURRENT_CHANNEL",
                    "READ_RUNNING_APPS",
                    "READ_UPDATE_INFO",
                    "UPDATE_FROM_REMOTE_APP",
                    "READ_LGE_TV_INPUT_EVENTS",
                    "READ_TV_CURRENT_TIME"
                ],
                "serial": "2f930e2d2cfe083771f68e4fe7bb07"
            },
            "permissions": [
                "LAUNCH",
                "LAUNCH_WEBAPP",
                "APP_TO_APP",
                "CLOSE",
                "TEST_OPEN",
                "TEST_PROTECTED",
                "CONTROL_AUDIO",
                "CONTROL_DISPLAY",
                "CONTROL_INPUT_JOYSTICK",
                "CONTROL_INPUT_MEDIA_RECORDING",
                "CONTROL_INPUT_MEDIA_PLAYBACK",
                "CONTROL_INPUT_TV",
                "CONTROL_POWER",
                "READ_APP_STATUS",
                "READ_CURRENT_CHANNEL",
                "READ_INPUT_DEVICE_LIST",
                "READ_NETWORK_STATE",
                "READ_RUNNING_APPS",
                "READ_TV_CHANNEL_LIST",
                "WRITE_NOTIFICATION_TOAST",
                "READ_POWER_STATE",
                "READ_COUNTRY_INFO"
            ],
            "signatures": [
                {
                    "signatureVersion": 1,
                    "signature": "eyJhbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwia2V5SWQiOiJ0ZXN0LXNpZ25pbmctY2VydCIsInNpZ25hdHVyZVZlcnNpb24iOjF9.hrVRgjCwXVvE2OOSpDZ58hR+59aFNwYDyjQgKk3auukd7pcegmE2CzPCa0bJ0ZsRAcKkCTJrWo5iDzNhMBWRyaMOv5zWSrthlf7G128qvIlpMT0YNY+n/FaOHE73uLrS/g7swl3/qH/BGFG2Hu4RlL48eb3lLKqTt2xKHdCs6Cd4RMfJPYnzgvI4BNrFUKsjkcu+WD4OO2A27Pq1n50cMchmcaXadJhGrOqH5YmHdOCj5NSHzJYrsW0HPlpuAx/ECMeIZYDh6RMqaFM2DXzdKX9NmmyqzJ3o/0lkk/N97gfVRLW5hA29yeAwaCViZNCP8iC9aO0q9fQojoa7NQnAtw=="
                }
            ]
        }
    }
}


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def connect_to_tv(tv_ip, timeout=TIMEOUT):
    """Connect via WebSocket. Try wss://3001 first, fall back to ws://3000."""
    import websocket

    # Try secure connection first (newer webOS)
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        ws = websocket.create_connection(
            f"wss://{tv_ip}:3001",
            timeout=timeout,
            sslopt={"context": ssl_context},
            suppress_origin=True
        )
        return ws
    except Exception:
        pass

    # Fall back to plain WebSocket (older webOS)
    try:
        ws = websocket.create_connection(
            f"ws://{tv_ip}:3000",
            timeout=timeout,
            suppress_origin=True
        )
        return ws
    except Exception as e:
        raise ConnectionError(
            f"Cannot reach TV at {tv_ip}. Is it powered on and on the same network?"
        ) from e


def register(ws, client_key=None, timeout=TIMEOUT):
    """Send registration handshake, return client_key."""
    reg = json.loads(json.dumps(REGISTRATION_PAYLOAD))
    if client_key:
        reg["payload"]["client-key"] = client_key

    ws.send(json.dumps(reg))

    ws.settimeout(timeout)
    new_key = client_key

    for _ in range(20):
        try:
            resp = json.loads(ws.recv())
        except Exception:
            break

        if resp.get("id") == "register_0":
            payload = resp.get("payload", {})
            if "client-key" in payload:
                new_key = payload["client-key"]
            if resp.get("type") == "registered":
                return new_key

    if new_key and new_key != client_key:
        return new_key

    raise RuntimeError("Registration failed. Try running setup again.")


def switch_input(ws, input_id):
    """Send switchInput SSAP command."""
    msg = {
        "type": "request",
        "id": "switch_1",
        "uri": "ssap://tv/switchInput",
        "payload": {"inputId": input_id}
    }
    ws.send(json.dumps(msg))

    resp = json.loads(ws.recv())
    payload = resp.get("payload", {})
    if not payload.get("returnValue"):
        raise RuntimeError(f"Switch failed: {json.dumps(payload)}")


def run_setup(ip=None):
    """Interactive first-time setup: get TV IP, pair, save config."""
    if not ip:
        ip = input("Enter your LG TV IP address: ").strip()
    if not ip:
        print("No IP address provided.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to TV at {ip}...")
    ws = connect_to_tv(ip, timeout=PAIRING_TIMEOUT)

    print("Please accept the connection request on your TV...")
    client_key = register(ws, timeout=PAIRING_TIMEOUT)
    ws.close()

    save_config({"tv_ip": ip, "client_key": client_key})
    print("Paired successfully! Config saved.")
    print(f"Run 'python3 \"{os.path.abspath(__file__)}\"' to switch to {DEFAULT_INPUT}.")


def run_switch(input_id):
    """Normal operation: connect, register with saved key, switch input."""
    try:
        config = load_config()
    except FileNotFoundError:
        print("Not configured. Run: python3 lg_switch.py --setup", file=sys.stderr)
        sys.exit(1)

    tv_ip = config["tv_ip"]
    client_key = config.get("client_key")

    ws = connect_to_tv(tv_ip)
    new_key = register(ws, client_key=client_key)

    if new_key != client_key:
        config["client_key"] = new_key
        save_config(config)

    switch_input(ws, input_id)
    ws.close()
    print(f"Switched to {input_id}")


def main():
    parser = argparse.ArgumentParser(description="Switch LG TV input")
    parser.add_argument("--setup", action="store_true",
                        help="First-time setup: enter TV IP and pair")
    parser.add_argument("--ip", type=str,
                        help="TV IP address (for setup)")
    parser.add_argument("--input", type=str, default=DEFAULT_INPUT,
                        help=f"Input to switch to (default: {DEFAULT_INPUT})")
    args = parser.parse_args()

    if args.setup:
        run_setup(args.ip)
    else:
        run_switch(args.input)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
