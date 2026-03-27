#!/bin/sh

# Отключаем IPv6 для LAN и WAN
uci set 'network.lan.ipv6=0'
uci set 'network.wan.ipv6=0'

# Отключаем делегирование IPv6 для LAN
uci set network.lan.delegate="0"

# Удаляем RA и DHCPv6
uci -q delete dhcp.lan.dhcpv6
uci -q delete dhcp.lan.ra

# Удаляем IPv6 ULA Prefix
uci -q delete network.globals.ula_prefix

# Фильтруем AAAA-записи в DNS через UCI (не через echo в файл!)
uci set dhcp.@dnsmasq[0].filter_aaaa='1'

# Сохраняем изменения
uci commit network
uci commit dhcp

# Отключаем odhcpd
/etc/init.d/odhcpd disable
/etc/init.d/odhcpd stop

# Отключаем IPv6 на уровне ядра
sysctl -w net.ipv6.conf.all.disable_ipv6=1
sysctl -w net.ipv6.conf.default.disable_ipv6=1

# Делаем постоянным через sysctl.d
grep -q 'disable_ipv6' /etc/sysctl.d/99-disable-ipv6.conf 2>/dev/null || {
    echo 'net.ipv6.conf.all.disable_ipv6=1' >> /etc/sysctl.d/99-disable-ipv6.conf
    echo 'net.ipv6.conf.default.disable_ipv6=1' >> /etc/sysctl.d/99-disable-ipv6.conf
}

# Перезапускаем службы
/etc/init.d/dnsmasq restart
/etc/init.d/network restart

echo "IPv6 отключен."
