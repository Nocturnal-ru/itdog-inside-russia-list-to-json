import json
import urllib.request
from pathlib import Path

# -------------------------------------------------------
# Список источников — добавляй сюда новые URL по мере надобности
SOURCES = [
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Russia/inside-raw.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Categories/hodca.lst",
]

CUSTOM_RULES_FILE = "custom-rules.json"
OUTPUT_FILE = "delta.lst"
# -------------------------------------------------------


def fetch_domains(url: str) -> set[str]:
    """Скачивает plain-text список доменов, возвращает множество."""
    with urllib.request.urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8")
    domains = set()
    for line in text.splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            domains.add(line)
    return domains


def load_custom_domains(filepath: str) -> list[str]:
    """Извлекает domain_suffix из custom-rules.json, игнорирует ip_cidr."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    domains = []
    for rule in data.get("rules", []):
        domains.extend(rule.get("domain_suffix", []))
    return domains


def main():
    # 1. Скачиваем и объединяем все источники
    print("Fetching source lists...")
    merged = set()
    for url in SOURCES:
        print(f"  -> {url}")
        fetched = fetch_domains(url)
        print(f"     {len(fetched)} domains")
        merged |= fetched
    print(f"Total merged: {len(merged)} unique domains\n")

    # 2. Загружаем custom-rules.json
    custom_domains = load_custom_domains(CUSTOM_RULES_FILE)
    print(f"Custom domains (domain_suffix): {len(custom_domains)}\n")

    # 3. Находим домены из custom-rules, которых нет в merged
    delta = [d for d in custom_domains if d.lower() not in merged]

    # 4. Записываем delta.lst
    Path(OUTPUT_FILE).write_text("\n".join(delta) + "\n", encoding="utf-8")
    print(f"Delta (absent in sources): {len(delta)} domains")
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
