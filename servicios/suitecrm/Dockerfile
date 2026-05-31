FROM php:8.2-apache

RUN apt-get update && apt-get install -y \
    libpng-dev libjpeg-dev libfreetype6-dev libzip-dev \
    libicu-dev libkrb5-dev libcurl4-openssl-dev \
    libldap2-dev libonig-dev libxml2-dev \
    unzip curl \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-configure ldap \
    && docker-php-ext-install \
        gd mysqli pdo_mysql zip intl \
        mbstring curl soap bcmath ldap opcache \
    && pecl install redis \
    && docker-php-ext-enable redis opcache \
    && a2enmod rewrite \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY config/apache-suitecrm.conf /etc/apache2/conf-available/suitecrm.conf
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf \
    && a2enconf suitecrm

COPY config/php-suitecrm.ini /usr/local/etc/php/conf.d/suitecrm.ini
COPY config/opcache.ini /usr/local/etc/php/conf.d/opcache.ini

WORKDIR /usr/src/suitecrm

RUN curl -L -o suitecrm.zip \
    https://github.com/SuiteCRM/SuiteCRM/releases/download/v7.15.1/SuiteCRM-7.15.1.zip \
    && unzip -q suitecrm.zip \
    && cp -a SuiteCRM-7.15.1/. . \
    && rm -rf SuiteCRM-7.15.1 suitecrm.zip \
    && mkdir -p cache custom upload logs \
    && chown -R www-data:www-data . \
    && chmod -R 755 . \
    && chmod -R 775 cache custom upload logs modules themes data

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]