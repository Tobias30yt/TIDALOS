#!/usr/bin/env bash
# Build an amd64 Ubuntu Noble live image. Run in a dedicated Linux build environment.
set -Eeuo pipefail
umask 022
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
version=0.1.0
image_revision=4
work=${TIDALOS_BUILD_DIR:-/var/tmp/tidalos-build-0.1.0}
[[ $EUID == 0 ]] || { echo 'Run with sudo in a Linux build environment.' >&2; exit 1; }
[[ $work == /var/tmp/tidalos-build-* && $work != *'..'* ]] || { echo 'Build directory must be /var/tmp/tidalos-build-*' >&2; exit 1; }
for tool in debootstrap chroot mount umount mksquashfs unsquashfs grub-mkrescue xorriso python3 dpkg-deb; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
if [[ -d $work && ! -f $work/.tidalos-build ]]; then
  echo "Refusing to reuse an unrelated directory: $work" >&2; exit 1
fi
mkdir -p "$work" "$repo/dist"
touch "$work/.tidalos-build"
exec 9>"$work/.lock"
flock -n 9 || { echo 'A TIDALOS build is already running.' >&2; exit 1; }
root="$work/rootfs"
iso="$work/iso"
cleanup() {
  local path
  for path in "$root/dev" "$root/proc" "$root/sys"; do
    if mountpoint -q "$path"; then umount -R "$path" || echo "Unmount failed: $path" >&2; fi
  done
}
trap cleanup EXIT
if [[ ! -f $work/.bootstrap-complete ]]; then
  [[ ! -d $root ]] || { echo 'Incomplete bootstrap; use a new TIDALOS_BUILD_DIR.' >&2; exit 1; }
  debootstrap --arch=amd64 --variant=minbase noble "$root" http://archive.ubuntu.com/ubuntu
  touch "$work/.bootstrap-complete"
fi
mkdir -p "$root/dev" "$root/proc" "$root/sys"
mount --rbind /dev "$root/dev"
mount --make-rslave "$root/dev"
mount -t proc proc "$root/proc"
mount -t sysfs sysfs "$root/sys"
cp /etc/resolv.conf "$root/etc/resolv.conf"
cat > "$root/etc/apt/sources.list" <<'SOURCES'
deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main restricted universe multiverse
SOURCES
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d"
chmod 755 "$root/usr/sbin/policy-rc.d"
if ! chroot "$root" dpkg --print-foreign-architectures | grep -qx i386; then
  chroot "$root" dpkg --add-architecture i386
fi
chroot "$root" apt-get update
chroot "$root" apt-get -f install -y --no-install-recommends
mapfile -t packages < <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$repo/config/live-packages.txt")
chroot "$root" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${packages[@]}"
python3 "$repo/scripts/build-packages.py"
mkdir -p "$root/tmp/tidalos-packages"
cp "$repo/dist/"tidalos-*"_${version}_all.deb" "$root/tmp/tidalos-packages/"
chroot "$root" /bin/bash -c 'DEBIAN_FRONTEND=noninteractive apt-get install --reinstall -y --no-install-recommends /tmp/tidalos-packages/*.deb'
for branding_dir in "$root/etc/calamares/branding/tidalos" "$root/usr/share/calamares/branding/tidalos"; do
  install -D -m 644 "$repo/config/calamares/branding.desc" "$branding_dir/branding.desc"
  install -m 644 "$repo/config/calamares/show.qml" "$branding_dir/show.qml"
  install -m 644 "$repo/assets/branding/tidalos.svg" "$branding_dir/tidalos.svg"
  if ! cmp -s "$repo/config/calamares/branding.desc" "$branding_dir/branding.desc" ||
     ! cmp -s "$repo/config/calamares/show.qml" "$branding_dir/show.qml" ||
     ! grep -q '^slideshow: "show.qml"$' "$branding_dir/branding.desc"; then
    echo "Calamares branding config is missing or differs from the repository source: $branding_dir" >&2
    exit 1
  fi
done
chroot "$root" python3 --version
chroot "$root" flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
chroot "$root" systemctl enable snapd.socket
chroot "$root" glib-compile-schemas --strict /usr/share/glib-2.0/schemas
printf 'de_DE.UTF-8 UTF-8\nen_US.UTF-8 UTF-8\n' > "$root/etc/locale.gen"
chroot "$root" locale-gen
printf 'LANG=de_DE.UTF-8\n' > "$root/etc/default/locale"
ln -sfn /usr/share/zoneinfo/Europe/Berlin "$root/etc/localtime"
printf 'Europe/Berlin\n' > "$root/etc/timezone"
printf 'XKBMODEL="pc105"\nXKBLAYOUT="de"\nXKBVARIANT=""\nXKBOPTIONS=""\n' > "$root/etc/default/keyboard"
printf 'tidalos\n' > "$root/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 tidalos\n::1 localhost ip6-localhost ip6-loopback\n' > "$root/etc/hosts"
cat > "$root/etc/casper.conf" <<'CASPER'
export USERNAME="tidal"
export USERFULLNAME="TIDALOS Live"
export HOST="tidalos"
export BUILD_SYSTEM="Ubuntu"
export FLAVOUR="Ubuntu"
CASPER
mkdir -p "$root/etc/lightdm/lightdm.conf.d" "$root/etc/NetworkManager/conf.d" "$root/etc/netplan"
cat > "$root/etc/lightdm/lightdm.conf.d/50-tidalos-live.conf" <<'LIGHTDM'
[Seat:*]
greeter-session=slick-greeter
user-session=cinnamon
autologin-user=tidal
autologin-user-timeout=0
LIGHTDM
cat > "$root/etc/lightdm/slick-greeter.conf" <<'GREETER'
[Greeter]
background=/usr/share/backgrounds/tidalos/tidal-depths.svg
theme-name=Tidal-Deep
icon-theme-name=Adwaita
draw-user-backgrounds=false
GREETER
rm -f "$root/etc/NetworkManager/conf.d/10-tidalos-live.conf"
cat > "$root/etc/NetworkManager/conf.d/10-globally-managed-devices.conf" <<'NETWORK'
[ifupdown]
managed=true
[keyfile]
unmanaged-devices=
NETWORK
cat > "$root/etc/netplan/01-tidalos-network-manager.yaml" <<'NETPLAN'
network:
  version: 2
  renderer: NetworkManager
NETPLAN
chmod 600 "$root/etc/netplan/01-tidalos-network-manager.yaml"
chroot "$root" systemctl enable lightdm.service NetworkManager.service
chroot "$root" systemctl set-default graphical.target
printf 'NAME=TIDALOS\nVERSION=0.1.0\nBASE=Ubuntu-24.04\nCHANNEL=live-alpha\nIMAGE_BUILD=r%s\n' "$image_revision" > "$root/etc/tidalos-release"
# Keep Ubuntu's os-release intact so repositories and upstream tools identify the base correctly.
mkdir -p "$root/etc/initramfs-tools/hooks" "$root/var/crash"
install -m 755 "$repo/config/tidalos-initramfs-hook" "$root/etc/initramfs-tools/hooks/tidalos-live"
chroot "$root" update-initramfs -u -k all
chroot "$root" apt-get clean
rm -f "$root/usr/sbin/policy-rc.d"
truncate -s 0 "$root/etc/machine-id"
rm -f "$root/var/lib/dbus/machine-id"
ln -s /etc/machine-id "$root/var/lib/dbus/machine-id"
mkdir -p "$iso/casper" "$iso/boot/grub" "$iso/.disk"
kernel=$(find "$root/boot" -maxdepth 1 -type f -name 'vmlinuz-*' | sort -V | tail -n 1)
[[ -n $kernel ]] || { echo 'No kernel found.' >&2; exit 1; }
kernel_version=${kernel##*/vmlinuz-}
cp "$kernel" "$iso/casper/vmlinuz"
cp "$root/boot/initrd.img-$kernel_version" "$iso/casper/initrd"
printf 'TIDALOS 0.1.0 Live Alpha amd64 - Build r%s\n' "$image_revision" > "$iso/.disk/info"
printf 'full_cd/single\n' > "$iso/.disk/cd_type"
cat > "$iso/boot/grub/grub.cfg" <<'GRUB'
set default=0
set timeout=5
if loadfont unicode; then
  insmod all_video
  terminal_output gfxterm
fi
set menu_color_normal=light-cyan/black
set menu_color_highlight=black/light-cyan
menuentry "TIDALOS 0.1 - Live Desktop (Build r4)" {
  linux /casper/vmlinuz boot=casper username=tidal hostname=tidalos locale=de_DE.UTF-8 keyboard-configuration/layoutcode=de nopersistent quiet console=tty0 console=ttyS0,115200 ---
  initrd /casper/initrd
}
menuentry "TIDALOS - Compatibility graphics" {
  linux /casper/vmlinuz boot=casper username=tidal hostname=tidalos locale=de_DE.UTF-8 keyboard-configuration/layoutcode=de nopersistent nomodeset console=tty0 console=ttyS0,115200 ---
  initrd /casper/initrd
}
GRUB
chroot "$root" dpkg-query -W --showformat='${Package} ${Version}\n' > "$iso/casper/filesystem.manifest"
cp "$iso/casper/filesystem.manifest" "$repo/dist/packages.manifest"
cp "$repo/README.md" "$iso/README.md"
cp "$repo/LICENSE" "$iso/LICENSE"
mkdir -p "$iso/docs"
cp "$repo/docs/BUILD.md" "$iso/docs/BUILD.md"
cp "$repo/docs/ROADMAP.md" "$iso/docs/ROADMAP.md"
cleanup
du -sx --block-size=1 "$root" | cut -f1 > "$iso/casper/filesystem.size"
mksquashfs "$root" "$iso/casper/filesystem.squashfs" -noappend -comp zstd -Xcompression-level 10 -processors 4 -wildcards -e 'tmp/*' 'var/cache/apt/archives/*' 'var/lib/apt/lists/*' 'var/log/*'
for branding_path in \
  etc/calamares/branding/tidalos/branding.desc \
  usr/share/calamares/branding/tidalos/branding.desc; do
  unsquashfs -cat "$iso/casper/filesystem.squashfs" "$branding_path" > "$work/branding-from-squashfs.desc"
  if ! cmp -s "$repo/config/calamares/branding.desc" "$work/branding-from-squashfs.desc"; then
    echo "Built live filesystem has stale Calamares branding at $branding_path." >&2
    exit 1
  fi
done
for slideshow_path in \
  etc/calamares/branding/tidalos/show.qml \
  usr/share/calamares/branding/tidalos/show.qml; do
  unsquashfs -cat "$iso/casper/filesystem.squashfs" "$slideshow_path" > "$work/show-from-squashfs.qml"
  if ! cmp -s "$repo/config/calamares/show.qml" "$work/show-from-squashfs.qml"; then
    echo "Built live filesystem has a missing or stale Calamares slideshow at $slideshow_path." >&2
    exit 1
  fi
done
rm -f "$work/branding-from-squashfs.desc" "$work/show-from-squashfs.qml"
(cd "$iso" && find . -type f ! -name md5sum.txt -print0 | sort -z | xargs -0 md5sum > md5sum.txt)
grub-mkrescue -o "$repo/dist/tidalos-${version}-amd64-r${image_revision}.iso" "$iso" -- -volid TIDALOS_010
cd "$repo/dist"
sha256sum "tidalos-${version}-amd64-r${image_revision}.iso" > SHA256SUMS
printf '\nBuilt %s/dist/tidalos-%s-amd64-r%s.iso\n' "$repo" "$version" "$image_revision"
