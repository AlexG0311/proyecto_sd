CREATE USER 'repl_user'@'%' IDENTIFIED BY 'repl_pass';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%';
CREATE USER 'suitecrm_user'@'%' IDENTIFIED BY 'secret';
GRANT ALL PRIVILEGES ON *.* TO 'suitecrm_user'@'%';
CREATE DATABASE suitecrm_a;
CREATE DATABASE suitecrm_b;
FLUSH PRIVILEGES;
