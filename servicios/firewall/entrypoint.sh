#!/bin/sh

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -F
iptables -t nat -F

iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# HTTP
iptables -t nat -A PREROUTING \
    -p tcp --dport 80 \
    -j DNAT --to-destination 192.168.1.5:80

iptables -A FORWARD \
    -p tcp -d 192.168.1.5 \
    --dport 80 \
    -j ACCEPT

# HTTPS
iptables -t nat -A PREROUTING \
    -p tcp --dport 443 \
    -j DNAT --to-destination 192.168.1.5:443

iptables -A FORWARD \
    -p tcp -d 192.168.1.5 \
    --dport 443 \
    -j ACCEPT

# NAT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth2 -j MASQUERADE

tail -f /dev/null