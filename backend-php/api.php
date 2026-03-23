<?php
/**
 * SIEM Platform - PHP Webhook Receiver Service
 *
 * Receives, validates, normalises and forwards security events from
 * external sources to the Python ingest pipeline.
 *
 * Port: 8000 (Apache inside Docker)
 */

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/config.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

$logger = new Logger('webhook');
$logger->pushHandler(new StreamHandler('php://stdout', Level::Debug));
$logger->pushHandler(new StreamHandler(LOG_FILE, Level::Warning));

// In-memory rate-limit store (per PHP-FPM worker; for production use Redis).
// Key: IP address, value: ['count' => int, 'window_start' => int]
$rateLimitStore = [];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Send a JSON response and terminate.
 */
function jsonResponse(array $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/**
 * Return the raw request body (cached so it can be read multiple times).
 */
function getRawBody(): string
{
    static $body = null;
    if ($body === null) {
        $body = (string) file_get_contents('php://input');
    }
    return $body;
}

/**
 * Validate HMAC-SHA256 signature from the X-Hub-Signature-256 header.
 *
 * Expected header format: sha256=<hex-digest>
 */
function validateHmacSignature(string $body, string $secret): bool
{
    $header = $_SERVER['HTTP_X_HUB_SIGNATURE_256']
        ?? $_SERVER['HTTP_X_SIGNATURE']
        ?? '';

    if ($header === '') {
        return false;
    }

    // Support both "sha256=..." and bare hex strings.
    $provided = str_starts_with($header, 'sha256=')
        ? substr($header, 7)
        : $header;

    $expected = hash_hmac('sha256', $body, $secret);

    return hash_equals($expected, strtolower($provided));
}

/**
 * Enforce a sliding-window rate limit per IP.
 *
 * Returns true when the request is within the allowed rate.
 */
function checkRateLimit(string $ip): bool
{
    global $rateLimitStore;

    $now    = time();
    $window = RATE_LIMIT_WINDOW;
    $max    = RATE_LIMIT_MAX_REQUESTS;

    if (!isset($rateLimitStore[$ip])) {
        $rateLimitStore[$ip] = ['count' => 0, 'window_start' => $now];
    }

    $entry = &$rateLimitStore[$ip];

    // Reset window if expired.
    if (($now - $entry['window_start']) >= $window) {
        $entry['count']        = 0;
        $entry['window_start'] = $now;
    }

    $entry['count']++;

    return $entry['count'] <= $max;
}

/**
 * Normalise a raw webhook payload into the canonical SIEM event schema.
 */
function normaliseEvent(array $payload, string $source): array
{
    $now = (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format(DateTimeInterface::RFC3339_EXTENDED);

    // Extract common fields with sensible defaults.
    $event = [
        'event_id'   => $payload['event_id']   ?? $payload['id']    ?? uniqid('php_', true),
        'timestamp'  => $payload['timestamp']   ?? $payload['time']  ?? $now,
        'source'     => $payload['source']      ?? $source,
        'event_type' => $payload['event_type']  ?? $payload['type']  ?? 'unknown',
        'severity'   => normaliseSeverity($payload['severity'] ?? $payload['level'] ?? 'medium'),
        'message'    => $payload['message']     ?? $payload['msg']   ?? '',
        'raw'        => $payload,
        'ingested_at'     => $now,
        'ingestion_source' => 'php-webhook',
    ];

    // Host / network context.
    if (isset($payload['host']) || isset($payload['hostname'])) {
        $event['host'] = $payload['host'] ?? $payload['hostname'];
    }
    if (isset($payload['source_ip']) || isset($payload['src_ip'])) {
        $event['source_ip'] = $payload['source_ip'] ?? $payload['src_ip'];
    }
    if (isset($payload['destination_ip']) || isset($payload['dst_ip'])) {
        $event['destination_ip'] = $payload['destination_ip'] ?? $payload['dst_ip'];
    }

    // User context.
    if (isset($payload['user']) || isset($payload['username'])) {
        $event['user'] = $payload['user'] ?? $payload['username'];
    }

    // Additional arbitrary fields forwarded under `extra`.
    $known = ['event_id','id','timestamp','time','source','event_type','type',
              'severity','level','message','msg','host','hostname',
              'source_ip','src_ip','destination_ip','dst_ip','user','username'];
    $extra = array_diff_key($payload, array_flip($known));
    if ($extra) {
        $event['extra'] = $extra;
    }

    return $event;
}

/**
 * Map arbitrary severity strings to the canonical set.
 */
function normaliseSeverity(string $sev): string
{
    $map = [
        'critical' => 'critical', 'crit'    => 'critical', '5' => 'critical',
        'high'     => 'high',     'error'   => 'high',     '4' => 'high',
        'medium'   => 'medium',   'warning' => 'medium',   'warn' => 'medium', '3' => 'medium',
        'low'      => 'low',      'info'    => 'low',      'debug' => 'low',
        '2'        => 'low',      '1'       => 'low',
    ];

    return $map[strtolower($sev)] ?? 'medium';
}

/**
 * Forward a normalised event to the Python ingestion service.
 *
 * Returns [bool $success, string $responseBody].
 */
function forwardToPython(array $event, Logger $logger): array
{
    $client = new Client([
        'base_uri' => PYTHON_SERVICE_URL,
        'timeout'  => 5.0,
        'headers'  => [
            'Content-Type'  => 'application/json',
            'X-Service-Key' => INTERNAL_SERVICE_KEY,
            'X-Source'      => 'php-webhook',
        ],
    ]);

    try {
        $response = $client->post('/api/logs/ingest', [
            'json' => $event,
        ]);

        $body = (string) $response->getBody();
        $logger->info('Forwarded event to Python service', [
            'event_id' => $event['event_id'],
            'status'   => $response->getStatusCode(),
        ]);

        return [true, $body];
    } catch (RequestException $e) {
        $logger->error('Failed to forward event to Python service', [
            'event_id' => $event['event_id'],
            'error'    => $e->getMessage(),
        ]);

        return [false, $e->getMessage()];
    }
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$uri    = strtok($_SERVER['REQUEST_URI'] ?? '/', '?');
$ip     = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';

// Strip a path prefix that Apache may inject (e.g. /api).
$uri = '/' . ltrim(str_replace(BASE_PATH, '', $uri), '/');

$logger->debug('Incoming request', ['method' => $method, 'uri' => $uri, 'ip' => $ip]);

// ---------------------------------------------------------------------------
// GET /health
// ---------------------------------------------------------------------------
if ($method === 'GET' && $uri === '/health') {
    $dbStatus = 'ok';
    try {
        $pdo = new PDO(
            'pgsql:host=' . DB_HOST . ';port=' . DB_PORT . ';dbname=' . DB_NAME,
            DB_USER,
            DB_PASSWORD,
            [PDO::ATTR_TIMEOUT => 2]
        );
        $pdo->query('SELECT 1');
    } catch (PDOException) {
        $dbStatus = 'unavailable';
    }

    jsonResponse([
        'status'    => 'healthy',
        'service'   => 'php-webhook',
        'version'   => '1.0.0',
        'timestamp' => (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format(DateTimeInterface::RFC3339),
        'checks'    => [
            'database' => $dbStatus,
            'php'      => PHP_VERSION,
        ],
    ]);
}

// ---------------------------------------------------------------------------
// GET /webhook/status
// ---------------------------------------------------------------------------
if ($method === 'GET' && $uri === '/webhook/status') {
    jsonResponse([
        'status'        => 'operational',
        'service'       => 'php-webhook-receiver',
        'uptime'        => time() - (int) ($_SERVER['REQUEST_TIME'] ?? time()),
        'rate_limit'    => [
            'max_requests' => RATE_LIMIT_MAX_REQUESTS,
            'window_sec'   => RATE_LIMIT_WINDOW,
        ],
        'python_target' => PYTHON_SERVICE_URL . '/api/logs/ingest',
        'timestamp'     => (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format(DateTimeInterface::RFC3339),
    ]);
}

// ---------------------------------------------------------------------------
// POST routes — shared pre-flight checks
// ---------------------------------------------------------------------------
if ($method === 'POST') {
    // Rate limiting
    if (!checkRateLimit($ip)) {
        $logger->warning('Rate limit exceeded', ['ip' => $ip]);
        header('Retry-After: ' . RATE_LIMIT_WINDOW);
        jsonResponse([
            'error'     => 'rate_limit_exceeded',
            'message'   => 'Too many requests. Please retry later.',
            'retry_after' => RATE_LIMIT_WINDOW,
        ], 429);
    }

    $rawBody = getRawBody();

    if ($rawBody === '') {
        jsonResponse(['error' => 'empty_body', 'message' => 'Request body must not be empty.'], 400);
    }

    $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
    if (!str_contains($contentType, 'application/json')) {
        jsonResponse(['error' => 'invalid_content_type', 'message' => 'Content-Type must be application/json.'], 415);
    }

    $payload = json_decode($rawBody, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        jsonResponse([
            'error'   => 'invalid_json',
            'message' => 'Could not decode JSON body: ' . json_last_error_msg(),
        ], 400);
    }

    // ---------------------------------------------------------------------------
    // POST /webhook/validate  — signature check only, no forwarding
    // ---------------------------------------------------------------------------
    if ($uri === '/webhook/validate') {
        $valid = validateHmacSignature($rawBody, WEBHOOK_SECRET);

        jsonResponse([
            'valid'     => $valid,
            'message'   => $valid ? 'Signature is valid.' : 'Signature is invalid or missing.',
            'timestamp' => (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format(DateTimeInterface::RFC3339),
        ], $valid ? 200 : 401);
    }

    // ---------------------------------------------------------------------------
    // POST /webhook/receive  — authenticate, normalise and forward
    // ---------------------------------------------------------------------------
    if ($uri === '/webhook/receive') {
        // Authenticate
        if (!validateHmacSignature($rawBody, WEBHOOK_SECRET)) {
            $logger->warning('Invalid HMAC signature', ['ip' => $ip]);
            jsonResponse([
                'error'   => 'unauthorized',
                'message' => 'Invalid or missing HMAC signature.',
            ], 401);
        }

        // Source header (optional)
        $source = $_SERVER['HTTP_X_WEBHOOK_SOURCE'] ?? 'unknown';

        // Support a batch of events (array) or a single event (object).
        $events   = isset($payload[0]) ? $payload : [$payload];
        $results  = [];
        $failures = 0;

        foreach ($events as $index => $rawEvent) {
            if (!is_array($rawEvent)) {
                $results[] = ['index' => $index, 'status' => 'error', 'message' => 'Event must be a JSON object.'];
                $failures++;
                continue;
            }

            $normalised = normaliseEvent($rawEvent, $source);
            [$ok, $detail] = forwardToPython($normalised, $logger);

            $results[] = [
                'index'    => $index,
                'event_id' => $normalised['event_id'],
                'status'   => $ok ? 'forwarded' : 'failed',
                'message'  => $ok ? 'Event forwarded successfully.' : $detail,
            ];

            if (!$ok) {
                $failures++;
            }
        }

        $totalCount = count($results);
        $httpStatus = match (true) {
            $failures === 0            => 200,
            $failures < $totalCount    => 207,  // Multi-Status: partial success
            default                    => 502,  // All failed
        };

        jsonResponse([
            'received'  => $totalCount,
            'forwarded' => $totalCount - $failures,
            'failed'    => $failures,
            'results'   => $results,
            'timestamp' => (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format(DateTimeInterface::RFC3339),
        ], $httpStatus);
    }
}

// ---------------------------------------------------------------------------
// Fallback — 404
// ---------------------------------------------------------------------------
$logger->info('Route not found', ['method' => $method, 'uri' => $uri]);
jsonResponse([
    'error'   => 'not_found',
    'message' => "No route matches $method $uri",
    'available_routes' => [
        'POST /webhook/receive',
        'POST /webhook/validate',
        'GET  /webhook/status',
        'GET  /health',
    ],
], 404);
