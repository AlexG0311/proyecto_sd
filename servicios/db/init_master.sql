-- ==================== USUARIOS PARA PROXYSQL Y REPLICACIÓN ====================

-- Usuario para monitoreo de ProxySQL
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT USAGE ON *.* TO 'monitor'@'%';
GRANT REPLICATION CLIENT, PROCESS ON *.* TO 'monitor'@'%';

-- Usuario dedicado para replicación (mejor que usar root)
CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED BY 'ReplPassFuerte123!';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

-- Usuario de SuiteCRM (más seguro)
CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'secret';
GRANT ALL PRIVILEGES ON suitecrm_a.* TO 'suitecrm_user'@'%';
GRANT ALL PRIVILEGES ON suitecrm_b.* TO 'suitecrm_user'@'%';

FLUSH PRIVILEGES;

-- Mostrar estado para los slaves
SHOW MASTER STATUS\G