#!/usr/bin/env python3
"""Build TIDALOS architecture-independent Debian packages with dpkg-deb."""
import gzip
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
PACKAGES = {
    "tidalos-wallpapers": ("", "Original Deep Ocean wallpaper and TIDALOS identity"),
    "tidalos-theme": ("cinnamon-common, gnome-themes-extra, adwaita-icon-theme", "Deep Ocean Cinnamon and GTK 3 theme"),
    "tidalos-default-settings": ("cinnamon, nemo, tidalos-theme (= 0.1.0), tidalos-wallpapers (= 0.1.0), fonts-ubuntu, libglib2.0-bin", "Default appearance for new TIDALOS desktop users"),
    "tidalos-welcome": ("python3, python3-gi, gir1.2-gtk-3.0, autorandr, arandr, cinnamon-settings-daemon, x11-xserver-utils, tidalos-wallpapers (= 0.1.0)", "Native TIDALOS welcome and display profile applications"),
    "tidalos-store": ("python3, python3-gi, gir1.2-gtk-3.0, apt, flatpak, snapd", "TIDALOS multi-source application store"),
    "tidalos-installer": ("calamares, efibootmgr, grub-efi-amd64-bin, grub-pc-bin, squashfs-tools, zenity", "TIDALOS disk installer"),
    "tidalos-desktop": ("tidalos-default-settings (= 0.1.0), tidalos-welcome (= 0.1.0), tidalos-store (= 0.1.0), tidalos-installer (= 0.1.0), cinnamon, nemo, gnome-terminal, lightdm, slick-greeter, network-manager-gnome", "TIDALOS desktop metapackage"),
}


def put(root, source, destination, executable=False):
    target = root / destination.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / source, target)
    target.chmod(0o755 if executable else 0o644)


def write(root, destination, text, executable=False):
    target = root / destination.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    target.chmod(0o755 if executable else 0o644)


def populate(root, name):
    if name == "tidalos-wallpapers":
        put(root, "assets/wallpapers/tidal-depths.svg", "usr/share/backgrounds/tidalos/tidal-depths.svg")
        put(root, "assets/branding/tidalos.svg", "usr/share/icons/hicolor/scalable/apps/tidalos.svg")
        write(root, "usr/share/gnome-background-properties/tidalos.xml", '<?xml version="1.0"?><wallpapers><wallpaper deleted="false"><name>Tidal Depths</name><filename>/usr/share/backgrounds/tidalos/tidal-depths.svg</filename><options>zoom</options><pcolor>#061d2b</pcolor><scolor>#061d2b</scolor><shade_type>solid</shade_type></wallpaper></wallpapers>\n')
    elif name == "tidalos-theme":
        for source in (REPO / "assets/themes/Tidal-Deep").rglob("*"):
            if source.is_file():
                put(root, source.relative_to(REPO), "usr/share/themes/Tidal-Deep/" + str(source.relative_to(REPO / "assets/themes/Tidal-Deep")))
    elif name == "tidalos-default-settings":
        put(root, "config/90_tidalos.gschema.override", "usr/share/glib-2.0/schemas/90_tidalos.gschema.override")
        for script in ("postinst", "postrm"):
            write(root, f"DEBIAN/{script}", '#!/bin/sh\nset -e\nif command -v glib-compile-schemas >/dev/null 2>&1; then\n    glib-compile-schemas /usr/share/glib-2.0/schemas\nfi\n', executable=True)
    elif name == "tidalos-welcome":
        put(root, "apps/welcome.py", "usr/bin/tidalos-welcome", executable=True)
        put(root, "apps/tidalos-welcome.desktop", "usr/share/applications/tidalos-welcome.desktop")
        put(root, "apps/tidalos-welcome-autostart.desktop", "etc/xdg/autostart/tidalos-welcome.desktop")
        put(root, "apps/tidalos-drivers.desktop", "usr/share/applications/tidalos-drivers.desktop")
        put(root, "apps/displays.py", "usr/bin/tidalos-displays", executable=True)
        put(root, "apps/tidalos-displays.desktop", "usr/share/applications/tidalos-displays.desktop")
    elif name == "tidalos-store":
        put(root, "apps/store.py", "usr/bin/tidalos-store", executable=True)
        put(root, "apps/tidalos-store.desktop", "usr/share/applications/tidalos-store.desktop")
    elif name == "tidalos-installer":
        put(root, "apps/tidalos-installer", "usr/bin/tidalos-installer", executable=True)
        put(root, "apps/tidalos-installer.desktop", "usr/share/applications/tidalos-installer.desktop")
        put(root, "config/calamares/settings.conf", "etc/calamares/settings.conf")
        for source in (REPO / "config/calamares/modules").rglob("*"):
            if source.is_file():
                put(root, source.relative_to(REPO), "etc/calamares/modules/" + str(source.relative_to(REPO / "config/calamares/modules")))
        put(root, "assets/branding/tidalos.svg", "usr/share/calamares/branding/tidalos/tidalos.svg")
        put(root, "config/calamares/show.qml", "usr/share/calamares/branding/tidalos/show.qml")
        put(root, "config/calamares/branding.desc", "usr/share/calamares/branding/tidalos/branding.desc")
        put(root, "assets/branding/tidalos.svg", "etc/calamares/branding/tidalos/tidalos.svg")
        put(root, "config/calamares/show.qml", "etc/calamares/branding/tidalos/show.qml")
        put(root, "config/calamares/branding.desc", "etc/calamares/branding/tidalos/branding.desc")


def build():
    if not shutil.which("dpkg-deb"):
        raise SystemExit("dpkg-deb is required. Run this script under Linux/WSL.")
    output = REPO / "dist"
    output.mkdir(exist_ok=True)
    for name, (dependencies, description) in PACKAGES.items():
        with tempfile.TemporaryDirectory(prefix=f"{name}-") as temporary:
            root = Path(temporary)
            populate(root, name)
            size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
            control = f"Package: {name}\nVersion: {VERSION}\nSection: x11\nPriority: optional\nArchitecture: all\nMaintainer: TIDALOS Development <development@tidalos.invalid>\nInstalled-Size: {(size + 1023) // 1024}\n"
            if dependencies:
                control += f"Depends: {dependencies}\n"
            control += f"Description: {description}\n Tidalwave OS 0.1 desktop components for Ubuntu Cinnamon.\n"
            write(root, "DEBIAN/control", control)
            put(root, "LICENSE", f"usr/share/doc/{name}/copyright")
            changelog = f"{name} ({VERSION}) unstable; urgency=low\n\n  * Initial TIDALOS Deep Ocean desktop alpha.\n\n -- TIDALOS Development <development@tidalos.invalid>  Sun, 18 Oct 2026 12:00:00 +0200\n"
            (root / f"usr/share/doc/{name}/changelog.gz").write_bytes(gzip.compress(changelog.encode(), mtime=0))
            for directory in root.rglob("*"):
                if directory.is_dir():
                    directory.chmod(0o755)
            root.chmod(0o755)
            subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(root), str(output / f"{name}_{VERSION}_all.deb")], check=True)
    print(f"Built {len(PACKAGES)} packages in {output}")


if __name__ == "__main__":
    build()
