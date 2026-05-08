#!/bin/sh

# Habilitar forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Limpiar reglas
iptables -F
iptables -t nat -F

# Políticas por defecto
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# DNAT: redirigir HTTP (puerto 80) desde eth0 hacia reverse proxy (192.168.1.5)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.1.5:80

# SNAT: enmascarar la IP origen de salida por eth1 y eth2
iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth2 -j MASQUERADE

# Mantener vivo el contenedor
tail -f /dev/null
