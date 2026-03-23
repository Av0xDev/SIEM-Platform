<?php
/**
 * SIEM Platform - PHP Service Configuration
 *
 * Values are read from environment variables with safe defaults for local dev.
 * Never commit real secrets — use .env or a secrets manager in production.
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// Database (PostgreSQL)
// ---------------------------------------------------------------------------
define('DB_HOST',     getenv('DB_HOST')     ?: 'postgres');
define('DB_PORT',     (int)(getenv('DB_PORT') ?: 5432));
define('DB_NAME',     getenv('DB_NAME')     ?: 'siem_db');
define('DB_USER',     getenv('DB_USER')     ?: 'siem_user');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: 'siem_password');

// ---------------------------------------------------------------------------
// Downstream services
// ---------------------------------------------------------------------------
define('PYTHON_SERVICE_URL', getenv('PYTHON_SERVICE_URL') ?: 'http://python-service:5000');
define('JAVA_SERVICE_URL',   getenv('JAVA_SERVICE_URL')   ?: 'http://java-service:8080');
define('RUBY_SERVICE_URL',   getenv('RUBY_SERVICE_URL')   ?: 'http://ruby-service:3000');

// ---------------------------------------------------------------------------
// Security
// ---------------------------------------------------------------------------
/** Shared HMAC secret used to verify incoming webhook payloads */
define('WEBHOOK_SECRET',      getenv('WEBHOOK_SECRET')      ?: 'change-me-in-production');
/** Bearer token expected from trusted internal callers */
define('INTERNAL_SERVICE_KEY', getenv('INTERNAL_SERVICE_KEY') ?: 'internal-service-key');
define('JWT_SECRET',           getenv('JWT_SECRET')           ?: 'jwt-secret-change-me');
define('JWT_ALGORITHM',        getenv('JWT_ALGORITHM')        ?: 'HS256');

// ---------------------------------------------------------------------------
// Rate limiting
// ---------------------------------------------------------------------------
/** Maximum number of webhook requests per IP per window */
define('RATE_LIMIT_MAX_REQUESTS', (int)(getenv('RATE_LIMIT_MAX_REQUESTS') ?: 100));
/** Sliding-window duration in seconds */
define('RATE_LIMIT_WINDOW',       (int)(getenv('RATE_LIMIT_WINDOW')       ?: 60));

// ---------------------------------------------------------------------------
// Application
// ---------------------------------------------------------------------------
define('APP_ENV',   getenv('APP_ENV')  ?: 'production');
define('BASE_PATH', getenv('BASE_PATH') ?: '');
define('LOG_FILE',  getenv('LOG_FILE')  ?: '/var/log/siem-php/webhook.log');
define('LOG_LEVEL', getenv('LOG_LEVEL') ?: 'warning');

// ---------------------------------------------------------------------------
// CORS
// ---------------------------------------------------------------------------
define('ALLOWED_ORIGINS', getenv('ALLOWED_ORIGINS') ?: '*');

// ---------------------------------------------------------------------------
// Runtime hardening
// ---------------------------------------------------------------------------
if (APP_ENV === 'production') {
    ini_set('display_errors', '0');
    ini_set('log_errors', '1');
    error_reporting(E_ALL);
} else {
    ini_set('display_errors', '1');
    error_reporting(E_ALL);
}

// Ensure log directory exists.
$logDir = dirname(LOG_FILE);
if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
}
