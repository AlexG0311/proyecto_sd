#!/bin/bash
set -e

DATADIR=/var/lib/mysql
GRASTATE=$DATADIR/grastate.dat

get_seqno() {
    if [ -f "$GRASTATE" ]; then
        grep "seqno:" "$GRASTATE" | awk '{print $2}'
    else
        echo "-1"
    fi
}

get_safe_to_bootstrap() {
    if [ -f "$GRASTATE" ]; then
        grep "safe_to_bootstrap:" "$GRASTATE" | awk '{print $2}'
    else
        echo "0"
    fi
}

SEQNO=$(get_seqno)
SAFE=$(get_safe_to_bootstrap)
NODE_NAME=${WSREP_NODE_NAME:-$(hostname)}

echo ">>> Nodo: $NODE_NAME | seqno: $SEQNO | safe_to_bootstrap: $SAFE"

if [ ! -f "$GRASTATE" ] || [ "$SAFE" = "1" ]; then
    echo ">>> Iniciando como nodo bootstrap..."

    exec gosu mysql mariadbd \
        --wsrep-new-cluster \
        --wsrep-node-name="$NODE_NAME" \
        --wsrep-node-address="$NODE_NAME"

else
    echo ">>> Uniéndose al clúster existente..."

    exec gosu mysql mariadbd \
        --wsrep-node-name="$NODE_NAME" \
        --wsrep-node-address="$NODE_NAME"
fi