# TIDALOS bauen

## Voraussetzungen

Linux amd64 (hier: Ubuntu in WSL 2), Root-Rechte für debootstrap und chroot, Internetzugang und mindestens 20 GB freier Speicher. Der Linux-Arbeitsordner muss auf einem Linux-Dateisystem liegen; die ISO darf auf dem Windows-Laufwerk ausgegeben werden. Installiere `squashfs-tools` (enthält `mksquashfs` und `unsquashfs`).

```bash
sudo apt-get update
sudo apt-get install debootstrap xorriso grub-pc-bin grub-efi-amd64-bin \
  grub-common mtools squashfs-tools python3
```

## Pakete

```bash
python3 scripts/build-packages.py
```

Erzeugt sieben `.deb`-Pakete in `dist/`, darunter den Calamares-Festplatteninstaller und den TIDALOS App Store. Das Desktop-Metapaket zieht beide als Abhängigkeit nach. Der Image-Build löst Paketabhängigkeiten mit APT auf und repariert einen eventuell teilweise installierten Paketstatus nach einem abgebrochenen Lauf. Zum Ausprobieren auf einer separaten Ubuntu-24.04-Testmaschine mit grafischem Desktop:

```bash
sudo apt install ./dist/tidalos-*_0.1.0_all.deb
```

Anschließend bei der Anmeldung Cinnamon auswählen. Die Standardwerte greifen bei Benutzern ohne eigene überschreibende Einstellungen. Bei bestehenden Cinnamon-Profilen das Theme „Tidal-Deep“ in den Einstellungen auswählen. Das Paket ersetzt keine persönlichen dconf-Einstellungen. Theme entfernen: `sudo apt remove tidalos-desktop tidalos-default-settings tidalos-theme tidalos-welcome tidalos-wallpapers`; zuvor bei einem persönlich ausgewählten Theme auf Adwaita wechseln. Abhängigkeiten werden dabei nicht automatisch entfernt.

## Live-ISO

```bash
sudo bash scripts/build-live.sh
```

Der Build arbeitet unter `/var/tmp/tidalos-build-0.1.0` und erzeugt `dist/tidalos-0.1.0-amd64-r3.iso`, eine Paketliste und `SHA256SUMS`. Die sichtbare Build-Kennung `r3` im Dateinamen und Startmenü unterscheidet dieses Image von älteren Dateien. Er verwendet signierte Ubuntu-Noble-Paketquellen mit Updates und Security. Bei jedem Build werden lokale TIDALOS-Pakete ausdrücklich neu installiert und die Calamares-Branding-Datei danach direkt mit der Repository-Datei abgeglichen. Vor dem Erzeugen der ISO prüft `unsquashfs` außerdem, dass die Branding-Datei im gepackten Live-Dateisystem exakt der Repository-Datei entspricht; ein veralteter oder unvollständiger Installer-Build bricht dadurch früh ab. Ein Lock verhindert gleichzeitige Builds im selben Verzeichnis. Ein frischer Build kann mit `sudo TIDALOS_BUILD_DIR=/var/tmp/tidalos-build-neu bash scripts/build-live.sh` gestartet werden. Nicht unter Windows-PowerShell direkt ausführen.

Die Abhängigkeiten sind noch nicht auf einen Repository-Snapshot fixiert; spätere Builds können neuere Ubuntu-Pakete enthalten. Deshalb ist dies ein wiederholbarer Buildprozess, noch kein bitidentisch reproduzierbarer Releasebuild. `.deb`- und ISO-Signierung sowie ein eigenes Update-Repository sind noch nicht eingerichtet.

### Java und Steam

Das Live-Image enthält OpenJDK 21 JDK (`openjdk-21-jdk`) und den Steam-Starter aus Ubuntus Multiverse-Quelle. Der Build aktiviert dafür zusätzlich die i386-Paketarchitektur und installiert Mesa-Vulkan-Treiber für amd64 und i386. Steam lädt bei der ersten Benutzung weitere Laufzeitdateien über das Internet.

### Gaming und Entwicklung

Die Live-Pakete enthalten Lutris, Wine für 64- und 32-Bit-Anwendungen, Winetricks, GameMode, MangoHud, Steam-Geräteregeln, Vulkan-Werkzeuge und die Spiele SuperTuxKart, Hedgewars, OpenTTD (mit OpenGFX/OpenMSX) und Extreme Tux Racer. OBS Studio und pavucontrol ergänzen Streaming/Aufzeichnung und Audio-Geräteauswahl. SuperTuxKart und Hedgewars benötigen große Datensammlungen; dadurch wächst das ISO deutlich. Für Spiele wird eine Vulkan-fähige Grafik empfohlen. Hardwareabhängige proprietäre Grafiktreiber werden nicht in das universelle ISO eingebaut; `ubuntu-drivers-common` und die grafischen Ubuntu-Systemwerkzeuge stehen zur Auswahl und Installation passender Treiber bereit. Der Starter „Grafiktreiber“ öffnet den Tab für zusätzliche Treiber, sofern der installierte Ubuntu-Dialog diesen Tab anbietet. Die Treiberinstallation bleibt eine bewusste, vom Benutzer bestätigte Systemänderung.

Die Entwicklungswerkzeuge umfassen Git, GCC/G++, CMake, GDB, pkg-config, Python 3 mit pip und virtuellen Umgebungen, Node.js/npm, Rust/Cargo, OpenJDK 21 JDK, Geany und Neovim. Der Build prüft, dass Python 3 im Root-Dateisystem vorhanden ist. `update-manager` und Synaptic stellen grafische Update- und Paketverwaltung bereit. Das zusätzliche Werkzeugset vergrößert das ISO und benötigt beim Build mehr Downloadzeit und Speicherplatz. Steam, Lutris und Winetricks benötigen Internet, um Spiele und weitere Laufzeitkomponenten zu laden.

Für mehrere Monitore sind Cinnamon-Anzeigeeinstellungen, `arandr` als grafische XRandR-Oberfläche und `x11-xserver-utils` (einschließlich `xrandr`) enthalten. Ob externe Anschlüsse, Auflösungen und mehrere Displays funktionieren, hängt zusätzlich vom Grafiktreiber, der virtuellen Maschine und der Hardware ab.

Alle diese Pakete sind Teil desselben Live-Dateisystems und werden vom Festplatteninstaller mitinstalliert. Änderungen im nicht-persistenten Live-System gehen beim Ausschalten weiterhin verloren.

### App Store und Flathub

Der native GTK-Store sucht parallel in APT, Flathub, Snap und GitHub. Installationen aus APT, Flathub und Snap erfordern eine grafische Administratorbestätigung. Flathub wird beim Image-Build als systemweites Flatpak-Remote eingerichtet; Snapd und sein Socket sind aktiviert. Der Live-Build benötigt dafür Internetzugriff auf `dl.flathub.org`.

GitHub-Ergebnisse sind Projekthinweise und öffnen nur die GitHub-Projektseite im Browser. Repositories oder dort bereitgestellte Skripte werden nicht automatisch installiert oder ausgeführt. GitHub-Suche benötigt Internet; die öffentliche API kann Suchlimits anwenden. Installierte Anwendungen und Änderungen im Live-System sind ohne Persistenz nach dem Ausschalten nicht vorhanden.

### Installation auf Festplatte

Im gestarteten Live-Desktop „TIDALOS installieren“ öffnen. Calamares kopiert das Live-Dateisystem auf die ausgewählte Partition, richtet den Benutzer und den Bootloader ein und unterstützt UEFI sowie BIOS. Die Installationsauswahl startet absichtlich ohne vorausgewählte Partitionierungsoption. „Datenträger löschen“ löscht Daten auf dem ausgewählten Datenträger; vor dem Bestätigen sorgfältig Modell und Größe prüfen. Verschlüsselung und Secure Boot werden in dieser Alpha nicht unterstützt.

Den vollständigen Installationsablauf nur in einer Test-VM mit einer entbehrlichen virtuellen Festplatte testen. Der bestehende `test-boot.py`-Smoke-Test startet absichtlich ohne Festplatte und testet daher nur den Live-Start. Vor einem Release muss zusätzlich eine Installation auf leerem GPT-Datenträger unter UEFI und leerem MBR-Datenträger unter BIOS durchgeführt und der Neustart von der virtuellen Festplatte geprüft werden.

## Boot-Test

```bash
sudo apt install qemu-system-x86 ovmf
sudo python3 scripts/test-boot.py dist/tidalos-0.1.0-amd64-r2.iso \
  --firmware bios --output dist/boot-bios
sudo python3 scripts/test-boot.py dist/tidalos-0.1.0-amd64-r2.iso \
  --firmware uefi --output dist/boot-uefi
```

Die Test-VM hat 3 GB RAM, zwei virtuelle CPUs, eine virtuelle Netzwerkkarte und keine Festplatte. Sie nutzt KVM, falls verfügbar, sonst Softwareemulation. Für SuperTuxKart und OBS ist eine VM mit mehr Arbeitsspeicher und 3D-Beschleunigung erforderlich; ihre Funktion sollte auf echter Hardware oder einer geeigneten GPU-VM getestet werden. Die Aufnahmen und das serielle Log müssen geprüft werden: Ein laufender QEMU-Prozess allein beweist keinen erfolgreichen Desktopstart.

Änderungen in der Live-Sitzung gehen beim Ausschalten verloren. Der Installer ist neu und muss in einer dedizierten Test-VM validiert werden. Secure Boot ist für dieses unsignierte Entwicklungsimage ausgeschaltet. Hardwarekompatibilität ist außerhalb der getesteten VMs noch nicht validiert.

## Designumfang

Das Cinnamon-Theme baut auf dem vollständigen mitgelieferten Cinnamon-Theme auf und verändert Panel, Menüs, Dialoge, Benachrichtigungen und weitere Shell-Oberflächen. GTK-3-Anwendungen nutzen ein auf Adwaita basierendes Tidal-Deep-Theme. GTK 4/libadwaita und Anwendungen mit eigenem Design werden noch nicht vollständig angepasst. Fensterrahmen ohne eigene Titelleiste verwenden zunächst Adwaita.

Das Willkommensprogramm ist natives Python/GTK 3. Es führt ausschließlich die fest definierten Anwendungen Cinnamon-Einstellungen, Nemo und Terminal aus. Die Option „Beim Anmelden anzeigen“ speichert eine benutzereigene Einstellung unter `~/.config/tidalos/welcome.json`.
