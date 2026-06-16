$TTL 604800

@   IN SOA ns1.clientea.com. admin.clientea.com. (
        2026061502
        604800
        86400
        2419200
        604800 )

@       IN NS ns1.clientea.com.

@       IN A 192.168.100.122
ns1     IN A 192.168.100.122

crm     IN A 192.168.100.122
www     IN CNAME crm



