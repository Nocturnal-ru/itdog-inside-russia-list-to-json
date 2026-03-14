#!/usr/bin/env python3
"""
Сборщик geosite_noc.dat для xray/v2ray из списков доменов.

Чтобы добавить новый источник — добавь словарь в список SOURCES:
  {
      "url":  "https://...",   # URL списка доменов
      "tag":  "mytag",         # тег в итоговом .dat файле
  }
Несколько источников с одинаковым тегом объединяются в один блок.
"""

import sys
import urllib.request
from collections import defaultdict

# ──────────────────────────────────────────────────────────────
# ИСТОЧНИКИ — редактируй только этот блок
# ──────────────────────────────────────────────────────────────
SOURCES = [
    {
        "url": (
            "https://raw.githubusercontent.com/Nocturnal-ru/"
            "itdog-inside-russia-list-to-json/refs/heads/main/"
            "cats/mygeositeblock.lst"
        ),
        "tag": "mygeositeblock",
    },
    # Пример добавления второго списка:
    # {
    #     "url": "https://example.com/another-list.lst",
    #     "tag": "another_tag",
    # },
]

OUTPUT_FILE = "geosite_noc.dat"
# ──────────────────────────────────────────────────────────────


# ── Protobuf-кодирование (без внешних зависимостей) ──────────

def _varint(value: int) -> bytes:
    """Кодирует целое число в формат protobuf varint."""
    out = b""
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            out += bytes([bits | 0x80])
        else:
            out += bytes([bits])
            break
    return out


def _tag(field: int, wtype: int) -> bytes:
    return _varint((field << 3) | wtype)


def pb_varint_field(field: int, value: int) -> bytes:
    """Поле типа int32/enum (wire type 0)."""
    return _tag(field, 0) + _varint(value)


def pb_bytes_field(field: int, data: bytes) -> bytes:
    """Поле типа bytes/message (wire type 2)."""
    return _tag(field, 2) + _varint(len(data)) + data


def pb_string_field(field: int, value: str) -> bytes:
    """Поле типа string (wire type 2)."""
    return pb_bytes_field(field, value.encode("utf-8"))


# ── Кодирование структур geosite.dat ─────────────────────────
# Схема:
#   GeoSiteList { repeated GeoSite entry = 1; }
#   GeoSite     { string country_code = 1; repeated Domain domain = 2; }
#   Domain      { Type type = 1; string value = 2; }
#   Domain.Type: Plain=0(keyword), Regex=1, Domain=2(subdomain), Full=3

DOMAIN_TYPE = {"keyword": 0, "regexp": 1, "domain": 2, "full": 3}


def encode_domain(dtype: int, value: str) -> bytes:
    data = b""
    if dtype != 0:                            # 0 — дефолт, не пишем
        data += pb_varint_field(1, dtype)
    data += pb_string_field(2, value)
    return data


def encode_geosite(tag: str, domains: list) -> bytes:
    data = pb_string_field(1, tag.upper())    # country_code
    for dtype, value in domains:
        data += pb_bytes_field(2, encode_domain(dtype, value))
    return data


def encode_geosite_list(geosites: list) -> bytes:
    data = b""
    for gs in geosites:
        data += pb_bytes_field(1, gs)
    return data


# ── Загрузка и разбор списка ──────────────────────────────────

def download(url: str) -> str:
    print(f"  Загрузка: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "geosite-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_list(text: str) -> list:
    """
    Разбирает строки списка доменов.

    Форматы строк:
      domain:example.com   → subdomain-match (тип 2, по умолчанию)
      full:example.com     → exact-match     (тип 3)
      keyword:word         → keyword-match   (тип 0)
      regexp:pattern       → regex-match     (тип 1)
      example.com          → subdomain-match (тип 2)
      # комментарий        → пропуск
    """
    domains = []
    skipped = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            skipped += 1
            continue
        if ":" in line:
            prefix, _, value = line.partition(":")
            prefix = prefix.lower()
            if prefix in DOMAIN_TYPE:
                domains.append((DOMAIN_TYPE[prefix], value.strip()))
            else:
                # include: и прочие директивы — пропускаем
                print(f"    Пропуск директивы: {line}")
                skipped += 1
        else:
            domains.append((DOMAIN_TYPE["domain"], line))
    return domains, skipped


# ── Главная функция ───────────────────────────────────────────

def main():
    # Группируем домены по тегу (несколько источников → один тег)
    tag_domains: dict = defaultdict(list)

    for src in SOURCES:
        tag = src["tag"]
        try:
            text = download(src["url"])
            domains, skipped = parse_list(text)
            tag_domains[tag].extend(domains)
            print(f"  [{tag}] +{len(domains)} доменов, пропущено строк: {skipped}")
        except Exception as e:
            print(f"  ОШИБКА при загрузке {src['url']}: {e}", file=sys.stderr)
            sys.exit(1)

    if not tag_domains:
        print("Нет доменов для записи.", file=sys.stderr)
        sys.exit(1)

    geosites = []
    for tag, domains in tag_domains.items():
        print(f"  Кодирование тега [{tag}]: {len(domains)} доменов")
        geosites.append(encode_geosite(tag, domains))

    output = encode_geosite_list(geosites)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(output)

    print(f"\nГотово: {OUTPUT_FILE} ({len(output)} байт)")


if __name__ == "__main__":
    main()
