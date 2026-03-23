<?php
// Configuration file for PHP webhook service

define('APP_NAME', 'SIEM Webhook Service');
define('APP_VERSION', '1.0.0');
define('PYTHON_SERVICE_URL', getenv('PYTHON_SERVICE_URL') ?: 'http://localhost:5000');
define('JAVA_SERVICE_URL', getenv('JAVA_SERVICE_URL') ?: 'http://localhost:8080');
define('WEBHOOK_SECRET', getenv('WEBHOOK_SECRET') ?: '');

// Error handling
error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', '/var/log/php-error.log');

// JSON responses
header('Content-Type: application/json; charset=utf-8');
?>