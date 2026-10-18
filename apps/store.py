#!/usr/bin/python3
"""Search and install applications from APT, Flathub and Snap for TIDALOS."""
import json
import re
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import urllib.parse
import urllib.request

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

MAX_RESULTS_PER_SOURCE = 30
SOURCE_NAMES = ("Alle Quellen", "APT", "Flathub", "Snap", "GitHub")
CSS = b"""
.tidal-store { background: #111e29; color: #ecf5f7; }
.store-title { font-size: 25px; font-weight: 600; }
.store-muted { color: #a2b7c3; }
.store-card { padding: 12px; }
"""


def run_command(command, timeout=30):
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"{command[0]} exited with status {result.returncode}")
    return result.stdout


def search_apt(query):
    output = run_command(["apt-cache", "search", "--names-only", re.escape(query)])
    found = []
    for line in output.splitlines():
        match = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9+.-]*)\s+-\s+(.*)$", line)
        if match:
            found.append({
                "source": "APT",
                "name": match.group(1),
                "description": match.group(2),
                "install": match.group(1),
            })
        if len(found) >= MAX_RESULTS_PER_SOURCE:
            break
    return found


def search_flatpak(query):
    output = run_command([
        "flatpak", "search", "--columns=application,name,description", query
    ], timeout=45)
    found = []
    for line in output.splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            columns = [column.strip() for column in line.split("\t")]
        else:
            columns = [column.strip() for column in re.split(r"\s{2,}", line.strip(), maxsplit=2)]
        if len(columns) < 2 or columns[0].lower() in ("application id", "application"):
            continue
        app_id, name = columns[:2]
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", app_id):
            continue
        found.append({
            "source": "Flathub",
            "name": name or app_id,
            "description": columns[2] if len(columns) > 2 else "",
            "install": app_id,
        })
        if len(found) >= MAX_RESULTS_PER_SOURCE:
            break
    return found


def search_snap(query):
    output = run_command(["snap", "find", "--format=json", query], timeout=45)
    payload = json.loads(output)
    if isinstance(payload, dict):
        payload = payload.get("snaps", payload.get("results"))
    if not isinstance(payload, list):
        raise RuntimeError("Snap returned an unexpected search response.")
    return [{
        "source": "Snap",
        "name": item["name"],
        "description": item.get("summary") or item.get("description") or "",
        "install": item["name"],
    } for item in payload[:MAX_RESULTS_PER_SOURCE] if isinstance(item, dict) and item.get("name")]


def search_github(query):
    parameters = urllib.parse.urlencode({"q": query, "per_page": MAX_RESULTS_PER_SOURCE, "sort": "stars"})
    request = urllib.request.Request(
        f"https://api.github.com/search/repositories?{parameters}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TIDALOS-App-Store",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub search returned HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"GitHub search failed: {error.reason}") from error
    items = payload.get("items")
    if not isinstance(items, list):
        raise RuntimeError("GitHub returned an unexpected search response.")
    found = []
    for item in items[:MAX_RESULTS_PER_SOURCE]:
        url = item.get("html_url", "")
        if not url.startswith("https://github.com/"):
            continue
        found.append({
            "source": "GitHub",
            "name": item.get("full_name") or item.get("name", "Repository"),
            "description": item.get("description") or "Keine Beschreibung angegeben.",
            "url": url,
        })
    return found


SEARCHERS = {
    "APT": search_apt,
    "Flathub": search_flatpak,
    "Snap": search_snap,
    "GitHub": search_github,
}


class AppStore(Gtk.Window):
    def __init__(self):
        super().__init__(title="TIDALOS App Store")
        self.set_default_size(900, 650)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("tidalos")
        self.get_style_context().add_class("tidal-store")
        self.generation = 0
        self._build_ui()

    def _build_ui(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_border_width(22)
        self.add(outer)
        outer.pack_start(Gtk.Label(label="SOFTWARE FÜR DEIN SYSTEM", xalign=0), False, False, 0)
        outer.pack_start(Gtk.Label(label="TIDALOS App Store", xalign=0), False, False, 0)
        outer.get_children()[1].get_style_context().add_class("store-title")
        outer.pack_start(Gtk.Label(
            label="Suche in Ubuntu APT, Flathub, Snap und GitHub.",
            xalign=0,
        ), False, False, 0)
        search_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.pack_start(search_bar, False, False, 0)
        self.query = Gtk.SearchEntry(placeholder_text="Zum Beispiel: Firefox, Blender, VS Code")
        self.query.connect("activate", self.search)
        search_bar.pack_start(self.query, True, True, 0)
        self.source = Gtk.ComboBoxText()
        for name in SOURCE_NAMES:
            self.source.append_text(name)
        self.source.set_active(0)
        search_bar.pack_start(self.source, False, False, 0)
        button = Gtk.Button(label="Suchen")
        button.get_style_context().add_class("suggested-action")
        button.connect("clicked", self.search)
        search_bar.pack_start(button, False, False, 0)
        self.status = Gtk.Label(label="Wähle eine Quelle und suche nach einer Anwendung.", xalign=0)
        self.status.set_line_wrap(True)
        self.status.set_max_width_chars(110)
        self.status.get_style_context().add_class("store-muted")
        outer.pack_start(self.status, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        outer.pack_start(scroll, True, True, 0)
        self.results = Gtk.ListBox()
        self.results.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.results)
        outer.pack_end(Gtk.Label(
            label="GitHub-Treffer öffnen das Projekt zur manuellen Prüfung; dort wird nichts automatisch installiert.",
            xalign=0,
        ), False, False, 0)
        outer.get_children()[-1].get_style_context().add_class("store-muted")
        self.show_all()

    def search(self, _widget):
        query = self.query.get_text().strip()
        if len(query) < 2:
            self.status.set_text("Gib mindestens zwei Zeichen für die Suche ein.")
            return
        selected = self.source.get_active_text()
        sources = tuple(SEARCHERS) if selected == "Alle Quellen" else (selected,)
        if not all(character.isprintable() for character in query):
            self.status.set_text("Die Suche enthält ungültige Zeichen.")
            return
        self.generation += 1
        generation = self.generation
        self.status.set_text("Suche läuft …")
        threading.Thread(
            target=self._search_sources, args=(generation, query, sources), daemon=True
        ).start()

    def _search_sources(self, generation, query, sources):
        results, errors = [], []
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            searches = {
                executor.submit(SEARCHERS[source], query): source
                for source in sources
            }
            for future in as_completed(searches):
                source = searches[future]
                try:
                    results.extend(future.result())
                except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
                    errors.append(f"{source}: {error}")
        GLib.idle_add(self._show_results, generation, results, errors)

    def _show_results(self, generation, results, errors):
        if generation != self.generation:
            return GLib.SOURCE_REMOVE
        for row in self.results.get_children():
            self.results.remove(row)
        for result in results:
            self._add_result(result)
        self.results.show_all()
        message = f"{len(results)} Treffer."
        if errors:
            message += " Nicht verfügbare Quellen: " + " | ".join(errors)
        elif not results:
            message = "Keine Treffer gefunden."
        self.status.set_text(message)
        return GLib.SOURCE_REMOVE

    def _add_result(self, result):
        row = Gtk.ListBoxRow()
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        card.set_border_width(10)
        card.get_style_context().add_class("store-card")
        row.add(card)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.pack_start(text, True, True, 0)
        title = Gtk.Label(label=f"{result['name']}  ·  {result['source']}", xalign=0)
        text.pack_start(title, False, False, 0)
        description = Gtk.Label(label=result["description"], xalign=0)
        description.set_line_wrap(True)
        description.set_max_width_chars(90)
        text.pack_start(description, False, False, 0)
        if result["source"] == "GitHub":
            button = Gtk.Button(label="Projekt öffnen")
            button.connect("clicked", self.open_project, result["url"])
        else:
            button = Gtk.Button(label="Installieren")
            button.connect("clicked", self.install, result)
        card.pack_end(button, False, False, 0)
        self.results.add(row)

    def open_project(self, _button, url):
        try:
            Gtk.show_uri_on_window(self, url, Gdk.CURRENT_TIME)
        except GLib.Error as error:
            self.status.set_text(f"Projekt konnte nicht im Browser geöffnet werden: {error.message}")

    def install(self, _button, result):
        if not shutil.which("pkexec"):
            self.status.set_text("pkexec fehlt; Installation benötigt eine grafische Administratorabfrage.")
            return
        source, package = result["source"], result["install"]
        commands = {
            "APT": ["apt-get", "install", "-y", "--", package],
            "Flathub": ["flatpak", "install", "--system", "--noninteractive", "flathub", package],
            "Snap": ["snap", "install", package],
        }
        self.status.set_text(f"Installiere {result['name']} …")
        threading.Thread(
            target=self._install_worker,
            args=(result["name"], ["pkexec", *commands[source]]),
            daemon=True,
        ).start()

    def _install_worker(self, name, command):
        try:
            output = run_command(command, timeout=1800)
            message = f"{name} wurde installiert."
            if output.strip():
                message += f" {output.strip()[-500:]}"
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            message = f"Installation fehlgeschlagen: {error}"
        GLib.idle_add(self.status.set_text, message)


if __name__ == "__main__":
    window = AppStore()
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()
