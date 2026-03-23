FROM php:8.2-apache

WORKDIR /var/www/html

# Enable mod_rewrite
RUN a2enmod rewrite

# Copy application files
COPY api.php .
COPY config.php .
COPY health.php .

# Create log directory
RUN mkdir -p /var/log && chmod 755 /var/log

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:80/health.php || exit 1

EXPOSE 80

CMD ["apache2-foreground"]