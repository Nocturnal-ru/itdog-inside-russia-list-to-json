#!/bin/sh

# Отключаем IPv6 для LAN и WAN
uci set 'network.lan.ipv6=0'
uci set 'network.wan.ipv6=0'
uci set 'dhcp.lan.dhcpv6=disabled'

# Отключаем делегирование IPv6 для LAN
uci set network.lan.delegate="0"

# Отключаем odhcpd
/etc/init.d/odhcpd disable
/etc/init.d/odhcpd stop

# Удаляем RA и DHCPv6, чтобы IPv6-адреса не раздавались
uci -q delete dhcp.lan.dhcpv6
uci -q delete dhcp.lan.ra

# Удаляем IPv6 ULA Prefix
uci -q delete network.globals.ula_prefix

# Применяем изменения одним коммитом
uci commit network
uci commit dhcp

# Вносим правку в /etc/config/dhcp для отключения IPv6 DNS-запросов
if ! grep -q "option filter_aaaa '1'" /etc/config/dhcp; then
    echo -e "\nconfig dnsmasq\n\toption filter_aaaa '1'" >> /etc/config/dhcp
fi

# Перезапускаем службы: сначала dnsmasq, потом network
/etc/init.d/dnsmasq restart
/etc/init.d/network restart

echo "IPv6 отключен."
