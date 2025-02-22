import requests
import json
import sys

# URLs исходных файлов
INSIDE_RUSSIA_URL = "https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/inside-russia.json"
CUSTOM_RULES_URL = "https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/custom-rules.json"
EXCLUDE_RULES_URL = "https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/exclude.json"
OUTPUT_FILE = "custom-rules.lst"

# Константы для формата вывода
NFT_PREFIX = "nftset=/"
NFT_SUFFIX = "/4#inet#fw4#vpn_domains"

def fetch_json(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching JSON from {url}: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {url}: {e}")
        sys.exit(1)

def merge_json_data(inside_russia_data, custom_rules_data, exclude_data):
    # Получаем все domain_suffix из обоих файлов
    domains = set()
    
    # Извлекаем домены из inside-russia.json
    for rule in inside_russia_data.get("rules", []):
        if "domain_suffix" in rule:
            domains.update(rule["domain_suffix"])
    
    # Добавляем домены из custom-rules.json
    for rule in custom_rules_data.get("rules", []):
        if "domain_suffix" in rule:
            domains.update(rule["domain_suffix"])
    
    # Получаем домены, которые нужно исключить
    exclude_domains = set()
    for rule in exclude_data.get("rules", []):
        if "domain_suffix" in rule:
            exclude_domains.update(rule["domain_suffix"])
    
    # Исключаем домены из списка
    domains.difference_update(exclude_domains)
    
    # Сортируем домены по алфавиту
    return sorted(list(domains))

def save_lst_file(domains, output_file):
    try:
        with open(output_file, 'w') as f:
            for domain in domains:
                # Форматируем каждую строку в требуемом формате
                formatted_line = f"{NFT_PREFIX}{domain}{NFT_SUFFIX}\n"
                f.write(formatted_line)
        print(f"LST file generated successfully: {output_file}")
    except IOError as e:
        print(f"Error saving LST file: {e}")
        sys.exit(1)

def main():
    try:
        print("Fetching inside-russia.json...")
        inside_russia_data = fetch_json(INSIDE_RUSSIA_URL)
        
        print("Fetching custom-rules.json...")
        custom_rules_data = fetch_json(CUSTOM_RULES_URL)
        
        print("Fetching exclude.json...")
        exclude_data = fetch_json(EXCLUDE_RULES_URL)
        
        print("Merging domain lists...")
        merged_domains = merge_json_data(inside_russia_data, custom_rules_data, exclude_data)
        print(f"Total unique domains after exclusion: {len(merged_domains)}")
        
        print("Generating LST file...")
        save_lst_file(merged_domains, OUTPUT_FILE)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
