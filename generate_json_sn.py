# генерируем subnets.json/subnets.lst/Noc из Discord.lst/itdog + Meta.lst/itdog + Twitter.lst/itdog + custom-subnets.lst/Noc
import requests
import json
import sys

# Ссылки на списки IP-адресов
URLS = [
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/Discord.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/Meta.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/Twitter.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/cloudflare.lst",
    "https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/custom-subnets.lst"
]
OUTPUT_FILE_JSON = "subnets.json"
OUTPUT_FILE_LST = "subnets.lst"

# Шаблон JSON-структуры
TEMPLATE = {
    "version": 1,
    "rules": [
        {"ip_cidr": []}
    ]
}

def fetch_ips(urls):
    try:
        all_ips = []
        for url in urls:
            print(f"Fetching IPs from {url}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # Проверяем, JSON это или текст
            if url.endswith('.json'):
                data = response.json()
                # Предполагаем, что в JSON есть поле "rules" с "ip_cidr"
                ips = data["rules"][0]["ip_cidr"]
            else:
                ips = response.text.splitlines()
            all_ips.extend([ip.strip() for ip in ips if ip.strip()])  # Фильтруем пустые строки
        
        if not all_ips:
            raise ValueError("All fetched IP lists are empty.")
        return all_ips
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IPs: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error in JSON structure: missing key {e}")
        sys.exit(1)

def update_json_template(ips):
    # Обновляем шаблон списком IP-адресов
    TEMPLATE["rules"][0]["ip_cidr"] = ips
    return TEMPLATE

def save_lst_file(ips, output_file):
    try:
        with open(output_file, "w") as f:
            for ip in ips:
                f.write(f"{ip}\n")
        print(f"LST file generated successfully: {output_file}")
    except IOError as e:
        print(f"Error saving LST file: {e}")
        sys.exit(1)

def main():
    try:
        print("Fetching IP lists...")
        ips = fetch_ips(URLS)
        print(f"Fetched {len(ips)} IP addresses total.")

        print("Updating JSON template...")
        updated_json = update_json_template(ips)

        with open(OUTPUT_FILE_JSON, "w") as f:
            json.dump(updated_json, f, indent=4)
        print(f"JSON file generated successfully: {OUTPUT_FILE_JSON}")

        print("Generating LST file...")
        save_lst_file(ips, OUTPUT_FILE_LST)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
