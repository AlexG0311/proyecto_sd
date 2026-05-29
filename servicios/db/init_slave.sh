#!/bin/bash

until mysql -hdb_master -uroot -prootpass -e "SELECT 1" &>/dev/null; do
    echo "Esperando master..."
    sleep 3
done

MASTER_STATUS=$(mysql -hdb_master -uroot -prootpass -e "SHOW MASTER STATUS\G")
MASTER_FILE=$(echo "$MASTER_STATUS" | grep "File:" | awk '{print $2}')
MASTER_POS=$(echo "$MASTER_STATUS" | grep "Position:" | awk '{print $2}')

mysql -uroot -prootpass -e "
STOP SLAVE;
CHANGE MASTER TO
  MASTER_HOST='db_master',
  MASTER_USER='root',
  MASTER_PASSWORD='rootpass',
  MASTER_LOG_FILE='$MASTER_FILE',
  MASTER_LOG_POS=$MASTER_POS;
START SLAVE;"

echo "Replicación configurada: $MASTER_FILE @ $MASTER_POS"

mysql -uroot -prootpass -e "
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT USAGE ON *.* TO 'monitor'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'monitor'@'%';

CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'secret';
GRANT ALL PRIVILEGES ON suitecrm_a.* TO 'suitecrm_user'@'%';
GRANT ALL PRIVILEGES ON suitecrm_b.* TO 'suitecrm_user'@'%';
FLUSH PRIVILEGES;"

echo "Usuarios creados en slave"
