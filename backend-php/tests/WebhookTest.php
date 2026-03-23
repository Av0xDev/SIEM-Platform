<?php
/**
 * SIEM Platform - PHP Webhook Service Tests
 *
 * Run with: vendor/bin/phpunit tests/ --testdox
 */

declare(strict_types=1);

namespace SIEM\Tests;

use PHPUnit\Framework\TestCase;

// Pull in helpers from api.php without executing the router.
// We define the constants the file needs before including it.
if (!defined('WEBHOOK_SECRET')) {
    define('WEBHOOK_SECRET',       'test-secret');
    define('INTERNAL_SERVICE_KEY', 'test-internal-key');
    define('JWT_SECRET',           'test-jwt-secret');
    define('JWT_ALGORITHM',        'HS256');
    define('PYTHON_SERVICE_URL',   'http://python-service:5000');
    define('JAVA_SERVICE_URL',     'http://java-service:8080');
    define('RUBY_SERVICE_URL',     'http://ruby-service:3000');
    define('DB_HOST',              'localhost');
    define('DB_PORT',              5432);
    define('DB_NAME',              'siem_db');
    define('DB_USER',              'siem_user');
    define('DB_PASSWORD',          'siem_password');
    define('RATE_LIMIT_MAX_REQUESTS', 100);
    define('RATE_LIMIT_WINDOW',    60);
    define('APP_ENV',              'testing');
    define('BASE_PATH',            '');
    define('LOG_FILE',             '/tmp/siem-test.log');
    define('LOG_LEVEL',            'debug');
    define('ALLOWED_ORIGINS',      '*');
}

// Include only the functions (not the router) by extracting them separately.
// Because api.php terminates via exit() in the router, we load helpers inline.

function validateHmacSignature(string $body, string $secret): bool
{
    $header   = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? $_SERVER['HTTP_X_SIGNATURE'] ?? '';
    if ($header === '') {
        return false;
    }
    $provided = str_starts_with($header, 'sha256=') ? substr($header, 7) : $header;
    $expected = hash_hmac('sha256', $body, $secret);
    return hash_equals($expected, strtolower($provided));
}

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

function normaliseEvent(array $payload, string $source): array
{
    $now = (new \DateTimeImmutable('now', new \DateTimeZone('UTC')))->format(\DateTimeInterface::RFC3339_EXTENDED);
    return [
        'event_id'         => $payload['event_id']  ?? $payload['id']   ?? uniqid('php_', true),
        'timestamp'        => $payload['timestamp']  ?? $payload['time'] ?? $now,
        'source'           => $payload['source']     ?? $source,
        'event_type'       => $payload['event_type'] ?? $payload['type'] ?? 'unknown',
        'severity'         => normaliseSeverity($payload['severity'] ?? $payload['level'] ?? 'medium'),
        'message'          => $payload['message']    ?? $payload['msg']  ?? '',
        'raw'              => $payload,
        'ingested_at'      => $now,
        'ingestion_source' => 'php-webhook',
    ];
}

// ---------------------------------------------------------------------------

class WebhookTest extends TestCase
{
    // -----------------------------------------------------------------------
    // HMAC Signature validation
    // -----------------------------------------------------------------------

    public function testValidSignatureIsAccepted(): void
    {
        $body   = '{"event_type":"login","severity":"high"}';
        $secret = 'test-secret';
        $sig    = 'sha256=' . hash_hmac('sha256', $body, $secret);

        $_SERVER['HTTP_X_HUB_SIGNATURE_256'] = $sig;

        $this->assertTrue(validateHmacSignature($body, $secret));
    }

    public function testInvalidSignatureIsRejected(): void
    {
        $body = '{"event_type":"login"}';

        $_SERVER['HTTP_X_HUB_SIGNATURE_256'] = 'sha256=badhash';
        unset($_SERVER['HTTP_X_SIGNATURE']);

        $this->assertFalse(validateHmacSignature($body, 'test-secret'));
    }

    public function testMissingSignatureIsRejected(): void
    {
        unset($_SERVER['HTTP_X_HUB_SIGNATURE_256'], $_SERVER['HTTP_X_SIGNATURE']);

        $this->assertFalse(validateHmacSignature('{}', 'test-secret'));
    }

    public function testBareHexSignatureIsAccepted(): void
    {
        $body   = '{"event_type":"alert"}';
        $secret = 'test-secret';
        $hex    = hash_hmac('sha256', $body, $secret);

        unset($_SERVER['HTTP_X_HUB_SIGNATURE_256']);
        $_SERVER['HTTP_X_SIGNATURE'] = $hex;

        $this->assertTrue(validateHmacSignature($body, $secret));
    }

    // -----------------------------------------------------------------------
    // Severity normalisation
    // -----------------------------------------------------------------------

    /** @dataProvider severityProvider */
    public function testSeverityNormalisation(string $input, string $expected): void
    {
        $this->assertSame($expected, normaliseSeverity($input));
    }

    public static function severityProvider(): array
    {
        return [
            ['critical', 'critical'],
            ['CRITICAL', 'critical'],
            ['crit',     'critical'],
            ['5',        'critical'],
            ['high',     'high'],
            ['error',    'high'],
            ['4',        'high'],
            ['medium',   'medium'],
            ['warning',  'medium'],
            ['warn',     'medium'],
            ['3',        'medium'],
            ['low',      'low'],
            ['info',     'low'],
            ['debug',    'low'],
            ['unknown',  'medium'],   // default
        ];
    }

    // -----------------------------------------------------------------------
    // Event normalisation
    // -----------------------------------------------------------------------

    public function testNormaliseEventWithFullPayload(): void
    {
        $payload = [
            'event_id'   => 'evt-001',
            'timestamp'  => '2024-01-01T00:00:00Z',
            'source'     => 'crowdstrike',
            'event_type' => 'malware_detected',
            'severity'   => 'critical',
            'message'    => 'Ransomware signature detected',
            'host'       => 'ws-042',
            'source_ip'  => '10.0.0.5',
            'user'       => 'jdoe',
        ];

        $event = normaliseEvent($payload, 'crowdstrike');

        $this->assertSame('evt-001',             $event['event_id']);
        $this->assertSame('2024-01-01T00:00:00Z', $event['timestamp']);
        $this->assertSame('crowdstrike',          $event['source']);
        $this->assertSame('malware_detected',     $event['event_type']);
        $this->assertSame('critical',             $event['severity']);
        $this->assertSame('Ransomware signature detected', $event['message']);
        $this->assertSame('php-webhook',          $event['ingestion_source']);
        $this->assertArrayHasKey('ingested_at',   $event);
    }

    public function testNormaliseEventAppliesDefaultsForMissingFields(): void
    {
        $event = normaliseEvent([], 'test-source');

        $this->assertStringStartsWith('php_',   $event['event_id']);
        $this->assertSame('test-source',         $event['source']);
        $this->assertSame('unknown',             $event['event_type']);
        $this->assertSame('medium',              $event['severity']);
        $this->assertSame('',                    $event['message']);
    }

    public function testNormaliseEventHandlesAlternativeFieldNames(): void
    {
        $payload = [
            'id'   => 'alt-id',
            'time' => '2024-06-01T12:00:00Z',
            'type' => 'login_failure',
            'level'=> 'high',
            'msg'  => 'Failed login attempt',
        ];

        $event = normaliseEvent($payload, 'syslog');

        $this->assertSame('alt-id',             $event['event_id']);
        $this->assertSame('2024-06-01T12:00:00Z', $event['timestamp']);
        $this->assertSame('login_failure',      $event['event_type']);
        $this->assertSame('high',               $event['severity']);
        $this->assertSame('Failed login attempt', $event['message']);
    }

    public function testNormaliseEventPreservesRawPayload(): void
    {
        $payload = ['event_type' => 'scan', 'severity' => 'low', 'custom_field' => 'value'];
        $event   = normaliseEvent($payload, 'nmap');

        $this->assertSame($payload, $event['raw']);
    }

    public function testNormaliseEventIncludesExtraFields(): void
    {
        $payload = [
            'event_type'   => 'alert',
            'severity'     => 'medium',
            'custom_field' => 'custom_value',
            'another'      => 42,
        ];

        $event = normaliseEvent($payload, 'test');

        $this->assertArrayHasKey('extra', $event);
        $this->assertArrayHasKey('custom_field', $event['extra']);
        $this->assertArrayHasKey('another', $event['extra']);
    }
}
