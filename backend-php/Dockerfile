FROM php:8.1-apache

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        libzip-dev \
        unzip \
        curl \
    && docker-php-ext-install pdo pdo_pgsql zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Composer
COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

# Apache: enable mod_rewrite and set document root
RUN a2enmod rewrite headers

# Copy custom Apache vhost
COPY docker/apache.conf /etc/apache2/sites-available/000-default.conf

WORKDIR /var/www/html

# Install PHP dependencies first (layer cache)
COPY composer.json composer.lock* ./
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-progress

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /var/log/siem-php \
    && chown -R www-data:www-data /var/log/siem-php /var/www/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fs http://localhost/health || exit 1

CMD ["apache2-foreground"]
