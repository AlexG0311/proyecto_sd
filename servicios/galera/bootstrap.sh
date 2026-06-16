#!/bin/bash
set -e

DATADIR=/var/lib/mysql
GRASTATE=$DATADIR/grastate.dat
NODE_NAME=${WSREP_NODE_NAME:-$(hostname)}
NODE_ADDRESS=${WSREP_NODE_ADDRESS:-$NODE_NAME}
PEER_LIST=${WSREP_CLUSTER_NODES:-galera1,galera2,galera3}
MYSQL_ROOT_PASSWORD=${MARIADB_ROOT_PASSWORD:-rootpass}

get_seqno() {
    if [ -f "$GRASTATE" ]; then
        grep '^seqno:' "$GRASTATE" | awk '{print $2}'
    else
        echo "-1"
    fi
}

get_safe_to_bootstrap() {
    if [ -f "$GRASTATE" ]; then
        grep '^safe_to_bootstrap:' "$GRASTATE" | awk '{print $2}'
    else
        echo "0"
    fi
}

datadir_is_empty() {
    [ -z "$(find "$DATADIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]
}

has_system_schema() {
    [ -d "$DATADIR/mysql" ]
}

cleanup_partial_datadir() {
    echo ">>> Directorio de datos parcial detectado en $DATADIR"
    echo ">>> Limpiando archivos viejos antes de inicializar..."
    find "$DATADIR" -mindepth 1 -maxdepth 1 -not -name lost+found -exec rm -rf {} +
}

cluster_alive() {
    for host in ${PEER_LIST//,/ }; do
        if [ "$host" = "$NODE_NAME" ]; then
            continue
        fi

        if mysqladmin ping -h "$host" -uroot -p"$MYSQL_ROOT_PASSWORD" --silent 2>/dev/null; then
            if mysql -h "$host" -uroot -p"$MYSQL_ROOT_PASSWORD" \
                -e "SHOW STATUS LIKE 'wsrep_cluster_status'" 2>/dev/null | grep -q Primary; then
                return 0
            fi
        fi
    done

    return 1
}

if [ ! -d "$DATADIR" ]; then
    mkdir -p "$DATADIR"
fi

if ! has_system_schema && ! datadir_is_empty; then
    cleanup_partial_datadir
fi

SEQNO=$(get_seqno)
SAFE=$(get_safe_to_bootstrap)

echo ">>> Nodo: $NODE_NAME | seqno: $SEQNO | safe_to_bootstrap: $SAFE"

if cluster_alive; then
    echo ">>> Clúster activo detectado en otro nodo. Uniéndose al clúster..."
    exec /usr/local/bin/docker-entrypoint.sh mariadbd \
        --wsrep-node-name="$NODE_NAME" \
        --wsrep-node-address="$NODE_ADDRESS"
elif [ "$SAFE" = "1" ] || [ ! -f "$GRASTATE" ]; then
    echo ">>> No hay clúster activo. Iniciando bootstrap en este nodo..."
    exec /usr/local/bin/docker-entrypoint.sh mariadbd \
        --wsrep-new-cluster \
        --wsrep-node-name="$NODE_NAME" \
        --wsrep-node-address="$NODE_ADDRESS"
else
    echo ">>> No hay clúster activo y este nodo no está marcado safe_to_bootstrap=1. Iniciando en modo join..."
    exec /usr/local/bin/docker-entrypoint.sh mariadbd \
        --wsrep-node-name="$NODE_NAME" \
        --wsrep-node-address="$NODE_ADDRESS"
fi
