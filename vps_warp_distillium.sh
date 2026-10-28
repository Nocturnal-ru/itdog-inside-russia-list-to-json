#!/usr/bin/env bash
# Native WireGuard WARP interface for Debian/Ubuntu VPS.
# Inspired by https://github.com/distillium/warp-native (MIT license).
# WARP registration and endpoint selection are handled externally by warpscout.
set -Eeuo pipefail
umask 077

IFACE="distillium"
TARGET="/etc/wireguard/${IFACE}.conf"
UNIT="wg-quick@${IFACE}.service"
SOURCE=""
REPLACE=0

usage() {
    cat <<'EOF'
Usage: bash vps_warp_distillium.sh [--config /path/to/warpscout.conf] [--replace]

Without --config, uses an existing /etc/wireguard/distillium.conf.
--replace  Allow replacing an existing config with a different --config file.

Requires root, systemd and Debian/Ubuntu with apt-get.
The installer forces Table = off and omits DNS from the interface config.
It never registers a WARP account or changes the VPS default route.
EOF
}

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
log()  { printf '==> %s\n' "$*"; }

while (($#)); do
    case "$1" in
        --config)
            (($# >= 2)) || fail 'Missing file after --config'
            SOURCE="$2"; shift 2 ;;
        --replace) REPLACE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; fail "Unknown argument: $1" ;;
    esac
done

[[ $EUID -eq 0 ]] || fail 'Run as root.'
[[ -d /run/systemd/system ]] || fail 'systemd is required.'
[[ -r /etc/os-release ]] || fail 'Cannot detect OS.'
# shellcheck disable=SC1091
. /etc/os-release
case "${ID:-}" in
    debian|ubuntu) ;;
    *) fail 'Only Debian and Ubuntu are supported.' ;;
esac
command -v apt-get >/dev/null || fail 'apt-get is required.'
[[ ! -L "$TARGET" ]] || fail "Refusing to replace a symlink: $TARGET"

if [[ -z "$SOURCE" ]]; then
    SOURCE="$TARGET"
    [[ -f "$SOURCE" ]] || fail "No configuration found. Provide --config /path/to/warpscout.conf"
else
    [[ -f "$SOURCE" && -r "$SOURCE" ]] || fail "Cannot read config: $SOURCE"
fi

TMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TMP_DIR"' EXIT
STAGED="$TMP_DIR/${IFACE}.conf"

# Accept only standard WireGuard keys. Do not execute arbitrary wg-quick hooks.
# Keep warpscout endpoint, keys, MTU, AllowedIPs and keepalive unchanged.
awk '
function die(message) { print "Invalid WireGuard config: " message > "/dev/stderr"; bad = 1; exit 1 }
{
    sub(/\r$/, "")
    line = $0
    sub(/^[[:space:]]+/, "", line)
    sub(/[[:space:]]+$/, "", line)
    if (line == "" || line ~ /^#/) { print; next }
    if (line == "[Interface]") {
        if (section != "" || got_interface++) die("duplicate/out-of-order [Interface]")
        section = "interface"
        print "[Interface]"
        print "Table = off"
        next
    }
    if (line == "[Peer]") {
        if (section != "interface" || got_peer++) die("expected one [Peer] after [Interface]")
        section = "peer"
        print "[Peer]"
        next
    }
    if (line ~ /^\[/) die("unknown section")
    n = index(line, "=")
    if (!n || section == "") die("malformed option or missing section")
    key = substr(line, 1, n-1)
    value = substr(line, n+1)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
    if (value == "") die("empty value for " key)
    if (section == "interface") {
        if (key == "Table" || key == "DNS") next
        if (key == "PrivateKey") got_private = 1
        else if (key == "Address") got_address = 1
        else if (key !~ /^(MTU|ListenPort|FwMark)$/) die("unsupported [Interface] option: " key)
    } else {
        if (key == "PublicKey") got_public = 1
        else if (key == "AllowedIPs") got_allowed = 1
        else if (key == "Endpoint") got_endpoint = 1
        else if (key !~ /^(PresharedKey|PersistentKeepalive)$/) die("unsupported [Peer] option: " key)
    }
    print
}
END {
    if (!bad && (!got_interface || !got_peer || !got_private || !got_address || !got_public || !got_allowed || !got_endpoint)) {
        print "Invalid WireGuard config: required Interface/Peer fields are missing" > "/dev/stderr"
        exit 1
    }
}
' "$SOURCE" > "$STAGED" || fail 'Config validation failed.'
chmod 600 "$STAGED"

if ! command -v wg >/dev/null || ! command -v wg-quick >/dev/null; then
    log 'Installing wireguard-tools (no wgcf, no warp-cli, no nftables changes)...'
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y wireguard-tools iproute2
fi
command -v wg >/dev/null && command -v wg-quick >/dev/null || fail 'WireGuard tools unavailable.'
wg-quick strip "$STAGED" >/dev/null || fail 'wg-quick could not parse the config.'

mkdir -p /etc/wireguard
chmod 700 /etc/wireguard
HAD_CONFIG=0
CHANGED=1
BACKUP=""
if [[ -f "$TARGET" ]]; then
    HAD_CONFIG=1
    if cmp -s "$STAGED" "$TARGET"; then CHANGED=0; fi
    if ((CHANGED)) && [[ "$SOURCE" != "$TARGET" ]] && (( ! REPLACE )); then
        fail "Existing $TARGET differs. Use --replace to back it up and replace it."
    fi
fi

if ((CHANGED)); then
    if ((HAD_CONFIG)); then
        BACKUP=$(mktemp "${TARGET}.bak.$(date +%Y%m%d-%H%M%S).XXXXXX")
        cp -p -- "$TARGET" "$BACKUP"
        chmod 600 "$BACKUP"
        log "Saved backup: $BACKUP"
    fi
    install -m 600 "$STAGED" "$TARGET"
    log "Saved: $TARGET (Table = off; no DNS override)"
else
    chmod 600 "$TARGET"
    log 'Configuration unchanged.'
fi

WAS_ACTIVE=0
systemctl is-active --quiet "$UNIT" && WAS_ACTIVE=1
if ((CHANGED && WAS_ACTIVE)); then
    log "Restarting $UNIT ..."
    if ! systemctl restart "$UNIT"; then
        log 'New configuration failed; restoring previous configuration.'
        if ((HAD_CONFIG)); then install -m 600 "$BACKUP" "$TARGET"; else rm -f "$TARGET"; fi
        systemctl start "$UNIT" || true
        fail 'Service restart failed; check journalctl -u wg-quick@distillium.'
    fi
elif (( ! WAS_ACTIVE )); then
    log "Starting $UNIT ..."
    if ! systemctl start "$UNIT"; then
        log 'Startup failed; restoring previous configuration (if any).'
        if ((CHANGED)); then
            if ((HAD_CONFIG)); then install -m 600 "$BACKUP" "$TARGET"; else rm -f "$TARGET"; fi
        fi
        fail 'Service start failed; check journalctl -u wg-quick@distillium.'
    fi
fi
systemctl enable "$UNIT" >/dev/null
log "Enabled: $UNIT"
wg show "$IFACE" || fail 'Service started, but WireGuard interface is not visible.'
log 'Done. Table = off leaves the VPS default route unchanged.'
