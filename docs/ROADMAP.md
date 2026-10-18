# Von der Idee zur Distribution

## 0. Entwurf — umgesetzt

Name, Farben und Fensteraufbau festgelegt. Interaktiver Entwurf im Chat, Designwerte, Hintergrundbild und natives Theme vorhanden.

## 1. Native Entwicklungsmaschine — eingerichtet

Ubuntu 24.04 wird isoliert mit debootstrap unter WSL aufgebaut. Paketversionen stehen in `dist/packages.manifest`. QEMU mit KVM dient als Testumgebung. Audio, Hardware, Skalierung und umfangreiche Eingabetests stehen noch aus.

## 2. TIDALOS Desktop — erste native Version

Tidal-Deep für Cinnamon und GTK 3 implementiert; das vollständige jeweilige Upstream-Theme dient als Grundlage. Das native Willkommensprogramm startet Cinnamon-Einstellungen, Nemo und Terminal. GTK 4/libadwaita, ein eigenes Iconset und eigene Fensterrahmen sind nächste Designschritte.

Die erste Live-Version verwendet Cinnamon, LightDM/Slick Greeter, Nemo, GNOME Terminal, Mousepad und Geany. Synaptic, Update Manager und der eigene TIDALOS App Store sind enthalten; der Store sucht in APT, Flathub, Snap und GitHub. Java 21 JDK sowie ein Basiswerkzeugsatz für C/C++, Python, Node.js und Rust sind vorinstalliert. Steam, Lutris, Wine, GameMode, MangoHud, OBS und vier native Spiele bilden den Gaming-Startpunkt. Ein eigener Starter öffnet Ubuntus Auswahl zusätzlicher Hardwaretreiber; proprietäre Treiber bleiben bewusst hardwareabhängig. Mehrere Displays werden über Cinnamon-Anzeigeeinstellungen und XRandR-Werkzeuge unterstützt, abhängig von Treiber und Hardware. Ein Browser ist noch nicht enthalten.

## 3. Debian-Pakete — gebaut

`tidalos-wallpapers`, `tidalos-theme`, `tidalos-default-settings`, `tidalos-welcome` und das Metapaket `tidalos-desktop` sind gebaut. Die Installation und GSettings-Schemas sind geprüft. Ubuntu-Quellen und `/etc/os-release` bleiben erhalten; `/etc/tidalos-release` ergänzt die Projektkennung.

## 4. Live-Image und Installer — Alpha

Live-ISO mit Casper, Linux-Kernel, SquashFS und GRUB erstellt. BIOS- und UEFI-Start wurden bis zum nativen Desktop geprüft. Calamares ist integriert und kann das Live-Dateisystem auf einen ausgewählten Datenträger kopieren. Die Installation selbst muss noch in UEFI- und BIOS-Test-VMs validiert werden. Live-Persistenz, signierte Bootkette, Repository-Snapshots und Release-Signierung sind offen. Secure Boot wird nicht unterstützt.

## 5. Release-Kriterien

Live-Start und Installation, Neustart, Updates, WLAN/Ethernet, Audio, Suspend, Multi-Monitor, HiDPI, Barrierefreiheit und Wiederherstellung testen. Prüfsummen, Paketliste, Lizenzinformationen und bekannte Probleme veröffentlichen. Ubuntu-Basissupport und eigene Wartungszusagen getrennt dokumentieren.
