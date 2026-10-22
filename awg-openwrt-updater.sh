#!/bin/sh
# Update already installed AmneziaWG packages from Slava-Shchipunov/awg-openwrt.
# OpenWrt 24.10 and earlier (opkg / .ipk). Does not alter UCI settings.
set -eu

UPSTREAM='https://github.com/Slava-Shchipunov/awg-openwrt/releases/download'
BACKUP_ROOT='/root/awg-backups'
DO_BACKUP=1
CHECK_ONLY=0
ASSUME_YES=0
WORK_DIR=''

usage() {
    cat <<'EOF'
Usage: sh awg-openwrt-updater.sh [options]
  -c, --check           Check available versions and dependencies; do not install
  -y, --yes             Do not ask for confirmation
  -b, --backup          Save configuration backup (default)
  -n, --no-backup       Skip configuration backup
      --backup-dir DIR  Backup directory (default: /root/awg-backups)
  -h, --help            Show this help

Only updates packages that are already installed. Requires opkg (IPK).
Does not support OpenWrt 25.x (APK) or reboot automatically.
EOF
}

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
log() { printf '%s\n' "$*"; }
cleanup() { [ -z "$WORK_DIR" ] || rm -rf "$WORK_DIR"; }
trap cleanup 0
trap 'exit 1' 1 2 3 15

while [ "$#" -gt 0 ]; do
    case "$1" in
        -c|--check) CHECK_ONLY=1 ;;
        -y|--yes) ASSUME_YES=1 ;;
        -b|--backup) DO_BACKUP=1 ;;
        -n|--no-backup) DO_BACKUP=0 ;;
        --backup-dir)
            [ "$#" -ge 2 ] || fail '--backup-dir requires a path'
            BACKUP_ROOT=$2
            shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; fail "Unknown option: $1" ;;
    esac
    shift
done

[ "$(id -u)" -eq 0 ] || fail 'Run as root'
command -v opkg >/dev/null 2>&1 || fail 'Only OpenWrt with opkg is supported (not apk)'
for cmd in ubus jsonfilter wget tar awk grep mktemp; do
    command -v "$cmd" >/dev/null 2>&1 || fail "Missing command: $cmd"
done
case "$BACKUP_ROOT" in /*) ;; *) fail 'Backup path must be absolute' ;; esac

log 'AmneziaWG updater: detecting OpenWrt platform...'
BOARD=$(ubus call system board) || fail 'Cannot query OpenWrt board'
# Not every OpenWrt version exposes release.arch through ubus. With set -e
# a failed jsonfilter previously caused a silent early exit.
FW_VERSION=$(printf '%s\n' "$BOARD" | jsonfilter -e '@.release.version' 2>/dev/null) \
    || fail 'Cannot determine OpenWrt version'
TARGET_FULL=$(printf '%s\n' "$BOARD" | jsonfilter -e '@.release.target' 2>/dev/null) \
    || fail 'Cannot determine OpenWrt target'
PKG_ARCH=$(printf '%s\n' "$BOARD" | jsonfilter -e '@.release.arch' 2>/dev/null) || PKG_ARCH=''
if [ -z "$PKG_ARCH" ]; then
    log 'ubus release.arch is unavailable; using opkg print-architecture.'
    PKG_ARCH=$(opkg print-architecture | awk '$1 == "arch" && $2 != "all" && $2 != "noarch" && $3 + 0 > max { max = $3 + 0; arch = $2 } END { print arch }') \
        || fail 'Cannot read opkg architectures'
fi
case "$FW_VERSION" in ''|*[!0-9.]*) fail 'Invalid OpenWrt version' ;; esac
case "$PKG_ARCH" in ''|*[!a-zA-Z0-9_-]*) fail 'Invalid package architecture' ;; esac
case "$TARGET_FULL" in
    */*) TARGET=${TARGET_FULL%%/*}; SUBTARGET=${TARGET_FULL#*/} ;;
    *) fail 'Missing target/subtarget' ;;
esac
case "$TARGET$SUBTARGET" in ''|*[!a-zA-Z0-9_-]*) fail 'Invalid target/subtarget' ;; esac
case "$FW_VERSION" in 2[0-4].*|1[0-9].*) ;; *) fail 'This script is for OpenWrt 24.x and older with opkg' ;; esac

WORK_DIR=$(mktemp -d /tmp/awg-update.XXXXXX) || fail 'Cannot create temp directory'
umask 077
opkg list-installed > "$WORK_DIR/installed.txt" || fail 'Cannot list installed packages'

installed_version() {
    awk -v name="$1" '$1 == name && $2 == "-" { print $3; exit }' "$WORK_DIR/installed.txt"
}

# OpenWrt IPK: gzip(tar(./control.tar.gz, ./data.tar.gz, ...)).
# Verify the package name, version and architecture before installation.
read_control() {
    pkg=$1
    file=$2
    tar -xzOf "$file" ./control.tar.gz > "$WORK_DIR/control.tar.gz" \
        || fail "Invalid IPK archive: $pkg"
    tar -xzOf "$WORK_DIR/control.tar.gz" ./control > "$WORK_DIR/control" \
        || fail "Invalid IPK control data: $pkg"
    got_name=$(awk -F ': ' '$1 == "Package" {print $2; exit}' "$WORK_DIR/control")
    got_version=$(awk -F ': ' '$1 == "Version" {print $2; exit}' "$WORK_DIR/control")
    got_arch=$(awk -F ': ' '$1 == "Architecture" {print $2; exit}' "$WORK_DIR/control")
    [ "$got_name" = "$pkg" ] || fail "Unexpected package: $got_name (expected $pkg)"
    [ -n "$got_version" ] || fail "Missing package version: $pkg"
    case "$got_arch" in all|"$PKG_ARCH") ;; *) fail "Package architecture mismatch: $pkg ($got_arch)" ;; esac
    printf '%s\n' "$got_version"
}

# Update *only* installed packages. Existing LuCI package type is preserved.
LUCI=''
if [ -n "$(installed_version luci-proto-amneziawg)" ]; then
    LUCI='luci-proto-amneziawg'
elif [ -n "$(installed_version luci-app-amneziawg)" ]; then
    LUCI='luci-app-amneziawg'
fi
[ -n "$LUCI" ] || fail 'Neither luci-proto-amneziawg nor luci-app-amneziawg is installed'
for pkg in kmod-amneziawg amneziawg-tools "$LUCI"; do
    [ -n "$(installed_version "$pkg")" ] || fail "Required package not installed: $pkg"
done

log "OpenWrt $FW_VERSION; $TARGET_FULL; $PKG_ARCH"
log 'Installed packages:'
for pkg in kmod-amneziawg amneziawg-tools "$LUCI" luci-i18n-amneziawg-ru; do
    old=$(installed_version "$pkg")
    [ -z "$old" ] || log "  $pkg: $old"
done

# Optional translation is updated only if already installed.
PKGS="kmod-amneziawg amneziawg-tools $LUCI"
if [ -n "$(installed_version luci-i18n-amneziawg-ru)" ]; then
    PKGS="$PKGS luci-i18n-amneziawg-ru"
fi

BASE_URL="$UPSTREAM/v$FW_VERSION"
SUFFIX="_v${FW_VERSION}_${PKG_ARCH}_${TARGET}_${SUBTARGET}.ipk"
: > "$WORK_DIR/plan"
for pkg in $PKGS; do
    file="$WORK_DIR/$pkg.ipk"
    url="$BASE_URL/$pkg$SUFFIX"
    log "Downloading $pkg..."
    wget -q -O "$file" "$url" && [ -s "$file" ] \
        || fail "Cannot download $url"
    old=$(installed_version "$pkg")
    new=$(read_control "$pkg" "$file")
    if opkg compare-versions "$old" '<<' "$new"; then
        log "  UPDATE: $old -> $new"
        printf '%s|%s|%s\n' "$pkg" "$old" "$new" >> "$WORK_DIR/plan"
    elif opkg compare-versions "$old" '=' "$new"; then
        log "  Up to date: $old"
    else
        fail "Refusing downgrade of $pkg: installed $old, release $new"
    fi
done

[ -s "$WORK_DIR/plan" ] || { log 'All installed AmneziaWG packages are up to date.'; exit 0; }

# Only pass outdated packages to opkg; it checks kernel ABI and other dependencies.
set --
while IFS='|' read -r pkg old new; do
    set -- "$@" "$WORK_DIR/$pkg.ipk"
done < "$WORK_DIR/plan"

log 'Checking dependencies and conflicts (opkg --noaction)...'
if ! opkg --noaction install "$@" > "$WORK_DIR/preflight.log" 2>&1; then
    cat "$WORK_DIR/preflight.log" >&2
    fail 'Preflight failed. Nothing was installed.'
fi
log 'Dependency check passed.'

[ "$CHECK_ONLY" -eq 0 ] || { log 'Check-only mode: no changes made.'; exit 0; }

if [ "$ASSUME_YES" -eq 0 ]; then
    printf 'Upgrade listed packages? [y/N]: '
    read -r answer || fail 'No confirmation received'
    case "$answer" in y|Y|yes|YES) ;; *) log 'Cancelled.'; exit 0 ;; esac
fi

if [ "$DO_BACKUP" -eq 1 ]; then
    mkdir -p "$BACKUP_ROOT" || fail 'Cannot create backup root'
    stamp=$(date +%Y%m%d-%H%M%S)
    backup="$BACKUP_ROOT/awg-$stamp-$$"
    mkdir -m 700 "$backup" || fail 'Cannot create backup directory'
    files='etc/config/network etc/config/firewall'
    [ -f /etc/config/podkop ] && files="$files etc/config/podkop"
    [ -f /etc/config/pbr ] && files="$files etc/config/pbr"
    # These UCI files may contain private keys: keep the backup root-only.
    # Word splitting is intentional for the fixed list of path names above.
    # shellcheck disable=SC2086
    tar -czf "$backup/config.tar.gz" -C / $files \
        || fail 'Configuration backup failed. No packages installed.'
    cp "$WORK_DIR/installed.txt" "$backup/packages-before.txt" \
        || fail 'Cannot save installed package list'
    printf '%s\n' "$BOARD" > "$backup/board.json"
    cp "$WORK_DIR/plan" "$backup/update-plan.txt"
    log "Configuration backup saved to: $backup"
else
    log 'WARNING: Configuration backup disabled.'
fi

log 'Installing updated packages...'
if ! opkg install "$@"; then
    fail 'Package install failed. Inspect opkg status; packages may be partially upgraded.'
fi

log 'Installed versions after upgrade:'
opkg list-installed | grep -E '^(kmod-amneziawg|amneziawg-tools|luci-(proto|app|i18n)-amneziawg)' || true
failed=0
while IFS='|' read -r pkg old new; do
    actual=$(opkg list-installed | awk -v name="$pkg" '$1 == name && $2 == "-" {print $3; exit}')
    if [ "$actual" != "$new" ]; then
        log "WARNING: $pkg expected $new, found ${actual:-not installed}"
        failed=1
    fi
done < "$WORK_DIR/plan"
[ "$failed" -eq 0 ] || fail 'One or more installed versions differ from expected versions'

log 'Upgrade successful. UCI config was not modified.'
if grep -q '^kmod-amneziawg|' "$WORK_DIR/plan"; then
    log 'Kernel module was updated: schedule a controlled reboot, then verify AWG handshake.'
else
    log 'Verify AWG handshake and traffic before considering the update complete.'
fi
