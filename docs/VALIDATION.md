# Prüfung des ersten Entwurfs

Stand: 18. Oktober 2026.

- JavaScript-Syntax und Design-JSON erfolgreich geprüft.
- Mit Playwright und lokalem Chrome geprüft: Startmenü-Suche, Ordnerwechsel, Akzentwahl, Taskleistenstil, Schnelleinstellungen und Schließen per Escape. Keine JavaScript-Laufzeitfehler.
- Layout bei 1024, 736, 390 und 320 Pixel Breite auf horizontales Überlaufen geprüft; Desktop- und schmale Ansicht visuell kontrolliert.
- Der isolierte Browsertest stellt die vom Chat bereitgestellten Lucide-Symbole nicht dar. Die Symbolinitialisierung im Chat bleibt vom Host abhängig.
- Python-Syntax und XML-Struktur des nativen Hintergrundbilds geprüft.
- Anwenden/Wiederherstellen des Hintergrunds noch nicht in einer echten Cinnamon-Sitzung getestet. WSL-Abfrage war in dieser Umgebung nicht zugänglich; keine native Linux-Laufzeitprüfung durchgeführt.

Die Vorschau ist ein Oberflächenentwurf, kein ausführbares Betriebssystem. Das native Live-Image ist gebaut; Installation und Hardwareunterstützung sind noch offen.

## Installer-Fortschritt

Calamares-Konfiguration, Paket und Live-Desktopstarter wurden ergänzt. Das Installer-DEB wurde gebaut und sein Payload geprüft; das vorhandene ISO wurde in dieser Sitzung nicht neu gebaut. Die Konfiguration verwendet das Casper-SquashFS als Installationsquelle, beginnt ohne vorausgewählte Partitionierungsoption, lässt bei der Benutzeranlage Autologin standardmäßig ausgeschaltet und entfernt die nur für die Live-Sitzung bestimmte LightDM-Autologin-Datei aus dem installierten System. Eine Installation mit Neustart wurde noch nicht ausgeführt. Der vorhandene QEMU-Boottest ist diskless und kann den Installer nicht validieren.

Die Calamares-Branding-Datei und die QML-Slideshow werden nun sowohl unter `/etc/calamares/branding/tidalos` als auch unter `/usr/share/calamares/branding/tidalos` installiert. Der Build prüft beide Kopien auch im SquashFS; der Starter verlangt den Marker `IMAGE_BUILD=r4` und meldet fehlende oder alte Branding-Dateien vor dem Start. Die Slideshow-Prüfung ignoriert nun abschließende CRLF-Zeilenenden, wie sie ein Windows-Git-Checkout erzeugt. Das Installer-Paket wurde erneut gebaut und enthält beide Pfade. Das neue r4-ISO wurde noch nicht erstellt, daher ist der Fix noch nicht in Calamares zur Laufzeit oder durch eine Festplatteninstallation verifiziert.

Die Anzeigeverwaltung mit Arandr-/Cinnamon-Startern, Autorandr-Profilen und zugehörigen Paketabhängigkeiten wurde ergänzt. Die geänderten Python-Dateien bestehen den Syntaxcheck und das Willkommens-/Anzeige-Paket wurde gebaut und geprüft. Monitor-Hotplug und die automatische Profilwiederherstellung sind noch nicht in einer grafischen Sitzung getestet.

Die vorangegangene UEFI-Gastdiagnose meldete die virtuelle Ethernet-Schnittstelle als `unmanaged`. Der Build überschreibt jetzt die Ubuntu-Vorgabedatei `10-globally-managed-devices.conf` unter `/etc/NetworkManager/conf.d`, damit deren Catch-all-Regel die Ethernet-Schnittstelle nicht länger ausschließt. Dieser Fix muss im nächsten ISO-Build erneut in QEMU geprüft werden.
