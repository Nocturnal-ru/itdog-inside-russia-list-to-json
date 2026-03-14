#!/usr/bin/env python3
"""
Генератор geoip_noc.dat в формате geoip.dat (xray/v2ray protobuf).
Без внешних зависимостей — только стандартная библиотека Python.
"""

import urllib.request
import ipaddress

# ──────────────────────────────────────────────
# Источники: (тег_в_dat, url)
# ──────────────────────────────────────────────
SOURCES = [
    ("DISCORD",      "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/Discord.lst"),
    ("CLOUDFLARE",   "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/cloudflare.lst"),
    ("CLOUDFRONT",   "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/cloudfront.lst"),
    ("DIGITALOCEAN", "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/digitalocean.lst"),
    ("HETZNER",      "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/hetzner.lst"),
    ("META",         "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/meta.lst"),
    ("OVH",          "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/ovh.lst"),
    ("ROBLOX",       "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/roblox.lst"),
    ("TELEGRAM",     "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/telegram.lst"),
    ("TWITTER",      "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/twitter.lst"),
    ("MYGEOIPBLOCK", "https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/refs/heads/main/cats/mygeoipblock.lst"),
]

OUTPUT_FILE = "geoip_noc.dat"

# ──────────────────────────────────────────────
# Минимальный protobuf encoder (без библиотек)
# ──────────────────────────────────────────────

def varint(value: int) -> bytes:
    """Кодирует целое число в формат protobuf varint."""
    result = b""
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            result += bytes([bits | 0x80])
        else:
            result += bytes([bits])
            break
    return result

def field_bytes(field_num: int, data: bytes) -> bytes:
    """Поле wire type 2 (length-delimited): строки, байты, вложенные сообщения."""
    tag = varint((field_num << 3) | 2)
    return tag + varint(len(data)) + data

def field_varint(field_num: int, value: int) -> bytes:
    """Поле wire type 0 (varint): числа."""
    tag = varint((field_num << 3) | 0)
    return tag + varint(value)

def encode_cidr(ip_bytes: bytes, prefix: int) -> bytes:
    """
    Сообщение CIDR:
      field 1 = ip   (bytes)
      field 2 = prefix (uint32)
    """
    msg = field_bytes(1, ip_bytes) + field_varint(2, prefix)
    return field_bytes(2, msg)   # обёрнуто как field 2 внутри GeoIP

def encode_geoip(country_code: str, cidrs: list) -> bytes:
    """
    Сообщение GeoIP (одна запись в GeoIPList):
      field 1 = country_code (string)
      field 2 = cidr[]       (repeated CIDR)
    Обёрнуто как field 1 в GeoIPList.
    """
    msg = field_bytes(1, country_code.encode("utf-8"))
    for ip_bytes, prefix in cidrs:
        cidr_inner = field_bytes(1, ip_bytes) + field_varint(2, prefix)
        msg += field_bytes(2, cidr_inner)
    return field_bytes(1, msg)   # field 1 = entry в GeoIPList

# ──────────────────────────────────────────────
# Основная логика
# ──────────────────────────────────────────────

def download(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")

def parse_cidrs(text: str) -> list:
    """Парсит текстовый список подсетей, пропускает комментарии и пустые строки."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            net = ipaddress.ip_network(line, strict=False)
            result.append((net.network_address.packed, net.prefixlen))
        except ValueError:
            print(f"  [SKIP] не удалось распарсить: {line!r}")
    return result

def main():
    output = b""

    for tag, url in SOURCES:
        print(f"[{tag}] загрузка {url}")
        try:
            text = download(url)
        except Exception as e:
            print(f"  [ERROR] {e} — пропускаем")
            continue

        cidrs = parse_cidrs(text)
        print(f"  → {len(cidrs)} подсетей")

        output += encode_geoip(tag, cidrs)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(output)

    print(f"\nГотово: {OUTPUT_FILE} ({len(output)} байт)")

if __name__ == "__main__":
    main()
