#!/usr/bin/python3
"""Native GTK welcome application for TIDALOS."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk, Gdk

STATE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "tidalos/welcome.json"
CSS = b"""
.tidal-welcome { background: #111e29; color: #ecf5f7; }
.tidal-brand { background: linear-gradient(150deg, #205f69, #0b2736); padding: 30px; }
.tidal-eyebrow { color: #5ce0cf; font-size: 10px; letter-spacing: 2px; }
.tidal-heading { font-size: 32px; font-weight: 500; }
.tidal-muted { color: #a2b7c3; }
.tidal-action { padding: 12px 16px; border-radius: 9px; }
.tidal-foot { color: #a2b7c3; font-size: 11px; }
.tidal-status { color: #ffb4b4; }
"""


def preference():
    try:
        return json.loads(STATE.read_text(encoding="utf-8")).get("show_on_login", True)
    except (OSError, ValueError, AttributeError):
        return True


def label(text, css=None):
    widget = Gtk.Label(label=text, xalign=0)
    widget.set_line_wrap(True)
    if css:
        widget.get_style_context().add_class(css)
    return widget


class Welcome(Gtk.Application):
    def __init__(self, smoke=False, screenshot=None):
        super().__init__(application_id="org.tidalos.Welcome", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.smoke = smoke
        self.screenshot = screenshot
        self.window = None

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        window = self.window = Gtk.ApplicationWindow(application=self, title="Willkommen bei TIDALOS")
        window.set_default_size(760, 460)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.set_icon_name("tidalos")
        window.get_style_context().add_class("tidal-welcome")
        bar = Gtk.HeaderBar(title="Willkommen")
        bar.set_show_close_button(True)
        window.set_titlebar(bar)
        layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        window.add(layout)
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        brand.get_style_context().add_class("tidal-brand")
        brand.set_size_request(180, -1)
        image = Gtk.Image.new_from_icon_name("tidalos", Gtk.IconSize.DIALOG)
        image.set_pixel_size(96)
        brand.pack_start(Gtk.Label(), True, True, 0)
        brand.pack_start(image, False, False, 0)
        brand.pack_start(Gtk.Label(label="T I D A L W A V E   O S"), False, False, 0)
        brand.pack_start(Gtk.Label(), True, True, 0)
        layout.pack_start(brand, False, False, 0)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_border_width(32)
        layout.pack_start(content, True, True, 0)
        content.pack_start(label("DEIN DESKTOP. DEIN FLOW.", "tidal-eyebrow"), False, False, 0)
        content.pack_start(label("Ein frischer Start.\nEin vertrautes Gefühl.", "tidal-heading"), False, False, 0)
        content.pack_start(label("Ein ruhiger Ort für deine Ideen.\nWillkommen bei TIDALOS.", "tidal-muted"), False, False, 0)
        actions = Gtk.Grid(column_spacing=10, row_spacing=10)
        content.pack_start(actions, False, False, 0)
        for index, (title, command, primary) in enumerate([
            ("Apps installieren", ["tidalos-store"], True),
            ("Grafiktreiber", ["software-properties-gtk", "--open-tab=4"], False),
            ("Monitore einrichten", ["cinnamon-settings", "display"], False),
            ("Design anpassen", ["cinnamon-settings", "themes"], True),
            ("Dateien öffnen", ["nemo"], False),
            ("Einstellungen", ["cinnamon-settings"], False),
            ("Terminal öffnen", ["x-terminal-emulator"], False),
        ]):
            button = Gtk.Button(label=title)
            button.get_style_context().add_class("tidal-action")
            if primary:
                button.get_style_context().add_class("suggested-action")
            button.connect("clicked", self.launch, command)
            actions.attach(button, index % 2, index // 2, 1, 1)
        self.status = label("", "tidal-status")
        content.pack_start(self.status, False, False, 0)
        content.pack_start(label("0.1.0 · Live Alpha · Ubuntu 24.04 / Cinnamon", "tidal-foot"), False, False, 0)
        try:
            live = "boot=casper" in Path("/proc/cmdline").read_text()
        except OSError:
            live = False
        if live:
            content.pack_start(label("Live-Sitzung: Änderungen werden beim Neustart verworfen.", "tidal-foot"), False, False, 0)
        toggle = Gtk.CheckButton(label="Beim Anmelden anzeigen")
        toggle.set_active(bool(preference()))
        toggle.connect("toggled", self.save_preference)
        content.pack_end(toggle, False, False, 0)
        window.show_all()
        if self.smoke or self.screenshot:
            GLib.timeout_add(1000, self.finish_smoke)

    def finish_smoke(self):
        if self.screenshot:
            surface = self.window.get_window()
            image = Gdk.pixbuf_get_from_window(surface, 0, 0, surface.get_width(), surface.get_height())
            image.savev(str(self.screenshot), "png", [], [])
        print("TIDALOS_WELCOME_READY", flush=True)
        self.quit()
        return GLib.SOURCE_REMOVE

    def launch(self, _button, command):
        if not shutil.which(command[0]):
            self.status.set_text(f"Anwendung nicht installiert: {command[0]}")
            return
        try:
            subprocess.Popen(command, start_new_session=True)
            self.status.set_text("")
        except OSError as error:
            self.status.set_text(f"Start fehlgeschlagen: {error}")

    def save_preference(self, toggle):
        try:
            STATE.parent.mkdir(parents=True, exist_ok=True)
            temporary = STATE.with_suffix(".tmp")
            temporary.write_text(json.dumps({"show_on_login": toggle.get_active()}), encoding="utf-8")
            temporary.replace(STATE)
        except OSError as error:
            self.status.set_text(f"Einstellung konnte nicht gespeichert werden: {error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autostart", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    if args.autostart and not preference():
        sys.exit(0)
    sys.exit(Welcome(smoke=args.smoke_test, screenshot=args.screenshot).run([sys.argv[0]]))
