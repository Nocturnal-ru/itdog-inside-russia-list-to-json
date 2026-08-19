# itdog-inside-russia-list-to-json

Набор моих дополнительных списков и небольших скриптов для подготовки правил в форматах, используемых **sing-box / Xray / V2Ray**, а также для проверки пересечений с публичными списками [itdoginfo/allow-domains](https://github.com/itdoginfo/allow-domains).

Репозиторий используется в основном как источник автоматически обновляемых файлов для моих конфигураций.

## Основные файлы

### Пользовательские правила

* [`custom-rules.json`](custom-rules.json) — основной список моих дополнительных правил в JSON-формате sing-box (`version: 3`).
* [`cats/`](cats/) — отдельные пользовательские категории в формате `.lst`.
* [`json/`](json/) — автоматически сгенерированные JSON-версии всех файлов из `cats/`.

Прямой URL для `custom-rules.json`:

```text
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/custom-rules.json
```

### Проверка пересечений с itdoginfo/allow-domains

Скрипт [`scripts/check_ITDdomains.py`](scripts/check_ITDdomains.py) сравнивает `domain_suffix` из `custom-rules.json` со списками:

* `Russia/inside-raw.lst`
* `Categories/hodca.lst`

Результат:

* [`delta.lst`](delta.lst) — домены из `custom-rules.json`, которых нет в проверяемых списках itdoginfo;
* [`duplicates.lst`](duplicates.lst) — домены, которые уже присутствуют и в `custom-rules.json`, и в проверяемых списках itdoginfo.

Прямые URL:

```text
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/delta.lst
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/duplicates.lst
```

### GeoIP / GeoSite для Xray/V2Ray

* [`geoip_noc.dat`](geoip_noc.dat) — GeoIP-файл, собираемый из выбранных списков IPv4-подсетей `itdoginfo/allow-domains` и моих дополнительных категорий.
* [`geosite_noc.dat`](geosite_noc.dat) — GeoSite-файл, собираемый из моих доменных списков.

Прямые URL:

```text
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/geoip_noc.dat
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/geosite_noc.dat
```

## Скрипты

Актуальные скрипты находятся в [`scripts/`](scripts/):

* `check_ITDdomains.py` — проверка пользовательских доменов на наличие в списках itdoginfo;
* `lst2json.py` — конвертация всех `cats/*.lst` в `json/*.json` формата sing-box;
* `generate_geoip.py` — сборка `geoip_noc.dat`;
* `generate_geosite.py` — сборка `geosite_noc.dat`.

Текущие Python-скрипты используют только стандартную библиотеку Python и не требуют установки дополнительных модулей.

## GitHub Actions

Актуальные workflow находятся в [`.github/workflows/`](.github/workflows/) и автоматически:

* обновляют `delta.lst` и `duplicates.lst`;
* конвертируют `cats/*.lst` в `json/*.json`;
* пересобирают `geoip_noc.dat`;
* пересобирают `geosite_noc.dat`.

Workflow запускаются по расписанию, а также могут быть запущены вручную через **Actions → Run workflow**.

## Структура репозитория

```text
.github/workflows/   актуальные GitHub Actions
cats/                исходные пользовательские .lst-категории
json/                автоматически сгенерированные JSON-категории
scripts/             актуальные Python-скрипты
old/                 архив старых, больше не используемых файлов
custom-rules.json    основной пользовательский список
delta.lst            правила, отсутствующие в проверяемых списках itdoginfo
duplicates.lst       найденные пересечения
geoip_noc.dat        генерируемый GeoIP-файл
geosite_noc.dat      генерируемый GeoSite-файл
owrt_tune.sh         вспомогательный скрипт настройки OpenWrt
```

> [!IMPORTANT]
> Каталог [`old/`](old/) содержит **устаревшие скрипты, списки и workflow**, оставленные только как архив. Они не относятся к текущей схеме работы репозитория. Актуальные скрипты находятся в `scripts/`, а workflow — в `.github/workflows/`.

## OpenWrt: отключение IPv6

[`owrt_tune.sh`](owrt_tune.sh) — отдельный вспомогательный скрипт для OpenWrt. Он отключает IPv6 для LAN/WAN, DHCPv6/RA и ULA, включает фильтрацию AAAA в dnsmasq, отключает `odhcpd`, задаёт sysctl-параметры и перезапускает сеть.

> [!WARNING]
> Скрипт изменяет сетевую конфигурацию OpenWrt и перезапускает сеть. Перед использованием желательно иметь резервную копию конфигурации и локальный доступ к роутеру.

Запуск напрямую:

```sh
sh <(wget -O - https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/owrt_tune.sh)
```

или с предварительным скачиванием:

```sh
wget -O /tmp/owrt_tune.sh https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/owrt_tune.sh
sh /tmp/owrt_tune.sh
rm /tmp/owrt_tune.sh
```

## Источники

Основной внешний источник списков:

* [itdoginfo/allow-domains](https://github.com/itdoginfo/allow-domains)

Мои файлы являются дополнениями и производными списками для собственной конфигурации; содержимое исходного проекта itdoginfo следует сверять с его репозиторием.
