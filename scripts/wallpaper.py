#!/usr/bin/env python3
"""Apply or restore the TIDALOS wallpaper in the current Cinnamon session."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SCHEMA = "org.cinnamon.desktop.background"
KEYS = ("picture-uri", "picture-options")


def settings(*args):
    return subprocess.check_output(["gsettings", *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "restore"))
    args = parser.parse_args()
    if sys.platform != "linux" or not shutil.which("gsettings"):
        parser.error("Run inside a Linux Cinnamon desktop session with gsettings.")
    if SCHEMA not in settings("list-schemas").splitlines():
        parser.error("Cinnamon background schema is not installed.")
    for key in KEYS:
        if settings("writable", SCHEMA, key) != "true":
            parser.error(f"Setting is not writable: {key}")
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "tidalos"
    backup = state / "wallpaper-backup.json"
    if args.action == "restore":
        if not backup.is_file():
            parser.error("No saved background settings found.")
        values = json.loads(backup.read_text(encoding="utf-8"))
        if not isinstance(values, dict) or any(not isinstance(values.get(k), str) for k in KEYS):
            parser.error("Invalid wallpaper backup.")
    else:
        source = Path(__file__).resolve().parents[1] / "assets/wallpapers/tidal-depths.svg"
        if not source.is_file():
            parser.error("Wallpaper asset is missing.")
        state.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            original = {key: settings("get", SCHEMA, key) for key in KEYS}
            with backup.open("x", encoding="utf-8") as stream:
                json.dump(original, stream, indent=2)
        target = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "backgrounds/tidalos/tidal-depths.svg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        values = {"picture-uri": "'" + target.resolve().as_uri().replace("'", "%27") + "'", "picture-options": "'zoom'"}
    before = {key: settings("get", SCHEMA, key) for key in KEYS}
    try:
        for key in KEYS:
            subprocess.run(["gsettings", "set", SCHEMA, key, values[key]], check=True)
            if settings("get", SCHEMA, key) != values[key]:
                raise RuntimeError(f"Could not verify {key}; check the session D-Bus connection.")
    except (subprocess.CalledProcessError, RuntimeError):
        for key in KEYS:
            subprocess.run(["gsettings", "set", SCHEMA, key, before[key]], check=False)
        raise
    print("TIDALOS wallpaper applied." if args.action == "apply" else "Previous wallpaper restored.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as error:
        sys.exit(f"Wallpaper operation failed: {error}")
