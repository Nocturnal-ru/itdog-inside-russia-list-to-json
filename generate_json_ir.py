import requests
import json
import sys

# Ссылка на список доменов
URL = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"
OUTPUT_FILE = "inside-russia.json"

# Шаблон JSON-структуры
TEMPLATE = {
    "version": 1,
    "rules": [        
        {"domain_suffix": []}  # Список доменов будет добавлен сюда
    ]
}

def fetch_domains(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        domains = response.text.splitlines()
        if not domains:
            raise ValueError("Fetched domain list is empty.")
        return domains
    except requests.exceptions.RequestException as e:
        print(f"Error fetching domains: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

def update_json_template(domains):
    # Обновляем шаблон только списком доменов
    TEMPLATE["rules"][0]["domain_suffix"] = domains
    return TEMPLATE

def main():
    try:
        print("Fetching domain list...")
        domains = fetch_domains(URL)
        print(f"Fetched {len(domains)} domains.")

        print("Updating JSON template...")
        updated_json = update_json_template(domains)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(updated_json, f, indent=4)

        print(f"JSON file generated successfully: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

