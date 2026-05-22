#!/bin/bash
set -e

# Primera vez que arranca el volumen está vacío
if [ ! -f /var/www/html/index.php ]; then
    echo ">>> Volumen vacío, copiando archivos de SuiteCRM..."
    cp -a /var/www/html_backup/. /var/www/html/
    echo ">>> Copia completada"
fi

# Permisos siempre al arrancar
echo ">>> Aplicando permisos..."
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
chmod -R 775 /var/www/html/cache \
             /var/www/html/custom \
             /var/www/html/modules \
             /var/www/html/themes \
             /var/www/html/data \
             /var/www/html/upload

echo ">>> Iniciando Apache..."
exec apache2-foreground