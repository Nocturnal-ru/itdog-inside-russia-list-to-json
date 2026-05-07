#!/usr/bin/env python3
"""
Конвертирует .lst файлы из cats/ в singbox JSON формат (version 3) в папку json/.
Строки автоматически разделяются на домены и IP/CIDR по содержимому.
"""

import json
import os
import ipaddress
import glob

CATS_DIR = "cats"
JSON_DIR = "json"


def is_ip_or_cidr(value: str) -> bool:
    """Возвращает True если строка — IP-адрес или CIDR-сеть."""
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def parse_lst(path: str) -> dict:
    """Читает .lst файл, возвращает singbox-совместимый dict."""
    domains = []
    ip_cidrs = []

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith("#"):
                continue
            if is_ip_or_cidr(line):
                ip_cidrs.append(line)
            else:
                domains.append(line)

    rule = {}
    if domains:
        rule["domain_suffix"] = domains
    if ip_cidrs:
        rule["ip_cidr"] = ip_cidrs

    return {
        "version": 3,
        "rules": [rule] if rule else []
    }


def main():
    os.makedirs(JSON_DIR, exist_ok=True)

    lst_files = sorted(glob.glob(os.path.join(CATS_DIR, "*.lst")))

    if not lst_files:
        print(f"[!] Нет .lst файлов в {CATS_DIR}/")
        return

    for lst_path in lst_files:
        basename = os.path.splitext(os.path.basename(lst_path))[0]
        json_path = os.path.join(JSON_DIR, f"{basename}.json")

        try:
            data = parse_lst(lst_path)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            rule = data["rules"][0] if data["rules"] else {}
            d_count = len(rule.get("domain_suffix", []))
            ip_count = len(rule.get("ip_cidr", []))
            print(f"[OK] {lst_path} -> {json_path}  (домены: {d_count}, IP/CIDR: {ip_count})")
        except Exception as e:
            print(f"[ERR] {lst_path}: {e}")


if __name__ == "__main__":
    main()
