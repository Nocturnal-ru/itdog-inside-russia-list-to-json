# itdog-inside-russia-list-to-json
автоконвертор списков
- inside Russia
- subnets (Meta/Discord/Twitter)

от ув. itdog в json format

https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/inside-russia.json

https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/subnets.json

с моими личными добавлениями в формате nfset

https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/custom-rules.lst

только добавки
https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/main/custom-rules.json

Скрипт настройки openwrt:
- отключение IPv6


Запуск 2 варианта:
sh <(wget -O - https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/master/owrt_tune.sh)
или
wget -O /tmp/owrt_tune.sh https://raw.githubusercontent.com/Nocturnal-ru/itdog-inside-russia-list-to-json/master/owrt_tune.sh
sh /tmp/owrt_tune.sh
rm /tmp/owrt_tune.sh
