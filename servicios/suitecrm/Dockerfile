FROM php:8.2-apache-bullseye

RUN apt-get update && apt-get install -y \
    libpng-dev libjpeg-dev libfreetype6-dev libzip-dev \
    libicu-dev libc-client-dev libkrb5-dev libcurl4-openssl-dev \
    libldap2-dev libonig-dev libxml2-dev \
    unzip git \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-configure imap --with-kerberos --with-imap-ssl \
    && docker-php-ext-configure ldap \
    && docker-php-ext-install gd mysqli pdo_mysql zip imap intl mbstring curl soap bcmath ldap \
    && a2enmod rewrite

RUN echo '<Directory /var/www/html>\n\
    AllowOverride All\n\
    Require all granted\n\
</Directory>' > /etc/apache2/conf-available/suitecrm.conf \
 && a2enconf suitecrm

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html_backup

RUN git clone --depth 1 --branch v7.15.1 https://github.com/salesagility/SuiteCRM.git . \
    && composer install --no-dev --optimize-autoloader \
    && mkdir -p cache custom upload \
    && chown -R www-data:www-data . \
    && chmod -R 755 . \
    && chmod -R 775 cache custom modules themes data upload

RUN echo "session.save_handler = files" > /usr/local/etc/php/conf.d/session.ini

# Copiar script de entrada
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]


EXPOSE 80
