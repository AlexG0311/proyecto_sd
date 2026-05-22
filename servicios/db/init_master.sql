CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT USAGE ON *.* TO 'monitor'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'monitor'@'%';

CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'secret';
GRANT ALL PRIVILEGES ON *.* TO 'suitecrm_user'@'%';

FLUSH PRIVILEGES;