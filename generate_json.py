import requests
import json

# Ссылка на список доменов
URL = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"
OUTPUT_FILE = "inside-russia.json"

def fetch_domains(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

def generate_json(domains):
    return {
        "version": 1,
        "rules": [
            {"ip_cidr": ["160.79.104.0/23"]},
            {"domain_suffix": domains},
        ]
    }

def main():
    try:
        domains = fetch_domains(URL)
        json_data = generate_json(domains)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(json_data, f, indent=4)

        print(f"JSON file generated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
