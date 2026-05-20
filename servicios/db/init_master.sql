CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor';
GRANT USAGE ON *.* TO 'monitor'@'%';

CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'secret';

CREATE DATABASE IF NOT EXISTS suitecrm_a;
CREATE DATABASE IF NOT EXISTS suitecrm_b;

GRANT ALL PRIVILEGES ON suitecrm_a.* TO 'suitecrm_user'@'%';
GRANT ALL PRIVILEGES ON suitecrm_b.* TO 'suitecrm_user'@'%';

FLUSH PRIVILEGES;
