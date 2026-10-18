#!/usr/bin/python3
"""Manage monitor layouts and hot-plug profiles for TIDALOS."""
import re
import shutil
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def command_output(command):
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"{command[0]} exited with status {result.returncode}")
    return result.stdout


def connected_displays():
    output = command_output(["xrandr", "--query"])
    displays = []
    for line in output.splitlines():
        match = re.match(r"^(\S+) connected(?: primary)?(?: (\d+x\d+\+\d+\+\d+))?", line)
        if match:
            name, mode = match.groups()
            displays.append((name, mode or "verbunden"))
    return displays


class DisplayManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="TIDALOS Monitore")
        self.set_default_size(560, 420)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("preferences-desktop-display")
        self.set_border_width(20)
        self._build()
        self.refresh()

    def _build(self):
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(layout)
        heading = Gtk.Label(label="Mehrere Bildschirme einrichten", xalign=0)
        heading.get_style_context().add_class("title-2")
        layout.pack_start(heading, False, False, 0)
        layout.pack_start(Gtk.Label(
            label="Monitore anordnen und ein Profil speichern. TIDALOS kann das passende Profil beim Anmelden und nach dem Anstecken eines Displays automatisch wiederherstellen.",
            xalign=0,
            wrap=True,
        ), False, False, 0)
        self.display_list = Gtk.ListBox()
        self.display_list.set_selection_mode(Gtk.SelectionMode.NONE)
        layout.pack_start(self.display_list, False, False, 0)
        actions = Gtk.Grid(column_spacing=8, row_spacing=8)
        layout.pack_start(actions, False, False, 0)
        for index, (title, callback) in enumerate([
            ("Cinnamon-Anzeigeeinstellungen", self.open_cinnamon),
            ("Monitore anordnen", self.open_arandr),
            ("Angezeigte Monitore aktualisieren", self.refresh),
            ("Aktuelles Layout als Profil speichern", self.save_profile),
            ("Passendes Profil anwenden", self.apply_profile),
        ]):
            button = Gtk.Button(label=title)
            button.connect("clicked", callback)
            actions.attach(button, index % 2, index // 2, 1, 1)
        self.status = Gtk.Label(label="", xalign=0, wrap=True)
        layout.pack_start(self.status, False, False, 0)
        layout.pack_end(Gtk.Label(
            label="Profile gelten pro Benutzer. Layouts werden automatisch umgeschaltet, wenn du ein Profil gespeichert hast.",
            xalign=0,
            wrap=True,
        ), False, False, 0)

    def refresh(self, _button=None):
        for row in self.display_list.get_children():
            self.display_list.remove(row)
        try:
            displays = connected_displays()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            self.status.set_text(f"Monitore konnten nicht erkannt werden: {error}")
            return False
        for name, mode in displays:
            self.display_list.add(Gtk.Label(label=f"{name} — {mode}", xalign=0, margin=6))
        self.display_list.show_all()
        if displays:
            self.status.set_text(f"{len(displays)} verbundene Anzeige(n) erkannt.")
        else:
            self.status.set_text("Kein aktiver Monitor wurde von XRandR gemeldet.")
        return True

    def launch(self, command):
        if not shutil.which(command[0]):
            self.status.set_text(f"Programm nicht installiert: {command[0]}")
            return
        try:
            subprocess.Popen(command, start_new_session=True)
        except OSError as error:
            self.status.set_text(f"Programm konnte nicht gestartet werden: {error}")

    def open_cinnamon(self, _button):
        self.launch(["cinnamon-settings", "display"])

    def open_arandr(self, _button):
        self.launch(["arandr"])

    def save_profile(self, _button):
        dialog = Gtk.Dialog(
            title="Monitorprofil speichern",
            transient_for=self,
            modal=True,
        )
        dialog.add_buttons(
            "Abbrechen", Gtk.ResponseType.CANCEL,
            "Speichern", Gtk.ResponseType.OK,
        )
        entry = Gtk.Entry(placeholder_text="z. B. schreibtisch")
        entry.set_activates_default(True)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.get_content_area().pack_start(Gtk.Label(
            label="Stelle zuerst das Layout in den Anzeigeeinstellungen oder mit Arandr ein. Danach einen Profilnamen wählen:",
            xalign=0,
            wrap=True,
            margin=12,
        ), False, False, 0)
        dialog.get_content_area().pack_start(entry, False, False, 8)
        dialog.show_all()
        response = dialog.run()
        profile = entry.get_text().strip()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", profile):
            self.status.set_text("Der Profilname darf nur Buchstaben, Zahlen, Bindestrich und Unterstrich enthalten.")
            return
        try:
            command_output(["autorandr", "--save", profile])
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            self.status.set_text(f"Monitorprofil konnte nicht gespeichert werden: {error}")
            return
        self.status.set_text(f"Profil „{profile}“ gespeichert. Autorandr stellt passende Profile beim Displaywechsel wieder her.")

    def apply_profile(self, _button):
        try:
            output = command_output(["autorandr", "--change"])
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            self.status.set_text(f"Passendes Monitorprofil konnte nicht angewendet werden: {error}")
            return
        if not self.refresh():
            return
        self.status.set_text(output.strip() or "Profilabgleich ausgeführt. Ohne passendes gespeichertes Profil ändert sich das Layout nicht.")


if __name__ == "__main__":
    window = DisplayManager()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
