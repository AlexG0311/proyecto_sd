#!/bin/bash
set -e

# Primera vez — copia archivos al volumen
if [ ! -f /var/www/html/index.php ]; then
    echo ">>> Copiando SuiteCRM al volumen..."
    cp -a /usr/src/suitecrm/. /var/www/html/
    echo ">>> Copia completada"
fi

# Parche credenciales si están vacías
if [ -f /var/www/html/config.php ]; then
    if grep -q "'db_user_name' => ''" /var/www/html/config.php; then
        echo ">>> Parcheando credenciales..."
        sed -i "s/'db_user_name' => ''/'db_user_name' => 'suitecrm_user'/" /var/www/html/config.php
        sed -i "s/'db_password' => ''/'db_password' => 'secret'/" /var/www/html/config.php
        sed -i "s/'db_port' => NULL/'db_port' => '3306'/" /var/www/html/config.php
    fi
fi

# Permisos
echo ">>> Aplicando permisos..."
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
chmod -R 775 /var/www/html/cache \
             /var/www/html/custom \
             /var/www/html/upload \
             /var/www/html/logs \
             /var/www/html/modules \
             /var/www/html/themes \
             /var/www/html/data
chmod 775 /var/www/html/config_override.php 2>/dev/null || true

echo ">>> Iniciando Apache..."
exec apache2-foreground