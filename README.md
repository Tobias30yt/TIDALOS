# TIDALOS

**Tidalwave OS** — ein eigener Desktop auf Ubuntu-Basis.

Status: **0.1.0 Live Alpha**. Nativer Cinnamon-Desktop, eigenes Theme, Willkommensprogramm und Calamares-Festplatteninstaller sind im Build integriert. Für den neuesten Stand muss Build r4 neu gebaut und genau die Datei `dist/tidalos-0.1.0-amd64-r4.iso` in der VM ausgewählt werden. Die Installation bietet manuelle Partitionierung und geführte Datenträgeroptionen; dabei ausgewählte Partitionen können gelöscht werden. Installer-Installation und Hardwareunterstützung sind noch nicht end-to-end validiert. Prüfergebnisse stehen in `docs/VALIDATION.md`.

## Starten

Die neu gebaute Datei `dist/tidalos-0.1.0-amd64-r4.iso` als virtuelles DVD-Laufwerk in einer VM einlegen. Linux/Ubuntu 64-bit, mindestens 3 GB RAM und 2 CPUs wählen, Secure Boot ausschalten. Im Bootmenü „TIDALOS 0.1 - Live Desktop (Build r4)“ auswählen. Die Live-Sitzung meldet den Benutzer `tidal` automatisch an.

Die VM benötigt zum Ausprobieren keine Festplatte. Änderungen der Live-Sitzung gehen beim Ausschalten verloren. Zum Installieren im Live-Desktop „TIDALOS installieren“ öffnen. Für einen Test eine VM mit einer leeren virtuellen Festplatte verwenden; die gewählte Installationsoption kann vorhandene Daten löschen. Die SHA-256-Prüfsumme liegt in `dist/SHA256SUMS`. Auf echter Hardware ist die Alpha noch nicht geprüft.

Der vollständige [Build- und Testablauf](docs/BUILD.md) beschreibt Paketbau, ISO-Erstellung und QEMU-Prüfung.

## Richtung

- Vorläufige Basis: Ubuntu 24.04 LTS, amd64.
- Desktop: Cinnamon; vertrautes Startmenü, Taskleiste unten, Nemo als Dateimanager.
- Gaming: Steam, Lutris, Wine (64/32 Bit), GameMode, MangoHud und Vulkan-Werkzeuge; passende Grafiktreiber werden über Ubuntus Treiberverwaltung gewählt.
- Spiele: SuperTuxKart, Hedgewars, OpenTTD mit freien Grafik-/Musiksets und Extreme Tux Racer.
- Streaming und Geräte: OBS Studio, Steam-Controller-/Geräte-Regeln und ein eigener Startpunkt zur Auswahl passender Grafiktreiber.
- Coding: Git, GCC/G++, CMake, GDB, Python mit pip/venv, Node.js/npm, Rust/Cargo, Java 21 JDK, Geany und Neovim.
- Software: eigener TIDALOS App Store mit Suche in APT, Flathub, Snap und GitHub.
- Systemwerkzeuge: grafische Update- und Paketverwaltung, Hardware-Treiber-Auswahl, Terminal-Monitoring und Datei-/Textwerkzeuge.
- Mehrere Monitore: Cinnamon-Anzeigeeinstellungen, Arandr, XRandR und Autorandr mit speicherbaren Layoutprofilen und automatischer Wiederherstellung beim Displaywechsel.
- Design: dunkle, ruhige Oberflächen; Türkis als Akzent; abstrakte Ozeanwellen.
- Bestehende Ubuntu-Paketverwaltung und Sicherheitsupdates beibehalten.

Ubuntu 24.04 ist eine bewusst konservative Entwicklungsbasis, keine Aussage zur neuesten Ubuntu-Version. Vor einem öffentlichen Release die Basis erneut bewerten. Der Ubuntu-Unterbau erhält reguläre Sicherheitswartung bis Mai 2029; daraus folgt keine gleich lange Wartungszusage für sämtliche Universe-Pakete oder unsere eigenen Anpassungen.

## Dateien

- `design/tokens.json`: erste Designwerte.
- `assets/themes/Tidal-Deep`: natives Cinnamon- und GTK-3-Theme.
- `apps/welcome.py`: natives Willkommensprogramm mit echten Anwendungsstartern.
- `apps/store.py`: eigener grafischer Store mit Paketinstallation aus APT, Flathub und Snap sowie GitHub-Projektsuche.
- Python 3 ist Teil der Live-Paketliste und wird vor der ISO-Erstellung vom Build geprüft.
- `config/90_tidalos.gschema.override`: Standardwerte für neue Cinnamon-Profile.
- `config/live-packages.txt`: Paketauswahl für die Live-ISO.
- `config/calamares/`: Calamares-Installerablauf und Partitions-, Benutzer- und Locale-Einstellungen.
- `scripts/build-packages.py`: sieben installierbare Debian-Pakete.
- `scripts/build-live.sh`: Ubuntu-Noble-Unterbau, Kernel, Casper und BIOS-/UEFI-Bootimage.
- `scripts/test-boot.py`: isolierte VM-Bootprüfung mit Screenshots und Log.
- `assets/wallpapers/tidal-depths.svg`: eigener skalierbarer Hintergrund.
- `scripts/wallpaper.py`: Hintergrund in einer laufenden Cinnamon-Sitzung setzen und zurücksetzen; keine Root-Rechte erforderlich.
- `docs/ROADMAP.md`: Weg zum nativen Desktop und zur ersten ISO.

Gaming- und Coding-Programme sind im Live-System und nach einer Festplatteninstallation verfügbar. Vier freie Spiele sowie Steam, Lutris, Wine, GameMode, MangoHud und Vulkan-Werkzeuge sind enthalten; OBS Studio unterstützt Aufzeichnung und Streaming. Die Spiele vergrößern das Image erheblich. Der Store ist im Anwendungsmenü und im Willkommensfenster erreichbar. Flathub wird systemweit eingerichtet; Snapd ist vorinstalliert und sein Socket aktiviert. Installationen benötigen eine Administratorbestätigung und im Live-System gehen Änderungen beim Ausschalten verloren. GitHub-Treffer öffnen die Projektseite zur manuellen Prüfung; beliebige Repository-Skripte werden aus Sicherheitsgründen nicht automatisch ausgeführt. Steam, Lutris und Winetricks laden zusätzliche Spiele beziehungsweise Windows-Laufzeitkomponenten bei Bedarf aus dem Internet. NVIDIA-Treiber werden nicht fest eingebaut; „Grafiktreiber“ öffnet Ubuntus Treiberverwaltung, in der passende Hardwaretreiber geprüft und ausgewählt werden können. Für mehrere Bildschirme stehen Cinnamon-Anzeigeeinstellungen, Arandr und XRandR zur Verfügung; tatsächliche Display-Ausgänge hängen vom Grafiktreiber und der Hardware ab.

## Hintergrund unter Cinnamon ausprobieren

Dieses Repository auf eine Ubuntu-/Cinnamon-Testmaschine kopieren. In einem Terminal der grafischen Sitzung:

```bash
python3 scripts/wallpaper.py apply
python3 scripts/wallpaper.py restore
```

Das Skript prüft die benötigten Cinnamon-Einstellungen vor dem Schreiben und sichert deren ursprüngliche Werte einmalig unter `$XDG_STATE_HOME/tidalos` (Standard: `~/.local/state/tidalos`). Wiederholtes Anwenden überschreibt diese Sicherung nicht. Der Hintergrund wird nach `$XDG_DATA_HOME/backgrounds/tidalos` kopiert. `restore` stellt die Einstellungen wieder her und behält die Sicherung sowie die Bilddatei bei. Es werden weder Pakete installiert noch Systemdateien geändert.

Der ältere interaktive Entwurf im Chat simuliert die Oberfläche. Das neue Willkommensprogramm und die Desktop-Pakete sind native Linux-Komponenten. Das separate Wallpaper-Hilfsskript wurde noch nicht in einer interaktiven Cinnamon-Sitzung auf Anwenden und Wiederherstellen geprüft.

## Referenzen

- [Ubuntu 24.04 Release Notes](https://documentation.ubuntu.com/release-notes/24.04/)
- [Cinnamon-Pakete in Ubuntu Noble](https://packages.ubuntu.com/search?keywords=cinnamon&searchon=names&suite=noble)
- [Cinnamon-Projekt](https://github.com/linuxmint/cinnamon)

Die Originalmarken Ubuntu, Linux Mint und Cinnamon gehören ihren jeweiligen Rechteinhabern. TIDALOS ist unser Projektname; eine öffentliche Namens- und Markenprüfung steht aus.
