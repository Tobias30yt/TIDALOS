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

Die vorangegangene UEFI-Gastdiagnose meldete die virtuelle Ethernet-Schnittstelle als `unmanaged`. Der Build überschreibt jetzt die Ubuntu-Vorgabedatei `10-globally-managed-devices.conf` unter `/etc/NetworkManager/conf.d`, damit deren Catch-all-Regel die Ethernet-Schnittstelle nicht länger ausschließt. Dieser Fix muss im nächsten ISO-Build erneut in QEMU geprüft werden.
