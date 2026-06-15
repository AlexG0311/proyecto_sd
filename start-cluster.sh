#!/bin/bash

set -e

echo "=================================="
echo " BUSCANDO NODO BOOTSTRAP GALERA "
echo "=================================="

BOOTSTRAP_NODE=""

for NODE in galera1 galera2 galera3
do
    FILE="./data/$NODE/grastate.dat"

    if [ -f "$FILE" ]; then

        SAFE=$(grep "safe_to_bootstrap" "$FILE" | awk '{print $2}')

        echo "$NODE -> safe_to_bootstrap=$SAFE"

        if [ "$SAFE" = "1" ]; then
            BOOTSTRAP_NODE=$NODE
        fi
    else
        echo "$NODE -> sin grastate.dat"
    fi
done

if [ -z "$BOOTSTRAP_NODE" ]; then
    echo ""
    echo "ERROR: Ningún nodo tiene safe_to_bootstrap=1"
    exit 1
fi

echo ""
echo "Nodo bootstrap encontrado: $BOOTSTRAP_NODE"
echo ""

echo "Levantando $BOOTSTRAP_NODE..."
docker compose up -d $BOOTSTRAP_NODE

echo "Esperando 20 segundos..."
sleep 20

echo "Levantando nodos restantes..."

for NODE in galera1 galera2 galera3
do
    if [ "$NODE" != "$BOOTSTRAP_NODE" ]; then
        docker compose up -d $NODE
    fi
done

echo ""
echo "Esperando sincronización..."
sleep 20

docker exec $BOOTSTRAP_NODE mariadb -uroot -prootpass -e "
SHOW STATUS LIKE 'wsrep_cluster_size';
SHOW STATUS LIKE 'wsrep_cluster_status';
SHOW STATUS LIKE 'wsrep_local_state_comment';
"

echo ""
echo "Clúster iniciado."