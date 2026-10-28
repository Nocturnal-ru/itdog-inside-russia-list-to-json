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
awg-openwrt-updater.sh  обновление установленных пакетов AmneziaWG (opkg)
vps_warp_distillium.sh  нативный WireGuard WARP-интерфейс на VPS (systemd)
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

## OpenWrt: обновление AmneziaWG

[`awg-openwrt-updater.sh`](awg-openwrt-updater.sh) обновляет уже установленные пакеты [awg-openwrt](https://github.com/Slava-Shchipunov/awg-openwrt): сравнивает версии с GitHub Releases, проверяет зависимости перед установкой и по умолчанию сохраняет резервную копию сетевых настроек в `/root/awg-backups/`. Конфигурацию интерфейсов скрипт не меняет.

Обновление (с подтверждением и резервным копированием):

```sh
sh <(wget -O - https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/awg-openwrt-updater.sh)
```

Проверка без установки:

```sh
sh <(wget -O - https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/awg-openwrt-updater.sh) --check
```

Поддерживаются OpenWrt с `opkg` (`.ipk`, в частности 24.10.x); OpenWrt 25.x с `apk` пока не поддерживается. При обновлении модуля ядра рекомендуется контролируемая перезагрузка и проверка туннеля. Формат `<(…)` требует поддержки process substitution командной оболочкой, из которой запускается команда.

## VPS: WARP через WireGuard (distillium)

[`vps_warp_distillium.sh`](vps_warp_distillium.sh) — упрощённый установщик нативного WARP-интерфейса для **Debian/Ubuntu с systemd** по мотивам [distillium/warp-native](https://github.com/distillium/warp-native). Используется штатный `wg-quick@distillium.service` и конфигурация `/etc/wireguard/distillium.conf`.

**Отличия от оригинала:** нет регистрации аккаунта, `wgcf`, kill switch, watchdog, изменения DNS сервера VPS или маршрута по умолчанию. Ключи и рабочий endpoint заранее получаются через [warpscout](https://github.com/vernette/warpscout). Скрипт ставит только недостающие `wireguard-tools` / `iproute2` через apt; сохраняет параметры warpscout, удаляет `DNS` и принудительно выставляет `Table = off`. Конфиги с командами `PostUp` / `PreUp` и с AmneziaWG-полями отклоняются.

### Установка

1. На компьютере с **warpscout** создай конфиг стандартного **WireGuard** (не AmneziaWG):

   ```bash
   warpscout scan -p wg -P -exclude-node DME -conf distillium.conf -table-off -no-dns
   ```

   `-p wg` принципиален: штатный `wg-quick` не поддерживает параметры `Jc/Jmin/Jmax/S1/S2/H1-H4`, которые присутствуют у `-p awg`. Если обычный WG блокируется на выбранной сети, этот установщик сам по себе блокировку не устранит. Если IPv6 на VPS полностью отключён, убери IPv6-адрес из `Address` и IPv6-префикс из `AllowedIPs` в исходном конфиге.

2. Скопируй конфиг на VPS, затем скачай и запусти скрипт **от root**:

   ```bash
   scp distillium.conf root@<VPS_IP>:/root/distillium.conf
   ```

   На VPS:

   ```bash
   curl -fsSLo /root/vps_warp_distillium.sh https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/vps_warp_distillium.sh
   bash /root/vps_warp_distillium.sh --config /root/distillium.conf
   ```

   Если конфиг уже сохранён в `/etc/wireguard/distillium.conf`, можно запустить скрипт без `--config`. При замене существующего конфига другим файлом явно добавь `--replace`: будет создана резервная копия `distillium.conf.bak.*`, а при ошибке запуска прежний конфиг будет восстановлен. Исходный файл в `/root` после успешной установки лучше удалить или хранить с правами `0600`.

### Проверка и управление

```bash
systemctl status wg-quick@distillium
wg show distillium
ip -4 route show default
curl -4 --interface distillium --max-time 15 -fsS https://www.cloudflare.com/cdn-cgi/trace
```

Туннель должен быть активен, а `default route` VPS — остаться прежним. Для появления `latest handshake` нужен реальный трафик через туннель. Последняя команда проверяет выход через интерфейс, а не через обычный IP VPS. При ошибке смотри `journalctl -u wg-quick@distillium -n 100 --no-pager`.

Остановить / запустить / выключить автозапуск:

```bash
systemctl stop wg-quick@distillium
systemctl start wg-quick@distillium
systemctl disable wg-quick@distillium
```

Для **Xray-core, сервер** (3x-ui, outbound `freedom`) можно использовать привязку `sockopt.interface` к `distillium` и направлять на этот outbound только нужные домены:

```json
{
  "tag": "distillium",
  "protocol": "freedom",
  "settings": {
    "domainStrategy": "ForceIPv4"
  },
  "streamSettings": {
    "sockopt": {
      "interface": "distillium"
    }
  }
}
```

Это JSON outbound ядра Xray, **не** конфиг 3x-ui. Поскольку kill switch отсутствует, строгую гарантию отсутствия выхода вне туннеля такая схема не даёт; отдельно проверь поведение при остановке интерфейса. Скрипт не меняет сетевую конфигурацию Xray или firewall.

## Источники

Основной внешний источник списков:

* [itdoginfo/allow-domains](https://github.com/itdoginfo/allow-domains)

Мои файлы являются дополнениями и производными списками для собственной конфигурации; содержимое исходного проекта itdoginfo следует сверять с его репозиторием.
