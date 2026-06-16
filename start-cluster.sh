#!/bin/bash

set -e

nodes=(galera1 galera2 galera3)
BOOTSTRAP_NODE=""
best_seqno=-1
has_grastate=false

echo "=================================="
echo " BUSCANDO NODO BOOTSTRAP GALERA "
echo "=================================="

echo "Verificando archivos grastate.dat..."
for NODE in "${nodes[@]}"; do
    FILE="./data/$NODE/grastate.dat"

    if [ -f "$FILE" ]; then
        has_grastate=true
        SAFE=$(grep -E '^safe_to_bootstrap:' "$FILE" | awk '{print $2}')
        SEQNO=$(grep -E '^seqno:' "$FILE" | awk '{print $2}')
        SEQNO=${SEQNO:--1}

        echo "$NODE -> safe_to_bootstrap=$SAFE, seqno=$SEQNO"

        if [ "$SAFE" = "1" ] && [ "$SEQNO" -gt "$best_seqno" ]; then
            best_seqno=$SEQNO
            BOOTSTRAP_NODE=$NODE
        fi
    else
        echo "$NODE -> sin grastate.dat"
    fi
done

if [ -z "$BOOTSTRAP_NODE" ]; then
    if [ "$has_grastate" = false ]; then
        echo "No hay grastate.dat en ningún nodo. Se usará galera1 como bootstrap por defecto."
        BOOTSTRAP_NODE=galera1
    else
        echo ""
        echo "ERROR: Ningún nodo tiene safe_to_bootstrap=1."
        echo "Debes revisar manualmente el estado de los datos antes de iniciar el clúster."
        exit 1
    fi
fi

echo ""
echo "Nodo bootstrap seleccionado: $BOOTSTRAP_NODE"
echo ""

echo "Levantando $BOOTSTRAP_NODE..."
docker compose up -d $BOOTSTRAP_NODE

echo "Esperando a que $BOOTSTRAP_NODE esté listo..."
for i in {1..20}; do
    if docker exec $BOOTSTRAP_NODE mariadb -uroot -prootpass -e "SELECT 1" >/dev/null 2>&1; then
        echo "  $BOOTSTRAP_NODE responde (intento $i)."
        break
    fi
    sleep 3
done

if ! docker exec $BOOTSTRAP_NODE mariadb -uroot -prootpass -e "SELECT 1" >/dev/null 2>&1; then
    echo "ERROR: $BOOTSTRAP_NODE no respondió dentro del tiempo esperado."
    exit 1
fi

echo "Esperando un estado Primary..."
for i in {1..20}; do
    if docker exec $BOOTSTRAP_NODE mariadb -uroot -prootpass -e "SHOW STATUS LIKE 'wsrep_cluster_status'" 2>/dev/null | grep -q Primary; then
        STATUS=Primary
        echo "  $BOOTSTRAP_NODE está en estado Primary."
        break
    fi
    sleep 3
done

if [ -z "$STATUS" ]; then
    echo "ERROR: $BOOTSTRAP_NODE no alcanzó estado Primary."
    docker exec $BOOTSTRAP_NODE mariadb -uroot -prootpass -e "SHOW STATUS LIKE 'wsrep_cluster_status'; SHOW STATUS LIKE 'wsrep_local_state_comment';" || true
    exit 1
fi

echo "Levantando nodos restantes..."
for NODE in "${nodes[@]}"; do
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
EOF
chmod +x start-cluster.sh