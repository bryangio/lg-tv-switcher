# LG TV Switcher

Switch your LG WebOS TV's HDMI input from the command line. Designed for multi-computer setups where one TV serves as a shared display.

## Requirements

- Python 3
- LG WebOS TV on the same network
- macOS, Linux, or Windows

## Setup

```bash
git clone https://github.com/bryangio/lg-tv-switcher.git
cd lg-tv-switcher
bash setup.sh
```

During setup you'll be prompted to:
1. Enter your TV's IP address (find it in TV Settings > Network)
2. Accept the pairing request on your TV using the remote

This saves a `config.json` file locally with your TV's IP and pairing key.

## Usage

Switch to the default input (HDMI 2):

```bash
python3 lg_switch.py
```

Switch to a specific input:

```bash
python3 lg_switch.py --input HDMI_1
python3 lg_switch.py --input HDMI_3
```

Re-run setup (new TV IP or re-pair):

```bash
python3 lg_switch.py --setup
```

## macOS Shortcut

You can create a Shortcut in the macOS Shortcuts app for one-click switching:

1. Open **Shortcuts.app**
2. Create a new Shortcut
3. Add a **Run Shell Script** action with:
   ```
   /usr/bin/python3 "/path/to/lg_switch.py" 2>&1
   ```
4. Name it "Switch TV to PC" (or whatever you like)
5. Right-click the shortcut > **Add to Dock**

You can also trigger it from Spotlight by typing the shortcut name.

## How It Works

The script communicates with LG WebOS TVs over WebSocket using the SSAP (Simple Service Access Protocol). On first run it pairs with the TV (similar to how the LG ThinQ app pairs), storing an authentication key for future use. Subsequent runs connect instantly without prompting.

- Connects via `wss://` on port 3001 (secure), with fallback to `ws://` on port 3000
- Uses the `ssap://tv/switchInput` command to change inputs
- The TV's self-signed TLS certificate is accepted automatically

## Compatibility

Tested on:
- LG OLED C5 (2025, WebOS 25)

Should work with any LG TV running WebOS (2014+). Newer models (2020+) typically require the secure WebSocket connection on port 3001.

## License

MIT
